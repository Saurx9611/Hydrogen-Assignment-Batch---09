"""
src/reactor_2d.py - Tier 2: 2D Axisymmetric Spatial Reduced-Order Model.
Solves convective-dispersive-reactive transport on a boundary-conforming (r, z) grid
in the diverging conical reduction zone, capturing wall channeling and wall heat loss.
"""

from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np

from src.config import (
    ReactorGeometry,
    FeedstockProperties,
    OperatingConditions,
    KineticConstants,
    R_UNIVERSAL,
    ATM_TO_PA,
)
from src.thermo import (
    gas_viscosity_pa_s,
    gas_thermal_conductivity_w_m_k,
    binary_diffusivity_m2_s,
    cp_molar,
    heat_of_reaction,
)
from src.reactions import ReactionModel
from src.reactor_1d import Reactor1D, SimulationResults1D


@dataclass
class SimulationResults2D:
    """Stores 2D spatial coordinate fields and solution contour matrices."""
    z_1d: np.ndarray          # 1D axial coordinates (m) (Nz,)
    r_max_1d: np.ndarray      # Radius R(z) at each axial station (m) (Nz,)
    r_grid: np.ndarray        # 2D physical radial coordinates r(eta, z) (Nr, Nz)
    z_grid: np.ndarray        # 2D physical axial coordinates z (Nr, Nz)
    t_gas_2d: np.ndarray      # 2D gas temperature field T_g(r, z) in K (Nr, Nz)
    t_solid_2d: np.ndarray    # 2D solid temperature field T_s(r, z) in K (Nr, Nz)
    y_co_2d: np.ndarray       # 2D CO dry mole fraction (%) (Nr, Nz)
    y_h2_2d: np.ndarray       # 2D H2 dry mole fraction (%) (Nr, Nz)
    y_co2_2d: np.ndarray      # 2D CO2 dry mole fraction (%) (Nr, Nz)
    y_ch4_2d: np.ndarray      # 2D CH4 dry mole fraction (%) (Nr, Nz)
    y_h2o_2d: np.ndarray      # 2D H2O wet mole fraction (%) (Nr, Nz)
    u_z_2d: np.ndarray        # 2D axial velocity field u_z(r, z) in m/s (Nr, Nz)


def solve_tridiagonal(a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray) -> np.ndarray:
    """Thomas algorithm for solving tridiagonal system Ax = d."""
    n = len(d)
    cp = np.zeros(n)
    dp = np.zeros(n)
    cp[0] = c[0] / b[0]
    dp[0] = d[0] / b[0]
    for i in range(1, n):
        denom = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / denom if i < n - 1 else 0.0
        dp[i] = (d[i] - a[i] * dp[i - 1]) / denom
    x = np.zeros(n)
    x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


class Reactor2D:
    """2D Axisymmetric spatial solver for the diverging conical gasifier hearth."""

    def __init__(
        self,
        geometry: ReactorGeometry = None,
        feedstock: FeedstockProperties = None,
        operating: OperatingConditions = None,
        kinetics: KineticConstants = None,
        n_r: int = 41,
        n_z: int = 101,
    ):
        self.geo = geometry or ReactorGeometry()
        self.feed = feedstock or FeedstockProperties()
        self.op = operating or OperatingConditions()
        self.kinetics = kinetics or KineticConstants()
        self.n_r = n_r
        self.n_z = n_z
        self.rxn = ReactionModel(self.kinetics)

    def solve(
        self,
        res_1d: SimulationResults1D = None,
        length_m: float = None,
    ) -> SimulationResults2D:
        """
        Execute 2D spatial solve across diverging cone.
        Coupled with Tier 1 1D baseline solution for axial mass integration.
        """
        if res_1d is None:
            r1d = Reactor1D(self.geo, self.feed, self.op, self.kinetics)
            res_1d = r1d.solve(length_m=length_m, num_points=self.n_z)

        l_gasif = length_m if length_m is not None else self.geo.l_gasif_baseline_m

        # Coordinate discretization
        z_arr = np.linspace(0.0, l_gasif, self.n_z)
        eta_arr = np.linspace(0.0, 1.0, self.n_r)  # eta = r / R(z)

        # Build 2D meshgrid in mapped domain (eta, z) and physical domain (r, z)
        # R(z) profile
        r_max_arr = np.array([self.geo.radius_at(z) for z in z_arr])

        r_grid = np.zeros((self.n_r, self.n_z))
        z_grid = np.zeros((self.n_r, self.n_z))

        for j in range(self.n_z):
            z_grid[:, j] = z_arr[j]
            r_grid[:, j] = eta_arr * r_max_arr[j]

        # Allocate 2D fields
        t_g_2d = np.zeros((self.n_r, self.n_z))
        t_s_2d = np.zeros((self.n_r, self.n_z))
        y_co_2d = np.zeros((self.n_r, self.n_z))
        y_h2_2d = np.zeros((self.n_r, self.n_z))
        y_co2_2d = np.zeros((self.n_r, self.n_z))
        y_ch4_2d = np.zeros((self.n_r, self.n_z))
        y_h2o_2d = np.zeros((self.n_r, self.n_z))
        u_z_2d = np.zeros((self.n_r, self.n_z))

        # Initialize inlet station j = 0 (z = 0, throat plane)
        t_core_0 = res_1d.t_gas_k[0]
        t_wall_0 = t_core_0 - 150.0  # Refractory throat wall slightly cooler

        for i in range(self.n_r):
            eta = eta_arr[i]
            # Parabolic core profile at inlet: T(eta) = T_core - (T_core - T_wall)*eta^2
            t_g_2d[i, 0] = t_core_0 - (t_core_0 - t_wall_0) * (eta ** 2)
            t_s_2d[i, 0] = res_1d.t_solid_k[0] - 50.0 * (eta ** 2)
            y_co_2d[i, 0] = res_1d.y_dry["CO"][0] * (1.0 - 0.05 * (eta ** 2))
            y_h2_2d[i, 0] = res_1d.y_dry["H2"][0] * (1.0 - 0.05 * (eta ** 2))
            y_co2_2d[i, 0] = res_1d.y_dry["CO2"][0] * (1.0 + 0.08 * (eta ** 2))
            y_ch4_2d[i, 0] = res_1d.y_dry["CH4"][0]
            # Wet H2O fraction
            f_h2o_0 = res_1d.f_h2o[0]
            f_tot_0 = f_h2o_0 + (
                res_1d.f_co[0] + res_1d.f_h2[0] + res_1d.f_co2[0] + res_1d.f_ch4[0] + res_1d.f_n2[0]
            )
            y_h2o_2d[i, 0] = (f_h2o_0 / f_tot_0) * 100.0 * (1.0 + 0.05 * (eta ** 2))

        # Step along axial direction j = 0 -> n_z - 1
        d_eta = eta_arr[1] - eta_arr[0]
        d_p_nom = self.op.chip_size_m

        for j in range(self.n_z):
            zj = z_arr[j]
            rj_max = r_max_arr[j]
            area_j = self.geo.area_at(zj)

            # 1. Radial porosity and axial velocity profile (channeling effect)
            eps_bulk = self.op.bed_void_fraction
            dist_from_wall = (1.0 - eta_arr) * rj_max
            eps_r = eps_bulk * (1.0 + 0.5 * np.exp(-2.0 * np.maximum(dist_from_wall, 0.0) / d_p_nom))
            eps_r = np.clip(eps_r, 0.35, 0.75)

            # Velocity profile based on Ergun permeability: u_z ~ eps^3 / (1 - eps)
            perm_r = (eps_r ** 3) / (1.0 - eps_r)
            q_gas_mean = (
                (res_1d.f_co[j] + res_1d.f_h2[j] + res_1d.f_co2[j] + res_1d.f_h2o[j] + res_1d.f_ch4[j] + res_1d.f_n2[j])
                * R_UNIVERSAL * res_1d.t_gas_k[j] / self.op.pressure_pa
            )
            u_mean = q_gas_mean / (area_j * eps_bulk)
            try:
                integral_perm = 2.0 * float(np.trapezoid(perm_r * eta_arr, eta_arr))
            except AttributeError:
                integral_perm = 2.0 * float(np.trapz(perm_r * eta_arr, eta_arr))
            u_z_profile = u_mean * (perm_r / max(integral_perm, 1.0e-5))
            u_z_2d[:, j] = u_z_profile

            if j == 0:
                continue

            dz = z_arr[j] - z_arr[j - 1]
            t_g_prev = t_g_2d[:, j - 1]
            t_s_prev = t_s_2d[:, j - 1]

            # Thermal and species dispersion coefficients
            pe_r = 8.5
            k_eff_r = gas_thermal_conductivity_w_m_k(np.mean(t_g_prev)) * eps_bulk + (
                1.2 * 1000.0 * u_z_profile * d_p_nom / pe_r
            )

            # 2. Advance radial temperature profile using implicit TDMA (Thomas Algorithm)
            a_mat = np.zeros(self.n_r)
            b_mat = np.ones(self.n_r)
            c_mat = np.zeros(self.n_r)
            d_vec = np.zeros(self.n_r)

            # Centerline symmetry condition: dT/d_eta = 0  ->  T_0 - T_1 = 0
            b_mat[0] = 1.0
            c_mat[0] = -1.0
            d_vec[0] = 0.0

            # Endothermic reaction cooling tracking 1D axial rate
            rxn_cooling = (res_1d.t_gas_k[j] - res_1d.t_gas_k[j - 1])

            for i in range(1, self.n_r - 1):
                eta = eta_arr[i]
                u_loc = max(u_z_profile[i], 0.05)
                rho_cp_loc = max((self.op.pressure_pa / (R_UNIVERSAL * t_g_prev[i])) * 30.0, 1.0)
                alpha_rad = k_eff_r[i] / rho_cp_loc

                kappa = (alpha_rad * dz) / (u_loc * (rj_max ** 2) * (d_eta ** 2))

                a_mat[i] = -kappa * (1.0 - 1.0 / (2.0 * i))
                b_mat[i] = 1.0 + 2.0 * kappa
                c_mat[i] = -kappa * (1.0 + 1.0 / (2.0 * i))
                d_vec[i] = t_g_prev[i] + rxn_cooling

            # Wall Robin boundary condition: -k_eff * dT/dr = U_wall * (T_wall - T_amb)
            k_wall = k_eff_r[-1]
            geom_coeff = k_wall / (rj_max * d_eta)
            u_wall = self.op.u_wall_w_m2_k
            gamma = u_wall / max(geom_coeff, 1.0e-5)

            a_mat[-1] = -1.0
            b_mat[-1] = 1.0 + gamma
            c_mat[-1] = 0.0
            d_vec[-1] = gamma * self.op.t_ambient_k

            t_g_next = solve_tridiagonal(a_mat, b_mat, c_mat, d_vec)

            # Match 1D core temperature along centerline
            center_offset = res_1d.t_gas_k[j] - t_g_next[0]
            t_g_next = t_g_next + center_offset

            t_s_next = t_s_prev + (res_1d.t_solid_k[j] - res_1d.t_solid_k[j - 1])
            t_s_next = t_s_next + 0.15 * (t_g_next - t_s_next)

            t_g_2d[:, j] = np.clip(t_g_next, 300.0, 2000.0)
            t_s_2d[:, j] = np.clip(t_s_next, 300.0, 2000.0)

            # 3. Advance species fields:
            rel_t_drop = (t_g_2d[:, j] - t_g_2d[0, j]) / max(t_g_2d[0, j], 1.0)  # negative near wall

            y_co_2d[:, j] = np.maximum(res_1d.y_dry["CO"][j] * (1.0 + 0.15 * rel_t_drop), 0.0)
            y_h2_2d[:, j] = np.maximum(res_1d.y_dry["H2"][j] * (1.0 + 0.12 * rel_t_drop), 0.0)
            y_co2_2d[:, j] = np.maximum(res_1d.y_dry["CO2"][j] * (1.0 - 0.25 * rel_t_drop), 0.0)
            y_ch4_2d[:, j] = res_1d.y_dry["CH4"][j] * np.ones(self.n_r)

            # Wet H2O profile
            f_dry_j = res_1d.gas_flow_m3_h[j] / (3.6 * 22.414)
            h2o_1d_pct = (res_1d.f_h2o[j] / (res_1d.f_h2o[j] + f_dry_j)) * 100.0
            y_h2o_2d[:, j] = np.maximum(h2o_1d_pct * (1.0 - 0.20 * rel_t_drop), 0.0)

        return SimulationResults2D(
            z_1d=z_arr,
            r_max_1d=r_max_arr,
            r_grid=r_grid,
            z_grid=z_grid,
            t_gas_2d=t_g_2d,
            t_solid_2d=t_s_2d,
            y_co_2d=y_co_2d,
            y_h2_2d=y_h2_2d,
            y_co2_2d=y_co2_2d,
            y_ch4_2d=y_ch4_2d,
            y_h2o_2d=y_h2o_2d,
            u_z_2d=u_z_2d,
        )

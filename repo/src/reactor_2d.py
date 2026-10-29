"""
src/reactor_2d.py - Tier 2: 2D axisymmetric reduced-order model of the diverging hearth.

Formulation (method of lines, finite volumes in the radial direction)
--------------------------------------------------------------------
The conical hearth r in [0, R(z)] is mapped onto eta = r / R(z) in [0, 1] and split into
N annular cells of equal width d_eta. Each cell is a conical stream-tube that follows
the wall divergence. Inside every cell the SAME physics as the 1D model is solved
(gas species, char, gas and solid temperatures, particle shrinkage; four reactions),
using Reactor1D.local_derivatives with the cell's own cross-section. Cells exchange
species and heat by radial dispersion:

  dF_i,k/dz  +=  [ 2 pi r D_r dC_i/dr ]_{k-1/2}^{k+1/2}
  (sum F Cp)_k dT_g,k/dz  +=  [ 2 pi r k_r dT_g/dr ]_{k-1/2}^{k+1/2}

  D_r = eps D_m + u_s d_p / Pe_m            (Pe_m = 10, packed-bed radial mixing)
  k_r = eps k_g + 4 sigma e/(2-e) d_p T^3 + rho_g c_p u_s d_p / Pe_h   (Pe_h = 8)

Boundary conditions: symmetry at eta = 0 (no flux); at eta = 1 the outer cell loses
heat to ambient with the calibrated wall coefficient U (same as the 1D model) and
there is no mass flux through the wall. The inlet (z = 0) is radially uniform and
equal to the 1D inlet state.

The resulting stiff ODE system (N x 10 states) is integrated with SciPy Radau using
the block-tridiagonal Jacobian sparsity. In the limit D_r, k_r -> infinity the model
reduces to the 1D model.

Not represented: radial velocity profiles / wall channelling, the air-nozzle jets,
and full Navier-Stokes flow. This is NOT CFD.
"""

from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import lil_matrix

from src.config import (
    ReactorGeometry,
    FeedstockProperties,
    OperatingConditions,
    KineticConstants,
    R_UNIVERSAL,
)
from src.thermo import gas_thermal_conductivity_w_m_k, binary_diffusivity_m2_s, cp_molar
from src.reactor_1d import Reactor1D
from src.flaming_pyrolysis import compute_throat_inlet_state

SIGMA = 5.670374e-8
PE_MASS = 10.0
PE_HEAT = 8.0
EMISSIVITY = 0.85
NV = 10  # states per cell: CO, H2, CO2, H2O, CH4, N2, C(s), Tg, Ts, dp
GAS = slice(0, 6)
SPECIES = ("CO", "H2", "CO2", "H2O", "CH4", "N2")


@dataclass
class SimulationResults2D:
    z_1d: np.ndarray          # axial stations (m), (Nz,)
    r_max_1d: np.ndarray      # R(z) (m), (Nz,)
    eta_nodes: np.ndarray     # eta of plotted nodes (axis, cell centres, wall), (Nr,)
    r_grid: np.ndarray        # physical r at nodes (m), (Nr, Nz)
    z_grid: np.ndarray        # z at nodes (m), (Nr, Nz)
    t_gas_2d: np.ndarray      # gas temperature (K)
    t_solid_2d: np.ndarray    # char temperature (K)
    y_co_2d: np.ndarray       # dry mol %
    y_h2_2d: np.ndarray
    y_co2_2d: np.ndarray
    y_ch4_2d: np.ndarray
    y_h2o_2d: np.ndarray      # wet mol %
    x_c_2d: np.ndarray        # char conversion (-)
    mixed_dry_exit: dict      # flow-weighted (mixing-cup) dry composition at the exit (%)
    mixed_t_exit_k: float     # flow-weighted gas temperature at the exit
    wall_loss_w: float        # total wall heat loss (W)
    n_cells: int


class Reactor2D:
    def __init__(self, geometry=None, feedstock=None, operating=None, kinetics=None, n_cells: int = 12, n_z: int = 111):
        self.geo = geometry or ReactorGeometry()
        self.feed = feedstock or FeedstockProperties()
        self.op = operating or OperatingConditions()
        self.kin = kinetics or KineticConstants()
        self.n = n_cells
        self.n_z = n_z
        self.r1d = Reactor1D(self.geo, self.feed, self.op, self.kin)
        edges = np.linspace(0.0, 1.0, n_cells + 1)
        self.eta_edges = edges
        self.eta_c = 0.5 * (edges[:-1] + edges[1:])
        self.w = edges[1:] ** 2 - edges[:-1] ** 2          # area fraction of each annulus
        self.d_eta = edges[1] - edges[0]

    # ------------------------------------------------------------------
    def _rhs(self, z, y):
        n = self.n
        Y = y.reshape(n, NV)
        R = self.geo.radius_at(z)
        A = self.geo.area_at(z)
        P = self.op.pressure_pa
        eps = self.op.bed_void_fraction
        dydz = np.zeros_like(Y)

        conc = np.zeros((n, 6))
        tg = np.maximum(Y[:, 7], 300.0)
        u_sup = np.zeros(n)
        cp_flow = np.zeros(n)
        for k in range(n):
            area_k = A * self.w[k]
            perim = 2.0 * np.pi * R if k == n - 1 else 0.0
            d, cpf = self.r1d.local_derivatives(z, Y[k], area_k, perim)
            dydz[k] = d
            cp_flow[k] = cpf
            f = np.maximum(Y[k, GAS], 0.0)
            ft = max(f.sum(), 1e-12)
            conc[k] = f / ft * P / (R_UNIVERSAL * tg[k])
            u_sup[k] = ft * R_UNIVERSAL * tg[k] / P / area_k

        # radial dispersion across interior interfaces k+1/2, k = 0..n-2
        dr = self.d_eta * R
        for k in range(n - 1):
            r_face = self.eta_edges[k + 1] * R
            t_f = 0.5 * (tg[k] + tg[k + 1])
            u_f = 0.5 * (u_sup[k] + u_sup[k + 1])
            dp = max(0.5 * (Y[k, 9] + Y[k + 1, 9]), 1e-4)
            d_m = binary_diffusivity_m2_s("CO", t_f, P)
            d_r = eps * d_m + u_f * dp / PE_MASS
            rho_cp = P / (R_UNIVERSAL * t_f) * cp_molar("N2", t_f)
            k_r = (eps * gas_thermal_conductivity_w_m_k(t_f)
                   + 4.0 * SIGMA * EMISSIVITY / (2.0 - EMISSIVITY) * dp * t_f ** 3
                   + rho_cp * u_f * dp / PE_HEAT)
            lat = 2.0 * np.pi * r_face
            j_species = lat * d_r * (conc[k + 1] - conc[k]) / dr      # mol/(s m) from k+1 to k
            q_heat = lat * k_r * (tg[k + 1] - tg[k]) / dr             # W/m from k+1 to k
            dydz[k, GAS] += j_species
            dydz[k + 1, GAS] -= j_species
            dydz[k, 7] += q_heat / cp_flow[k]
            dydz[k + 1, 7] -= q_heat / cp_flow[k + 1]
        return dydz.ravel()

    def _sparsity(self):
        m = self.n * NV
        S = lil_matrix((m, m), dtype=int)
        for k in range(self.n):
            for j in (k - 1, k, k + 1):
                if 0 <= j < self.n:
                    S[k * NV:(k + 1) * NV, j * NV:(j + 1) * NV] = 1
        return S.tocsr()

    # ------------------------------------------------------------------
    def solve(self, length_m: float = None) -> SimulationResults2D:
        L = length_m if length_m is not None else self.geo.l_gasif_baseline_m
        inlet = compute_throat_inlet_state(self.feed, self.op)
        base = np.array([inlet["F_CO_0"], inlet["F_H2_0"], inlet["F_CO2_0"], inlet["F_H2O_0"],
                         inlet["F_CH4_0"], inlet["F_N2_0"], inlet["F_C_solid_0"],
                         inlet["T_g0"], inlet["T_s0"], inlet["d_p_0"]])
        y0 = np.zeros((self.n, NV))
        for k in range(self.n):
            y0[k] = base
            y0[k, :7] = base[:7] * self.w[k]
        z_eval = np.linspace(0.0, L, self.n_z)
        sol = solve_ivp(self._rhs, (0.0, L), y0.ravel(), method="Radau", t_eval=z_eval,
                        rtol=1e-5, atol=1e-9, jac_sparsity=self._sparsity())
        if not sol.success:
            raise RuntimeError(f"2D solver failed: {sol.message}")

        Ys = sol.y.reshape(self.n, NV, -1)          # (cell, var, z)
        F = np.maximum(Ys[:, :6, :], 0.0)
        dry = F[:, [0, 1, 2, 4, 5], :].sum(axis=1)  # CO, H2, CO2, CH4, N2
        wet = F.sum(axis=1)

        def field(cell_vals):
            # nodes: axis (copy of first cell), cell centres, wall (copy of last cell)
            return np.vstack([cell_vals[:1], cell_vals, cell_vals[-1:]])

        y_dry = {sp: field(100.0 * F[:, i, :] / dry) for sp, i in (("CO", 0), ("H2", 1), ("CO2", 2), ("CH4", 4))}
        y_h2o = field(100.0 * F[:, 3, :] / wet)
        x_c = field(np.clip(1.0 - Ys[:, 6, :] / (base[6] * self.w[:, None]), 0.0, 1.0))
        tg = field(Ys[:, 7, :])
        ts = field(Ys[:, 8, :])

        eta_nodes = np.concatenate([[0.0], self.eta_c, [1.0]])
        r_max = np.array([self.geo.radius_at(z) for z in sol.t])
        r_grid = eta_nodes[:, None] * r_max[None, :]
        z_grid = np.broadcast_to(sol.t[None, :], r_grid.shape).copy()

        F_exit = F[:, :, -1].sum(axis=0)
        dry_exit = F_exit[[0, 1, 2, 4, 5]].sum()
        mixed = {sp: 100.0 * F_exit[i] / dry_exit for sp, i in (("CO", 0), ("H2", 1), ("CO2", 2), ("CH4", 4), ("N2", 5))}
        wts = F[:, :, -1].sum(axis=1)
        t_mix = float(np.sum(wts * Ys[:, 7, -1]) / wts.sum())

        from scipy.integrate import trapezoid
        perim = 2.0 * np.pi * r_max
        q_wall = float(trapezoid(self.op.u_wall_w_m2_k * perim * (Ys[-1, 7, :] - self.op.t_ambient_k), sol.t))

        return SimulationResults2D(
            z_1d=sol.t, r_max_1d=r_max, eta_nodes=eta_nodes, r_grid=r_grid, z_grid=z_grid,
            t_gas_2d=tg, t_solid_2d=ts, y_co_2d=y_dry["CO"], y_h2_2d=y_dry["H2"],
            y_co2_2d=y_dry["CO2"], y_ch4_2d=y_dry["CH4"], y_h2o_2d=y_h2o, x_c_2d=x_c,
            mixed_dry_exit=mixed, mixed_t_exit_k=t_mix, wall_loss_w=q_wall, n_cells=self.n,
        )

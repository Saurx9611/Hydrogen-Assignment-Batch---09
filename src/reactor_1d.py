"""
src/reactor_1d.py - Tier 1: 1D Mechanistic Fixed-Bed Downdraft Gasifier Model.
Solves the coupled ODE system for gas species, solid char, particle shrinkage,
and dual gas-solid temperature profiles in a diverging conical hearth.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from scipy.integrate import solve_ivp

from src.config import (
    FeedstockProperties,
    ReactorGeometry,
    OperatingConditions,
    KineticConstants,
    R_UNIVERSAL,
    ATM_TO_PA,
    M_C,
)
from src.feedstock import (
    BiomassAnalysis,
    calculate_syngas_lhv_mj_nm3,
    calculate_conversion_efficiency,
)
from src.thermo import cp_molar, heat_of_reaction
from src.reactions import ReactionModel
from src.flaming_pyrolysis import compute_throat_inlet_state


@dataclass
class SimulationResults1D:
    """Stores full 1D axial solution profiles."""
    z_m: np.ndarray
    f_co: np.ndarray
    f_h2: np.ndarray
    f_co2: np.ndarray
    f_h2o: np.ndarray
    f_ch4: np.ndarray
    f_n2: np.ndarray
    f_c_solid: np.ndarray
    t_gas_k: np.ndarray
    t_solid_k: np.ndarray
    d_p_m: np.ndarray
    y_dry: Dict[str, np.ndarray]
    carbon_conversion: np.ndarray
    cold_gas_efficiency_percent: np.ndarray
    gas_flow_m3_h: np.ndarray


class Reactor1D:
    """1D Mechanistic downdraft gasifier simulation solver."""

    def __init__(
        self,
        geometry: ReactorGeometry = None,
        feedstock: FeedstockProperties = None,
        operating: OperatingConditions = None,
        kinetics: KineticConstants = None,
    ):
        self.geo = geometry or ReactorGeometry()
        self.feed = feedstock or FeedstockProperties()
        self.op = operating or OperatingConditions()
        self.rxn = ReactionModel(kinetics or KineticConstants())
        self.biomass = BiomassAnalysis(self.feed, self.op.moisture_content_db)

    def _ode_derivatives(self, z: float, y_vec: np.ndarray) -> np.ndarray:
        """
        Right-hand side derivatives dY/dz for solve_ivp:
        Y = [F_CO, F_H2, F_CO2, F_H2O, F_CH4, F_N2, F_C_solid, T_g, T_s, d_p]
        """
        # Unpack state vector and enforce non-negativity
        f_co = max(y_vec[0], 0.0)
        f_h2 = max(y_vec[1], 0.0)
        f_co2 = max(y_vec[2], 0.0)
        f_h2o = max(y_vec[3], 0.0)
        f_ch4 = max(y_vec[4], 0.0)
        f_n2 = max(y_vec[5], 0.0)
        f_c_solid = max(y_vec[6], 1.0e-8)
        t_g = max(y_vec[7], 300.0)
        t_s = max(y_vec[8], 300.0)
        d_p = max(y_vec[9], 1.0e-4)

        # Local geometry
        area = self.geo.area_at(z)
        radius = self.geo.radius_at(z)
        perimeter = 2.0 * np.pi * radius

        # Total molar flow and mole fractions
        f_total = f_co + f_h2 + f_co2 + f_h2o + f_ch4 + f_n2
        if f_total <= 0:
            return np.zeros_like(y_vec)

        y_dict = {
            "CO": f_co / f_total,
            "H2": f_h2 / f_total,
            "CO2": f_co2 / f_total,
            "H2O": f_h2o / f_total,
            "CH4": f_ch4 / f_total,
            "N2": f_n2 / f_total,
        }

        # Superficial gas velocity (m/s)
        # Q = F_total * R * T_g / P
        q_gas = f_total * R_UNIVERSAL * t_g / self.op.pressure_pa
        u_gas = max(q_gas / (area * self.op.bed_void_fraction), 0.01)

        # Reaction rates in mol/(m3.s)
        rates = self.rxn.compute_rates(
            y=y_dict,
            t_gas_k=t_g,
            t_solid_k=t_s,
            d_p_m=d_p,
            void_fraction=self.op.bed_void_fraction,
            u_gas_m_s=u_gas,
            p_pa=self.op.pressure_pa,
        )

        r1 = rates["R1_boudouard"]
        r2 = rates["R2_water_gas"]
        r3 = rates["R3_methanation"]
        r4 = rates["R4_wgs"]
        a_p = rates["a_p"]
        h_gs = rates["h_gs"]

        # If solid char is fully consumed, char reactions cease
        if f_c_solid <= 1.0e-6:
            r1 = 0.0
            r2 = 0.0
            r3 = 0.0

        # Species molar flow derivatives: dF_i/dz = A * sum(nu_ij * R_j)
        df_co_dz = area * (2.0 * r1 + r2 - r4)
        df_h2_dz = area * (r2 - 2.0 * r3 + r4)
        df_co2_dz = area * (-r1 + r4)
        df_h2o_dz = area * (-r2 - r4)
        df_ch4_dz = area * r3
        df_n2_dz = 0.0

        # Char consumption rate
        df_c_solid_dz = -area * (r1 + r2 + r3)

        # Particle shrinking rate
        # Solid downward mass velocity
        m_char_flow = max(f_c_solid * M_C, 1.0e-8)
        u_solid = max(
            m_char_flow / (self.feed.char_density_kg_m3 * (1.0 - self.op.bed_void_fraction) * area),
            1.0e-5,
        )
        dd_p_dz = - (2.0 * M_C / (self.feed.char_density_kg_m3 * u_solid)) * (r1 + r2 + r3) / max(a_p, 1.0)
        # Cap shrinkage if particle becomes very small
        if d_p <= 1.0e-4:
            dd_p_dz = 0.0

        # Energy Balances
        # 1. Heat capacity flow of gas: sum(F_i * Cp_i)
        cp_flow_gas = (
            f_co * cp_molar("CO", t_g)
            + f_h2 * cp_molar("H2", t_g)
            + f_co2 * cp_molar("CO2", t_g)
            + f_h2o * cp_molar("H2O", t_g)
            + f_ch4 * cp_molar("CH4", t_g)
            + f_n2 * cp_molar("N2", t_g)
        )
        cp_flow_gas = max(cp_flow_gas, 1.0)

        # Wall heat loss per unit length (W/m)
        # Calibrated to dissipate measured 12.8% of energy
        dq_loss_dz = self.op.u_wall_w_m2_k * perimeter * (t_g - self.op.t_ambient_k)

        # Gas energy derivative:
        # Interphase heat exchange: h_gs * a_p * A * (T_s - T_g)
        # WGS reaction heat: (-Delta H_r4) * R4 * A
        dh_r4 = heat_of_reaction("wgs", t_g)
        q_interphase = h_gs * a_p * area * (t_s - t_g)
        dt_g_dz = (q_interphase - dh_r4 * r4 * area - dq_loss_dz) / cp_flow_gas

        # Solid char heat capacity flow: m_char * Cp_char
        cp_flow_solid = max(m_char_flow * (cp_molar("C", t_s) / M_C), 0.1)

        # Solid char energy derivative:
        # -Interphase heat loss + Endothermic gasification heats:
        dh_r1 = heat_of_reaction("boudouard", t_s)
        dh_r2 = heat_of_reaction("water_gas", t_s)
        dh_r3 = heat_of_reaction("methanation", t_s)
        q_rxn_solid = (-dh_r1 * r1 - dh_r2 * r2 - dh_r3 * r3) * area

        dt_s_dz = (-q_interphase + q_rxn_solid) / cp_flow_solid

        return np.array([
            df_co_dz,
            df_h2_dz,
            df_co2_dz,
            df_h2o_dz,
            df_ch4_dz,
            df_n2_dz,
            df_c_solid_dz,
            dt_g_dz,
            dt_s_dz,
            dd_p_dz,
        ])

    def solve(
        self,
        length_m: Optional[float] = None,
        num_points: int = 200,
    ) -> SimulationResults1D:
        """Execute 1D simulation across gasification zone [0, length_m]."""
        l_gasif = length_m if length_m is not None else self.geo.l_gasif_baseline_m

        # Compute initial state from flaming pyrolysis submodel
        inlet = compute_throat_inlet_state(self.feed, self.op)

        y0 = np.array([
            inlet["F_CO_0"],
            inlet["F_H2_0"],
            inlet["F_CO2_0"],
            inlet["F_H2O_0"],
            inlet["F_CH4_0"],
            inlet["F_N2_0"],
            inlet["F_C_solid_0"],
            inlet["T_g0"],
            inlet["T_s0"],
            inlet["d_p_0"],
        ])

        z_eval = np.linspace(0.0, l_gasif, num_points)

        sol = solve_ivp(
            fun=self._ode_derivatives,
            t_span=(0.0, l_gasif),
            y0=y0,
            t_eval=z_eval,
            method="Radau",
            rtol=1.0e-5,
            atol=1.0e-8,
        )

        if not sol.success:
            # Fall back to BDF if Radau encountered difficulty
            sol = solve_ivp(
                fun=self._ode_derivatives,
                t_span=(0.0, l_gasif),
                y0=y0,
                t_eval=z_eval,
                method="BDF",
                rtol=1.0e-5,
                atol=1.0e-8,
            )

        z_arr = sol.t
        y_sol = sol.y

        f_co = np.maximum(y_sol[0], 0.0)
        f_h2 = np.maximum(y_sol[1], 0.0)
        f_co2 = np.maximum(y_sol[2], 0.0)
        f_h2o = np.maximum(y_sol[3], 0.0)
        f_ch4 = np.maximum(y_sol[4], 0.0)
        f_n2 = np.maximum(y_sol[5], 0.0)
        f_c_solid = np.maximum(y_sol[6], 0.0)
        t_g = y_sol[7]
        t_s = y_sol[8]
        d_p = np.maximum(y_sol[9], 1.0e-4)

        # Dry mole fractions:
        f_dry_tot = f_co + f_h2 + f_co2 + f_ch4 + f_n2
        f_dry_tot = np.maximum(f_dry_tot, 1.0e-8)

        y_dry = {
            "CO": (f_co / f_dry_tot) * 100.0,
            "H2": (f_h2 / f_dry_tot) * 100.0,
            "CO2": (f_co2 / f_dry_tot) * 100.0,
            "CH4": (f_ch4 / f_dry_tot) * 100.0,
            "N2": (f_n2 / f_dry_tot) * 100.0,
        }

        # Carbon conversion X_C(z) = 1 - F_C(z) / F_C,0
        f_c_0 = inlet["F_C_solid_0"]
        x_c = np.clip(1.0 - (f_c_solid / f_c_0), 0.0, 1.0)

        # Producer gas flow rate in m3/h at standard conditions (0°C, 101.325 kPa)
        # 1 kmol = 22.414 Nm3 -> V_dot = F_dry_tot (mol/s) * 3600 / 1000 * 22.414
        gas_flow_m3_h = f_dry_tot * 3.6 * 22.414

        # Cold gas conversion efficiency along bed (Jayah et al. Table 7 basis: HHV = 19.6 MJ/kg)
        cge_arr = np.zeros_like(z_arr)
        hhv_biomass_mj_kg = self.feed.hhv_mj_kg
        feed_dry_kg_h = self.op.feed_rate_dry_kg_h

        for idx in range(len(z_arr)):
            syngas_dict = {k: y_dry[k][idx] / 100.0 for k in y_dry}
            lhv_gas_mj_nm3 = calculate_syngas_lhv_mj_nm3(syngas_dict)
            cge_arr[idx] = calculate_conversion_efficiency(
                gas_flow_m3_h_std=gas_flow_m3_h[idx],
                syngas_lhv_mj_nm3=lhv_gas_mj_nm3,
                biomass_feed_rate_dry_kg_h=feed_dry_kg_h,
                biomass_lhv_dry_mj_kg=hhv_biomass_mj_kg,
            )

        return SimulationResults1D(
            z_m=z_arr,
            f_co=f_co,
            f_h2=f_h2,
            f_co2=f_co2,
            f_h2o=f_h2o,
            f_ch4=f_ch4,
            f_n2=f_n2,
            f_c_solid=f_c_solid,
            t_gas_k=t_g,
            t_solid_k=t_s,
            d_p_m=d_p,
            y_dry=y_dry,
            carbon_conversion=x_c,
            cold_gas_efficiency_percent=cge_arr,
            gas_flow_m3_h=gas_flow_m3_h,
        )

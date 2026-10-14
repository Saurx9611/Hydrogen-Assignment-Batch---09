"""
src/reactions.py - Heterogeneous char gasification and homogeneous water-gas shift kinetics.
Incorporates boundary-layer film mass transfer resistance, surface kinetics,
particle shrinkage, and interphase heat exchange.
"""

from typing import Dict, Tuple
import numpy as np
from src.config import (
    KineticConstants,
    R_UNIVERSAL,
    ATM_TO_PA,
    M_C,
)
from src.thermo import (
    gas_viscosity_pa_s,
    gas_thermal_conductivity_w_m_k,
    binary_diffusivity_m2_s,
    kp_boudouard,
    kp_water_gas,
    kp_methanation,
    keq_wgs,
    heat_of_reaction,
)


class ReactionModel:
    """Manages kinetic rates, interphase transport, and energy sources."""

    def __init__(self, kinetics: KineticConstants = None):
        self.k = kinetics or KineticConstants()

    def packed_bed_transport(
        self,
        d_p_m: float,
        void_fraction: float,
        u_gas_m_s: float,
        t_gas_k: float,
        p_pa: float = 101325.0,
    ) -> Tuple[float, Dict[str, float], float]:
        """
        Calculate specific surface area a_p, film mass transfer coefficients k_m,
        and interphase heat transfer coefficient h_gs.

        Returns:
            a_p: specific external surface area (m2 / m3 bed)
            km_dict: {species: mass_transfer_coeff (m/s)}
            h_gs: interphase heat transfer coefficient (W/(m2.K))
        """
        d_p_m = max(float(d_p_m), 1.0e-4)
        void_fraction = float(np.clip(void_fraction, 0.2, 0.8))
        t_gas_k = max(float(t_gas_k), 300.0)

        # External specific surface area for spherical particles in packed bed
        a_p = 6.0 * (1.0 - void_fraction) / d_p_m

        # Fluid properties
        rho_g = (p_pa * 0.028) / (R_UNIVERSAL * t_gas_k)  # approximate syngas density
        mu_g = gas_viscosity_pa_s(t_gas_k)
        k_g = gas_thermal_conductivity_w_m_k(t_gas_k)

        # Particle Reynolds number (based on superficial velocity)
        re_p = max(rho_g * u_gas_m_s * d_p_m / mu_g, 1.0e-3)

        # Prandtl number: Pr = mu * Cp / k_g ~ 0.72 for syngas
        pr = 0.72

        # Interphase heat transfer: Convection (Ranz & Marshall, 1952) + Radiation at high temperature
        nu_p = 2.0 + 0.6 * (re_p ** 0.5) * (pr ** (1.0 / 3.0))
        h_conv = nu_p * k_g / d_p_m
        sigma_sb = 5.670374419e-8
        eps_rad = 0.85  # emissivity of wood char / gas mixture
        h_rad = 4.0 * sigma_sb * eps_rad * (t_gas_k ** 3)
        h_gs = h_conv + h_rad

        # Mass transfer coefficients for CO2, H2O, H2 (Wakao & Funazkri, 1978)
        km_dict = {}
        for sp in ["CO2", "H2O", "H2"]:
            d_ab = binary_diffusivity_m2_s(sp, t_gas_k, p_pa)
            sc = mu_g / (rho_g * d_ab)
            sh_p = 2.0 + 1.1 * (re_p ** 0.6) * (sc ** (1.0 / 3.0))
            km_dict[sp] = sh_p * d_ab / d_p_m

        return a_p, km_dict, h_gs

    def compute_rates(
        self,
        y: Dict[str, float],
        t_gas_k: float,
        t_solid_k: float,
        d_p_m: float,
        void_fraction: float,
        u_gas_m_s: float,
        p_pa: float = 101325.0,
    ) -> Dict[str, float]:
        """
        Compute volumetric reaction rates R1, R2, R3, R4 in mol/(m3.s).

        Reactions:
          R1 (Boudouard):     C + CO2 -> 2 CO
          R2 (Water-gas):     C + H2O -> CO + H2
          R3 (Methanation):   C + 2 H2 -> CH4
          R4 (WGS):           CO + H2O <-> CO2 + H2
        """
        t_solid_k = float(np.clip(t_solid_k, 300.0, 2500.0))
        t_gas_k = float(np.clip(t_gas_k, 300.0, 2500.0))
        d_p_m = max(float(d_p_m), 1.0e-4)

        # Partial pressures in atm
        p_atm = p_pa / ATM_TO_PA
        p_co = max(y.get("CO", 0.0), 0.0) * p_atm
        p_co2 = max(y.get("CO2", 0.0), 0.0) * p_atm
        p_h2 = max(y.get("H2", 0.0), 0.0) * p_atm
        p_h2o = max(y.get("H2O", 0.0), 0.0) * p_atm
        p_ch4 = max(y.get("CH4", 0.0), 0.0) * p_atm

        # Molar concentrations in mol/m3
        c_total = p_pa / (R_UNIVERSAL * t_gas_k)
        c_co = max(y.get("CO", 0.0), 0.0) * c_total
        c_co2 = max(y.get("CO2", 0.0), 0.0) * c_total
        c_h2 = max(y.get("H2", 0.0), 0.0) * c_total
        c_h2o = max(y.get("H2O", 0.0), 0.0) * c_total

        # Transport properties
        a_p, km_dict, h_gs = self.packed_bed_transport(
            d_p_m, void_fraction, u_gas_m_s, t_gas_k, p_pa
        )

        # ----------------------------------------------------
        # 1. Boudouard Reaction: C + CO2 <-> 2 CO
        # ----------------------------------------------------
        kp1 = kp_boudouard(t_solid_k)  # P_CO^2 / P_CO2 (atm)
        # Driving force: (P_CO2 - P_CO^2 / Kp1)
        df1 = max(0.0, p_co2 - (p_co ** 2) / max(kp1, 1.0e-10))

        # Intrinsic kinetic constant (m/(s.atm))
        kr1 = self.k.a1 * np.exp(-self.k.e1 / (R_UNIVERSAL * t_solid_k))

        # Combined film mass transfer and chemical resistance:
        # km1 is in m/s; converting kr1 from m/(s.atm) to m/s: kr1_eff = kr1 * (R*Ts/ATM_TO_PA)
        km1 = km_dict.get("CO2", 0.05)
        # Rate per unit char area in mol/(m2.s):
        # r1'' = df1 / [ (R*Ts / kr1) + (R*Tg / km1) ]
        denom1 = (R_UNIVERSAL * t_solid_k / max(kr1, 1.0e-20)) + (
            R_UNIVERSAL * t_gas_k / (km1 * ATM_TO_PA)
        )
        r1_double_prime = (df1 * ATM_TO_PA) / denom1  # mol/(m2.s)
        r1 = a_p * r1_double_prime  # mol/(m3.s)

        # ----------------------------------------------------
        # 2. Water-Gas Reaction: C + H2O <-> CO + H2
        # ----------------------------------------------------
        kp2 = kp_water_gas(t_solid_k)  # (P_CO * P_H2) / P_H2O (atm)
        df2 = max(0.0, p_h2o - (p_co * p_h2) / max(kp2, 1.0e-10))

        kr2 = self.k.a2 * np.exp(-self.k.e2 / (R_UNIVERSAL * t_solid_k))
        km2 = km_dict.get("H2O", 0.05)
        denom2 = (R_UNIVERSAL * t_solid_k / max(kr2, 1.0e-20)) + (
            R_UNIVERSAL * t_gas_k / (km2 * ATM_TO_PA)
        )
        r2_double_prime = (df2 * ATM_TO_PA) / denom2
        r2 = a_p * r2_double_prime  # mol/(m3.s)

        # ----------------------------------------------------
        # 3. Methanation Reaction: C + 2 H2 <-> CH4
        # ----------------------------------------------------
        kp3 = kp_methanation(t_solid_k)  # P_CH4 / P_H2^2 (atm^-1)
        df3 = max(0.0, (p_h2 ** 2) - p_ch4 / max(kp3, 1.0e-10))

        kr3 = self.k.a3 * np.exp(-self.k.e3 / (R_UNIVERSAL * t_solid_k))
        km3 = km_dict.get("H2", 0.10)
        denom3 = (R_UNIVERSAL * t_solid_k / max(kr3, 1.0e-20)) + (
            R_UNIVERSAL * t_gas_k / (km3 * ATM_TO_PA)
        )
        r3_double_prime = (df3 * ATM_TO_PA) / denom3
        r3 = a_p * r3_double_prime  # mol/(m3.s)

        # ----------------------------------------------------
        # 4. Homogeneous Water-Gas Shift: CO + H2O <-> CO2 + H2
        # ----------------------------------------------------
        keq4 = keq_wgs(t_gas_k)
        kwgs = self.k.a_wgs * np.exp(-self.k.e_wgs / (R_UNIVERSAL * t_gas_k))
        # Rate = void_fraction * kwgs * [ C_CO * C_H2O - C_CO2 * C_H2 / Keq ]
        driving_wgs = c_co * c_h2o - (c_co2 * c_h2) / max(keq4, 1.0e-10)
        r4 = void_fraction * kwgs * driving_wgs  # mol/(m3.s)

        return {
            "R1_boudouard": max(0.0, r1),
            "R2_water_gas": max(0.0, r2),
            "R3_methanation": max(0.0, r3),
            "R4_wgs": r4,
            "a_p": a_p,
            "h_gs": h_gs,
        }

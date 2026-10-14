"""
src/flaming_pyrolysis.py - Upstream drying, pyrolysis, and flaming oxidation submodel.
Follows Milligan (1994) as adopted by Jayah et al. (2003, Section 3, p. 460).
Determines throat inlet gas molar flow rates, char feed rate, and flame temperature (~1600 K).
"""

from typing import Dict, Tuple
import numpy as np
from src.config import (
    FeedstockProperties,
    OperatingConditions,
    R_UNIVERSAL,
    M_C,
    M_H2,
    M_O2,
    M_N2,
    M_CO,
    M_CO2,
    M_H2O,
    M_CH4,
)
from src.feedstock import BiomassAnalysis
from src.thermo import keq_wgs, enthalpy_sensible, HF_298


def compute_throat_inlet_state(
    feedstock: FeedstockProperties,
    operating: OperatingConditions,
) -> Dict[str, float]:
    """
    Computes initial conditions at the throat entrance (z = 0):
      - Molar flow rates of CO, H2, CO2, H2O, CH4, N2 (mol/s)
      - Solid char carbon flow rate (mol/s)
      - Initial char particle diameter (m)
      - Peak throat gas temperature T_g0 (K) (~1600 K)
      - Initial char temperature T_s0 (K)
    """
    # 1. Feedstock mass flow rates (kg/s)
    m_wood_dry_kg_s = operating.feed_rate_dry_kg_h / 3600.0
    m_moist_kg_s = m_wood_dry_kg_s * operating.moisture_content_db
    m_air_kg_s = operating.air_flow_rate_kg_h / 3600.0

    # If air_fuel_ratio is specified differently from feed/air:
    if operating.air_fuel_ratio > 0:
        m_air_kg_s = m_wood_dry_kg_s * operating.air_fuel_ratio

    # 2. Elemental molar inflow from wood (mol/s)
    # C, H, O, N in dry wood
    c_wood_mass_frac = feedstock.c_percent / 100.0
    h_wood_mass_frac = feedstock.h_percent / 100.0
    o_wood_mass_frac = feedstock.o_percent / 100.0
    n_wood_mass_frac = feedstock.n_percent / 100.0
    fc_mass_frac = feedstock.fc_db / 100.0

    # Char entering reduction zone is fixed carbon (pure carbon assumption)
    m_char_dry_kg_s = m_wood_dry_kg_s * fc_mass_frac
    f_c_solid_0 = m_char_dry_kg_s / M_C  # mol C(s) / s

    # Volatiles entering flaming zone:
    c_vol_mol_s = (m_wood_dry_kg_s * (c_wood_mass_frac - fc_mass_frac)) / M_C
    h_wood_mol_s = (m_wood_dry_kg_s * h_wood_mass_frac) / 0.001008
    o_wood_mol_s = (m_wood_dry_kg_s * o_wood_mass_frac) / 0.015999
    n_wood_mol_s = (m_wood_dry_kg_s * n_wood_mass_frac) / 0.014007

    # Moisture inflow:
    h2o_moist_mol_s = m_moist_kg_s / M_H2O

    # Air inflow (assumed dry air: 21% O2, 79% N2 molar, M_air = 28.97 g/mol)
    air_moles_s = m_air_kg_s / 0.02897
    o2_air_mol_s = air_moles_s * 0.21
    n2_air_mol_s = air_moles_s * 0.79

    # Total elemental atoms in gas phase entering flaming pyrolysis:
    c_gas_tot = c_vol_mol_s
    h_gas_tot = h_wood_mol_s + 2.0 * h2o_moist_mol_s
    o_gas_tot = o_wood_mol_s + h2o_moist_mol_s + 2.0 * o2_air_mol_s
    n_gas_tot = n_wood_mol_s + 2.0 * n2_air_mol_s

    # In flaming pyrolysis, oxygen is completely consumed.
    # Methane is formed by rapid pyrolysis tar-cracking; Jayah et al. observe ~1.1-1.3% CH4 in dry gas.
    # We estimate CH4 moles corresponding to ~1.2% dry syngas volume.
    approx_dry_gas_mol_s = n2_air_mol_s / 0.53  # N2 is ~52-54% of dry syngas
    f_ch4_0 = approx_dry_gas_mol_s * 0.012

    # Remaining C, H, O to distribute among CO, CO2, H2, H2O:
    c_rem = max(c_gas_tot - f_ch4_0, 1.0e-5)
    h_rem = max(h_gas_tot - 4.0 * f_ch4_0, 1.0e-5)
    o_rem = max(o_gas_tot, 1.0e-5)

    # Let throat peak temperature T_0 ~ 1600 K (from Jayah Fig. 5)
    # At 1600 K, equilibrium Water-Gas Shift Keq ~ 0.27
    t_flame_k = 1600.0

    # Solve for equilibrium between CO, CO2, H2, H2O subject to:
    # 1) n_CO + n_CO2 = c_rem
    # 2) 2*n_H2 + 2*n_H2O = h_rem  => n_H2 + n_H2O = 0.5 * h_rem
    # 3) n_CO + 2*n_CO2 + n_H2O = o_rem
    # From (1) and (3): n_CO2 + n_H2O = o_rem - c_rem
    # Combining with (2): n_CO2 + (0.5 * h_rem - n_H2) = o_rem - c_rem
    # Along with WGS: (n_CO2 * n_H2) / (n_CO * n_H2O) = Keq(T_flame)

    keq = keq_wgs(t_flame_k)

    # Parametric quadratic solve for n_CO:
    # Let x = n_CO (0 <= x <= c_rem)
    # n_CO2 = c_rem - x
    # n_H2O = o_rem - c_rem - n_CO2 = o_rem - 2*c_rem + x
    # n_H2 = 0.5 * h_rem - n_H2O = 0.5 * h_rem - (o_rem - 2*c_rem + x)
    # Using 1D bisection or root-find on [0, c_rem]:
    def wgs_residual(x_co):
        n_co = x_co
        n_co2 = max(c_rem - n_co, 1.0e-8)
        n_h2o = max(o_rem - c_rem - n_co2, 1.0e-8)
        n_h2 = max(0.5 * h_rem - n_h2o, 1.0e-8)
        return (n_co2 * n_h2) / (n_co * n_h2o) - keq

    # Bisect on allowable bounds
    x_min = max(1.0e-6, 2.0 * c_rem - o_rem)
    x_max = min(c_rem - 1.0e-6, 2.0 * c_rem - o_rem + 0.5 * h_rem)
    if x_min >= x_max:
        x_min = 0.1 * c_rem
        x_max = 0.9 * c_rem

    x_co = 0.5 * (x_min + x_max)
    for _ in range(50):
        res = wgs_residual(x_co)
        if abs(res) < 1.0e-6:
            break
        if res > 0:
            x_min = x_co
        else:
            x_max = x_co
        x_co = 0.5 * (x_min + x_max)

    f_co_0 = max(x_co, 1.0e-6)
    f_co2_0 = max(c_rem - f_co_0, 1.0e-6)
    f_h2o_0 = max(o_rem - c_rem - f_co2_0, 1.0e-6)
    f_h2_0 = max(0.5 * h_rem - f_h2o_0, 1.0e-6)
    f_n2_0 = 0.5 * n_gas_tot

    # Initial particle diameter equals fuel chip nominal size
    d_p_0 = operating.chip_size_m

    return {
        "F_CO_0": f_co_0,
        "F_H2_0": f_h2_0,
        "F_CO2_0": f_co2_0,
        "F_H2O_0": f_h2o_0,
        "F_CH4_0": f_ch4_0,
        "F_N2_0": f_n2_0,
        "F_C_solid_0": f_c_solid_0,
        "d_p_0": d_p_0,
        "T_g0": t_flame_k,
        "T_s0": t_flame_k - 50.0,
    }

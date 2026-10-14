"""
src/thermo.py - Thermochemical and transport properties of gas species and solid char.
Implements specific heats Cp(T), sensible enthalpies, heats of reaction,
chemical equilibrium constants, and packed-bed transport properties.
"""

import numpy as np
from src.config import R_UNIVERSAL, ATM_TO_PA

# Standard enthalpies of formation at 298.15 K (J/mol)
# NIST Chemistry WebBook values
HF_298 = {
    "CO": -110530.0,
    "CO2": -393520.0,
    "H2O": -241820.0,  # gas phase
    "CH4": -74850.0,
    "H2": 0.0,
    "N2": 0.0,
    "O2": 0.0,
    "C": 0.0,          # graphite/char
}

# Polynomial coefficients for molar heat capacity Cp(T) = a + b*T + c*T^2 + d*T^3 (J/(mol.K))
# Valid for 300 K <= T <= 2000 K (Smith, Van Ness, Abbott / Perry's Handbook)
CP_COEFFS = {
    "CO":   [28.16,  0.1675e-2,  0.5372e-5, -2.222e-9],
    "CO2":  [22.26,  5.9810e-2, -3.5010e-5,  7.469e-9],
    "H2O":  [32.24,  0.1923e-2,  1.0550e-5, -3.595e-9],
    "CH4":  [19.89,  5.0240e-2,  1.2690e-5, -11.01e-9],
    "H2":   [27.14,  0.9274e-2, -1.3810e-5,  7.645e-9],
    "N2":   [28.90, -0.1571e-2,  0.8081e-5, -2.873e-9],
    "O2":   [25.48,  1.5200e-2, -0.7155e-5,  1.312e-9],
    "C":    [11.18,  1.0950e-2, -0.4891e-5,  0.0],
}


def cp_molar(species: str, t_k: float) -> float:
    """Calculate molar specific heat capacity Cp at temperature T (K) in J/(mol.K)."""
    t_k = float(np.clip(t_k, 250.0, 2500.0))
    coeffs = CP_COEFFS.get(species, CP_COEFFS["N2"])
    return coeffs[0] + coeffs[1] * t_k + coeffs[2] * (t_k ** 2) + coeffs[3] * (t_k ** 3)


def enthalpy_sensible(species: str, t_k: float) -> float:
    """Calculate sensible enthalpy int_{298.15}^T Cp(T') dT' in J/mol."""
    t_k = float(np.clip(t_k, 250.0, 2500.0))
    t0 = 298.15
    coeffs = CP_COEFFS.get(species, CP_COEFFS["N2"])
    a, b, c, d = coeffs

    def int_cp(t):
        return a * t + 0.5 * b * (t ** 2) + (c / 3.0) * (t ** 3) + 0.25 * d * (t ** 4)

    return int_cp(t_k) - int_cp(t0)


def heat_of_reaction(reaction_id: str, t_k: float) -> float:
    """
    Calculate reaction enthalpy Delta H_r(T) in J/mol at temperature T (K).
    Reactions:
      'boudouard': C(s) + CO2 -> 2 CO
      'water_gas': C(s) + H2O -> CO + H2
      'methanation': C(s) + 2 H2 -> CH4
      'wgs': CO + H2O -> CO2 + H2
    """
    if reaction_id == "boudouard":
        # C + CO2 -> 2 CO
        dh298 = 2.0 * HF_298["CO"] - (HF_298["C"] + HF_298["CO2"])
        delta_h_sens = 2.0 * enthalpy_sensible("CO", t_k) - (
            enthalpy_sensible("C", t_k) + enthalpy_sensible("CO2", t_k)
        )
        return dh298 + delta_h_sens

    elif reaction_id == "water_gas":
        # C + H2O -> CO + H2
        dh298 = (HF_298["CO"] + HF_298["H2"]) - (HF_298["C"] + HF_298["H2O"])
        delta_h_sens = (enthalpy_sensible("CO", t_k) + enthalpy_sensible("H2", t_k)) - (
            enthalpy_sensible("C", t_k) + enthalpy_sensible("H2O", t_k)
        )
        return dh298 + delta_h_sens

    elif reaction_id == "methanation":
        # C + 2 H2 -> CH4
        dh298 = HF_298["CH4"] - (HF_298["C"] + 2.0 * HF_298["H2"])
        delta_h_sens = enthalpy_sensible("CH4", t_k) - (
            enthalpy_sensible("C", t_k) + 2.0 * enthalpy_sensible("H2", t_k)
        )
        return dh298 + delta_h_sens

    elif reaction_id == "wgs":
        # CO + H2O -> CO2 + H2
        dh298 = (HF_298["CO2"] + HF_298["H2"]) - (HF_298["CO"] + HF_298["H2O"])
        delta_h_sens = (enthalpy_sensible("CO2", t_k) + enthalpy_sensible("H2", t_k)) - (
            enthalpy_sensible("CO", t_k) + enthalpy_sensible("H2O", t_k)
        )
        return dh298 + delta_h_sens

    else:
        raise ValueError(f"Unknown reaction_id: {reaction_id}")


# Equilibrium constants (Chen 1987, Yoon et al. 1978, Jayah 2002)
def kp_boudouard(t_k: float) -> float:
    """Equilibrium constant K_p1 for Boudouard reaction in atm: P_CO^2 / P_CO2."""
    t_k = float(np.clip(t_k, 400.0, 2500.0))
    ln_kp = -20922.0 / t_k + 20.35
    return float(np.exp(np.clip(ln_kp, -50.0, 50.0)))


def kp_water_gas(t_k: float) -> float:
    """Equilibrium constant K_p2 for Water-Gas reaction in atm: (P_CO * P_H2) / P_H2O."""
    t_k = float(np.clip(t_k, 400.0, 2500.0))
    ln_kp = -16326.0 / t_k + 17.59
    return float(np.exp(np.clip(ln_kp, -50.0, 50.0)))


def kp_methanation(t_k: float) -> float:
    """Equilibrium constant K_p3 for Methanation reaction in atm^-1: P_CH4 / P_H2^2."""
    t_k = float(np.clip(t_k, 400.0, 2500.0))
    ln_kp = 10480.0 / t_k - 12.35
    return float(np.exp(np.clip(ln_kp, -50.0, 50.0)))


def keq_wgs(t_k: float) -> float:
    """Equilibrium constant for Water-Gas Shift: (P_CO2 * P_H2) / (P_CO * P_H2O)."""
    t_k = float(np.clip(t_k, 400.0, 2500.0))
    ln_keq = 4276.0 / t_k - 3.961
    return float(np.exp(np.clip(ln_keq, -20.0, 20.0)))


# Transport properties of syngas mixture
def gas_viscosity_pa_s(t_k: float) -> float:
    """
    Approximate dynamic viscosity of syngas mixture (Pa.s) using Sutherland-type formula.
    Base: Producer gas dominated by N2, CO, CO2.
    """
    t_k = float(np.clip(t_k, 300.0, 2500.0))
    # Sutherland formula for N2/CO: mu_0 = 1.78e-5 Pa.s at 300 K, S = 111 K
    return 1.78e-5 * ((t_k / 300.0) ** 1.5) * ((300.0 + 111.0) / (t_k + 111.0))


def gas_thermal_conductivity_w_m_k(t_k: float) -> float:
    """Thermal conductivity of gas mixture (W/(m.K))."""
    t_k = float(np.clip(t_k, 300.0, 2500.0))
    return 0.026 * ((t_k / 300.0) ** 0.8)


def binary_diffusivity_m2_s(species: str, t_k: float, p_pa: float = 101325.0) -> float:
    """
    Effective binary diffusion coefficient of species in syngas/N2 mixture (m2/s).
    Scales with T^1.75 / P (Fuller-Schettler-Giddings).
    """
    t_k = float(np.clip(t_k, 300.0, 2500.0))
    # Base diffusivities at 300 K, 1 atm
    d0_map = {
        "H2": 7.5e-5,
        "CH4": 2.2e-5,
        "CO": 2.0e-5,
        "H2O": 2.5e-5,
        "CO2": 1.6e-5,
        "N2": 2.0e-5,
    }
    d0 = d0_map.get(species, 2.0e-5)
    return d0 * ((t_k / 300.0) ** 1.75) * (ATM_TO_PA / p_pa)

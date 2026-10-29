"""
tests/test_thermo.py - Unit tests for thermodynamic and transport property functions.
"""

import pytest
import numpy as np
from src.thermo import (
    cp_molar,
    enthalpy_sensible,
    heat_of_reaction,
    kp_boudouard,
    kp_water_gas,
    kp_methanation,
    keq_wgs,
    gas_viscosity_pa_s,
    gas_thermal_conductivity_w_m_k,
    binary_diffusivity_m2_s,
)


def test_heat_capacities_positive():
    species_list = ["CO", "CO2", "H2O", "CH4", "H2", "N2", "C"]
    temps = [300.0, 600.0, 1000.0, 1500.0, 2000.0]

    for sp in species_list:
        for t in temps:
            cp = cp_molar(sp, t)
            assert cp > 0.0, f"Cp for {sp} at {t} K is non-positive: {cp}"
            assert 5.0 <= cp <= 100.0, f"Cp for {sp} at {t} K out of bounds: {cp}"


def test_sensible_enthalpy_monotonic():
    species_list = ["CO", "CO2", "H2O", "H2", "N2"]
    for sp in species_list:
        h300 = enthalpy_sensible(sp, 300.0)
        h1000 = enthalpy_sensible(sp, 1000.0)
        h1500 = enthalpy_sensible(sp, 1500.0)
        assert h300 < h1000 < h1500


def test_reaction_enthalpies():
    # Standard 298 K reaction heats:
    # Boudouard: +172.5 kJ/mol (endothermic)
    # Water-gas: +131.3 kJ/mol (endothermic)
    # Methanation: -74.8 kJ/mol (exothermic)
    # WGS: -41.2 kJ/mol (exothermic)
    dh1 = heat_of_reaction("boudouard", 298.15)
    dh2 = heat_of_reaction("water_gas", 298.15)
    dh3 = heat_of_reaction("methanation", 298.15)
    dh4 = heat_of_reaction("wgs", 298.15)

    assert pytest.approx(dh1 / 1000.0, 1.0) == 172.5
    assert pytest.approx(dh2 / 1000.0, 1.0) == 131.3
    assert pytest.approx(dh3 / 1000.0, 1.0) == -74.8
    assert pytest.approx(dh4 / 1000.0, 1.0) == -41.2


def test_equilibrium_constants_le_chatelier():
    # Endothermic reactions: Kp increases with T
    kp1_low = kp_boudouard(800.0)
    kp1_high = kp_boudouard(1500.0)
    assert kp1_high > kp1_low, "Boudouard Kp must increase with T"

    kp2_low = kp_water_gas(800.0)
    kp2_high = kp_water_gas(1500.0)
    assert kp2_high > kp2_low, "Water-gas Kp must increase with T"

    # Exothermic reactions: Kp decreases with T
    kp3_low = kp_methanation(800.0)
    kp3_high = kp_methanation(1500.0)
    assert kp3_low > kp3_high, "Methanation Kp must decrease with T"

    keq4_low = keq_wgs(800.0)
    keq4_high = keq_wgs(1500.0)
    assert keq4_low > keq4_high, "WGS Keq must decrease with T"


def test_transport_properties():
    t_vals = [300.0, 1000.0, 1600.0]
    for t in t_vals:
        mu = gas_viscosity_pa_s(t)
        k = gas_thermal_conductivity_w_m_k(t)
        d_co = binary_diffusivity_m2_s("CO", t)

        assert 1.0e-5 <= mu <= 6.0e-5
        assert 0.02 <= k <= 0.15
        assert 1.0e-5 <= d_co <= 1.0e-3

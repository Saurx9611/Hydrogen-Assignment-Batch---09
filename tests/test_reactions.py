"""
tests/test_reactions.py - Unit tests for reaction kinetics and packed-bed transport.
"""

import pytest
from src.reactions import ReactionModel


def test_reaction_model_packed_bed_transport():
    rxn = ReactionModel()
    a_p, km_dict, h_gs = rxn.packed_bed_transport(
        d_p_m=0.025,
        void_fraction=0.48,
        u_gas_m_s=0.5,
        t_gas_k=1200.0,
    )
    # a_p = 6 * (1 - 0.48) / 0.025 = 124.8 m2/m3
    assert pytest.approx(a_p, 1e-1) == 124.8
    assert h_gs > 10.0, "Interphase heat transfer h_gs must be positive and substantial"
    assert km_dict["CO2"] > 0.001
    assert km_dict["H2O"] > 0.001


def test_reaction_rates_non_negative():
    rxn = ReactionModel()
    y = {"CO": 0.15, "H2": 0.15, "CO2": 0.10, "H2O": 0.08, "CH4": 0.01, "N2": 0.51}
    rates = rxn.compute_rates(
        y=y,
        t_gas_k=1300.0,
        t_solid_k=1250.0,
        d_p_m=0.025,
        void_fraction=0.48,
        u_gas_m_s=0.5,
    )

    assert rates["R1_boudouard"] >= 0.0
    assert rates["R2_water_gas"] >= 0.0
    assert rates["R3_methanation"] >= 0.0
    assert isinstance(rates["R4_wgs"], float)

"""
tests/test_feedstock.py - Unit tests for feedstock stoichiometry, heating values, and efficiency.
"""

import pytest
from src.config import FeedstockProperties
from src.feedstock import BiomassAnalysis, calculate_syngas_lhv_mj_nm3, calculate_conversion_efficiency


def test_feedstock_proximate_sum():
    feed = FeedstockProperties()
    total_prox = feed.vm_db + feed.fc_db + feed.ash_db
    assert pytest.approx(total_prox, 1e-3) == 100.0


def test_feedstock_ultimate_sum():
    feed = FeedstockProperties()
    total_ult = feed.c_percent + feed.h_percent + feed.n_percent + feed.ash_percent + feed.o_percent
    assert pytest.approx(total_ult, 1e-3) == 100.0


def test_molar_formula():
    feed = FeedstockProperties()
    biomass = BiomassAnalysis(feed, moisture_content_db=0.15)
    alpha, beta, gamma, m_daf = biomass.molar_formula_daf

    # Carbon is normalized to 1.0
    # Rubber wood: C=50.6%, H=6.5%, O=42.0%, N=0.2%
    # mol C = 50.6/12.011 = 4.2128
    # mol H = 6.5/1.008 = 6.4484 => alpha ~ 1.53
    # mol O = 42.0/15.999 = 2.6252 => beta ~ 0.62
    assert 1.50 <= alpha <= 1.56
    assert 0.60 <= beta <= 0.65
    assert 0.002 <= gamma <= 0.005
    assert 0.022 <= m_daf <= 0.025  # kg/mol (~23.6 g/mol)


def test_lhv_values():
    feed = FeedstockProperties()
    biomass = BiomassAnalysis(feed, moisture_content_db=0.15)

    # HHV = 19.6 MJ/kg; LHV_dry should be ~18.17 MJ/kg
    assert 18.0 <= biomass.lhv_dry_mj_kg <= 18.3
    # Wet LHV at 15% d.b. (~13% w.b.) should be ~15.48 MJ/kg
    assert 15.0 <= biomass.lhv_as_received_mj_kg <= 16.0


def test_syngas_heating_value_and_efficiency():
    # Typical syngas composition from Table 5: CO: 19.1%, H2: 15.5%, CH4: 1.1%
    y_dry = {"CO": 0.191, "H2": 0.155, "CH4": 0.011, "CO2": 0.114, "N2": 0.529}
    lhv_nm3 = calculate_syngas_lhv_mj_nm3(y_dry)
    # Expected LHV of downdraft syngas is ~4.0 - 5.5 MJ/Nm3
    assert 4.0 <= lhv_nm3 <= 5.5

    # Test conversion efficiency:
    # 47.2 Nm3/h dry syngas at ~4.48 MJ/Nm3 with 18.6 kg/h dry wood at 19.6 MJ/kg HHV
    eff = calculate_conversion_efficiency(
        gas_flow_m3_h_std=47.2,
        syngas_lhv_mj_nm3=lhv_nm3,
        biomass_feed_rate_dry_kg_h=18.6,
        biomass_lhv_dry_mj_kg=19.6,
    )
    # Expected efficiency is in range 50% - 65% (Jayah baseline ~56%)
    assert 50.0 <= eff <= 65.0

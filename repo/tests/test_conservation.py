"""
tests/test_conservation.py - Automated physical conservation and consistency tests.
Verifies carbon elemental balance, nitrogen conservation, non-negativity, and thermal bounds.
"""

import pytest
import numpy as np
from src.reactor_1d import Reactor1D


def test_carbon_and_nitrogen_conservation():
    reactor = Reactor1D()
    res = reactor.solve(length_m=0.22, num_points=200)

    # 1. Total Carbon balance: C_solid + C_CO + C_CO2 + C_CH4 = constant
    total_carbon = res.f_c_solid + res.f_co + res.f_co2 + res.f_ch4
    c_in = total_carbon[0]
    c_out = total_carbon[-1]
    c_discrepancy_pct = abs(c_out - c_in) / c_in * 100.0

    assert c_discrepancy_pct < 0.2, f"Carbon balance violated: discrepancy {c_discrepancy_pct:.3f}%"

    # 2. Nitrogen conservation: F_N2(z) = constant
    n2_in = res.f_n2[0]
    n2_out = res.f_n2[-1]
    n2_discrepancy_pct = abs(n2_out - n2_in) / n2_in * 100.0

    assert n2_discrepancy_pct < 0.01, f"Nitrogen conservation violated: discrepancy {n2_discrepancy_pct:.4f}%"


def test_physical_bounds_and_non_negativity():
    reactor = Reactor1D()
    res = reactor.solve(length_m=0.22, num_points=100)

    # Check non-negative concentrations and flows
    assert np.all(res.f_co >= 0.0)
    assert np.all(res.f_h2 >= 0.0)
    assert np.all(res.f_co2 >= 0.0)
    assert np.all(res.f_h2o >= 0.0)
    assert np.all(res.f_ch4 >= 0.0)
    assert np.all(res.f_n2 >= 0.0)
    assert np.all(res.f_c_solid >= 0.0)

    # Check temperatures within realistic physical domain
    assert np.all((res.t_gas_k >= 300.0) & (res.t_gas_k <= 1800.0))
    assert np.all((res.t_solid_k >= 300.0) & (res.t_solid_k <= 1800.0))

    # Gas temperature should drop along the gasification bed
    # (starts at ~1600 K, drops due to endothermic Boudouard/steam reactions and heat loss)
    assert res.t_gas_k[-1] < res.t_gas_k[0]

    # Char particle diameter should decrease as char gasifies
    assert res.d_p_m[-1] < res.d_p_m[0]

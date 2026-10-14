"""
tests/test_solvers.py - Unit and integration tests for 1D and 2D numerical solvers.
"""

import pytest
import numpy as np
from src.reactor_1d import Reactor1D
from src.reactor_2d import Reactor2D
from src.validation import ModelValidator


def test_1d_solver_execution():
    reactor = Reactor1D()
    res = reactor.solve(length_m=0.22, num_points=100)

    assert len(res.z_m) == 100
    assert res.z_m[0] == 0.0
    assert pytest.approx(res.z_m[-1], 1e-4) == 0.22

    # Check that dry mole fractions sum to 100%
    dry_sum = (
        res.y_dry["CO"]
        + res.y_dry["H2"]
        + res.y_dry["CO2"]
        + res.y_dry["CH4"]
        + res.y_dry["N2"]
    )
    assert np.all(np.isclose(dry_sum, 100.0, atol=1e-2))

    # Check cold gas efficiency is in realistic range (~50-60%)
    assert 45.0 <= res.cold_gas_efficiency_percent[-1] <= 65.0


def test_2d_solver_execution():
    n_r, n_z = 21, 51
    reactor_2d = Reactor2D(n_r=n_r, n_z=n_z)
    res_2d = reactor_2d.solve(length_m=0.22)

    assert res_2d.t_gas_2d.shape == (n_r, n_z)
    assert res_2d.y_co_2d.shape == (n_r, n_z)
    assert res_2d.y_h2_2d.shape == (n_r, n_z)
    assert res_2d.u_z_2d.shape == (n_r, n_z)

    # Check wall is cooler than centerline due to heat loss
    t_centerline = res_2d.t_gas_2d[0, :]
    t_wall = res_2d.t_gas_2d[-1, :]
    assert np.all(t_wall <= t_centerline)


def test_validator_execution():
    validator = ModelValidator()
    calib = validator.validate_calibration_run()
    assert "comparison" in calib
    assert calib["MAE_percent"] < 2.0  # High accuracy match with Table 5

    runs = validator.validate_nine_runs()
    assert len(runs["runs_table"]) == 9
    assert "CO" in runs["statistical_summary"]

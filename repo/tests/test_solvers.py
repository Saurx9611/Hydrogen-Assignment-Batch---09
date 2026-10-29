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
    """2D model runs, shapes are consistent, wall is cooler than the axis and the
    flow-weighted exit state is close to (but not identical with) the 1D model."""
    from src.config import OperatingConditions
    op = OperatingConditions(chip_size_m=0.025, air_fuel_ratio=2.20, moisture_content_db=0.147)
    res_2d = Reactor2D(operating=op, n_cells=8, n_z=41).solve(length_m=0.22)
    n_nodes = 8 + 2
    assert res_2d.t_gas_2d.shape == (n_nodes, 41)
    assert res_2d.y_co_2d.shape == (n_nodes, 41)
    assert np.all(res_2d.t_gas_2d[-1, 1:] <= res_2d.t_gas_2d[0, 1:] + 1e-6)
    assert abs(sum(res_2d.mixed_dry_exit.values()) - 100.0) < 1e-6
    res_1d = Reactor1D(operating=op).solve(0.22, 100)
    assert abs(res_2d.mixed_dry_exit["CO"] - res_1d.y_dry["CO"][-1]) < 3.0


def test_2d_reduces_to_1d_with_strong_mixing(monkeypatch):
    """With very large radial dispersion the 2D model must collapse onto the 1D model."""
    import src.reactor_2d as r2
    from src.config import OperatingConditions
    monkeypatch.setattr(r2, "PE_MASS", 1e-4)
    monkeypatch.setattr(r2, "PE_HEAT", 1e-4)
    op = OperatingConditions(chip_size_m=0.025, air_fuel_ratio=2.20, moisture_content_db=0.147, u_wall_w_m2_k=5.0)
    r2d = r2.Reactor2D(operating=op, n_cells=4, n_z=21).solve(0.10)
    r1d = Reactor1D(operating=op).solve(0.10, 50)
    for sp in ("CO", "H2", "CO2"):
        assert abs(r2d.mixed_dry_exit[sp] - r1d.y_dry[sp][-1]) < 0.3


def test_validator_execution():
    validator = ModelValidator()
    calib = validator.validate_calibration_run()
    assert "comparison" in calib
    assert calib["MAE_percent"] < 1.0  # calibration target (Table 5)
    assert abs(calib["wall_loss_percent"] - 12.8) < 0.2  # calibrated heat loss

    runs = validator.validate_nine_runs()
    assert len(runs["runs_table"]) == 9
    st = runs["statistical_summary"]["CO"]
    # statistics are computed, not hard-coded: recompute and compare
    m = np.array([r["CO_meas"] for r in runs["runs_table"]])
    s_ = np.array([r["CO_sim"] for r in runs["runs_table"]])
    assert abs(st["MAE"] - np.mean(np.abs(s_ - m))) < 1e-9
    r2 = 1 - np.sum((s_ - m) ** 2) / np.sum((m - m.mean()) ** 2)
    assert abs(st["R2_vs_1to1"] - r2) < 1e-9


def test_throat_temperature_responds_to_operating_conditions():
    """Energy-balance anchored throat temperature: more air -> hotter, more moisture -> colder."""
    from src.config import OperatingConditions, FeedstockProperties
    from src.flaming_pyrolysis import throat_temperature
    f = FeedstockProperties()
    base = OperatingConditions(air_fuel_ratio=2.20, moisture_content_db=0.147)
    t_base, _ = throat_temperature(f, base)
    assert abs(t_base - base.throat_t_anchor_k) < 1.0
    t_air, _ = throat_temperature(f, OperatingConditions(air_fuel_ratio=2.40, moisture_content_db=0.147))
    t_wet, _ = throat_temperature(f, OperatingConditions(air_fuel_ratio=2.20, moisture_content_db=0.30))
    t_hot, _ = throat_temperature(f, OperatingConditions(air_fuel_ratio=2.20, moisture_content_db=0.147, t_air_in_k=450.0))
    assert t_air > t_base and t_wet < t_base and t_hot > t_base


def test_energy_and_element_closure():
    from src.config import OperatingConditions
    from src.balances import closure
    res = Reactor1D(operating=OperatingConditions(chip_size_m=0.025, air_fuel_ratio=2.2, moisture_content_db=0.147)).solve(0.22, 200)
    c = closure(res)
    for el in c["elements"].values():
        assert abs(el["error_percent"]) < 1e-6
    assert abs(c["energy"]["residual_percent_of_feed_HHV"]) < 0.5

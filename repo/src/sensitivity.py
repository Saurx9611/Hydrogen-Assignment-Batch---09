"""
src/sensitivity.py - Parametric study mirroring Jayah et al. (2003) Section 8 / Table 7.

Base case for the sweeps (Jayah's simulation base is not fully stated in the paper):
3 cm chips, MC 15 % d.b., AFR 2.20, air at 300 K, 61 deg throat, 12.8 % heat loss.
Each case is integrated to 50 cm so that the efficiency-vs-length curve and the optimum
length can be evaluated. The optimum length follows Jayah's definition: the length at
which the conversion efficiency reaches 99.5 % of its ultimate (maximum) value.

Heat loss is specified, as in Jayah et al., as % of input energy over the 22 cm hearth;
the wall coefficient U that gives that loss is found for each case.
"""

import dataclasses
from typing import Dict, Any
import numpy as np
from scipy.optimize import brentq

from src.config import ReactorGeometry, FeedstockProperties, OperatingConditions, KineticConstants
from src.reactor_1d import Reactor1D, SimulationResults1D
from src.feedstock import calculate_syngas_lhv_mj_nm3

L_MAX = 0.50
BASE_OP = OperatingConditions(chip_size_m=0.03, air_fuel_ratio=2.20, moisture_content_db=0.15,
                              feed_rate_dry_kg_h=18.6)


def run_case(op=BASE_OP, geo=None, kin=None, length=L_MAX, n=301) -> SimulationResults1D:
    return Reactor1D(geo or ReactorGeometry(), FeedstockProperties(), op, kin or KineticConstants()).solve(length, n)


def optimum_length(res: SimulationResults1D) -> Dict[str, float]:
    eff = res.cold_gas_efficiency_percent
    z_cm = res.z_m * 100.0
    ultimate = float(np.max(eff))
    target = 0.995 * ultimate
    idx = int(np.argmax(eff >= target))
    # linear interpolation between idx-1 and idx
    if idx > 0:
        z_opt = float(np.interp(target, [eff[idx - 1], eff[idx]], [z_cm[idx - 1], z_cm[idx]]))
    else:
        z_opt = float(z_cm[0])
    return {
        "eff_22cm": float(np.interp(22.0, z_cm, eff)),
        "ultimate_eff": ultimate,
        "z_at_ultimate_cm": float(z_cm[int(np.argmax(eff))]),
        "optimum_length_cm": z_opt,
        "eff_at_optimum": target,
    }


def u_for_heat_loss(op, percent, geo=None, kin=None):
    f = lambda u: run_case(dataclasses.replace(op, u_wall_w_m2_k=u), geo, kin, 0.22, 80).wall_loss_percent[-1] - percent
    return brentq(f, 0.5, 600.0, xtol=0.05)


def run_table7_study() -> Dict[str, Any]:
    out: Dict[str, Any] = {"base": dataclasses.asdict(BASE_OP)}

    def family(name, values, make):
        curves, summary = {}, []
        for v in values:
            op, geo = make(v)
            res = run_case(op, geo)
            curves[v] = res
            s = optimum_length(res)
            s["value"] = v
            s["u_wall"] = op.u_wall_w_m2_k
            s["wall_loss_22cm_percent"] = float(np.interp(0.22, res.z_m, res.wall_loss_percent))
            summary.append(s)
        out[name] = {"curves": curves, "summary": summary}

    family("chip_size_cm", [1.0, 3.0, 5.0],
           lambda v: (dataclasses.replace(BASE_OP, chip_size_m=v / 100.0), None))
    family("moisture_content_percent_db", [0.0, 15.0, 30.0],
           lambda v: (dataclasses.replace(BASE_OP, moisture_content_db=max(v, 1e-4) / 100.0), None))
    family("heat_loss_percent_input_energy", [5.0, 10.0, 15.0],
           lambda v: (dataclasses.replace(BASE_OP, u_wall_w_m2_k=u_for_heat_loss(BASE_OP, v)), None))
    family("throat_angle_degrees", [30.0, 61.0, 90.0],
           lambda v: (BASE_OP, ReactorGeometry(throat_angle_deg=v)))
    family("air_temperature_k", [300.0, 450.0, 600.0],
           lambda v: (dataclasses.replace(BASE_OP, t_air_in_k=v), None))
    return out


def run_operating_sweeps() -> Dict[str, Any]:
    """AFR and feed-rate sweeps at 22 cm (not in Jayah's Table 7)."""
    def at22(op):
        r = run_case(op, length=0.22, n=120)
        y = {k: r.y_dry[k][-1] / 100.0 for k in r.y_dry}
        return {"lhv": float(calculate_syngas_lhv_mj_nm3(y)), "cge": float(r.cold_gas_efficiency_percent[-1]),
                "t_exit": float(r.t_gas_k[-1]), "t_throat": float(r.t_gas_k[0]), "flow": float(r.gas_flow_m3_h[-1]),
                "CO": y["CO"] * 100, "H2": y["H2"] * 100, "CO2": y["CO2"] * 100, "xc": float(r.carbon_conversion[-1])}

    afr = np.round(np.linspace(1.8, 2.6, 9), 2)
    feed = np.linspace(12.0, 24.0, 7)
    return {
        "afr": [dict(value=float(a), **at22(dataclasses.replace(BASE_OP, air_fuel_ratio=float(a)))) for a in afr],
        "feed": [dict(value=float(f), **at22(dataclasses.replace(BASE_OP, feed_rate_dry_kg_h=float(f)))) for f in feed],
    }

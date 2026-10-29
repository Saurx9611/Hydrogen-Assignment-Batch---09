"""
src/calibration.py - Calibration of three parameters against Jayah et al. (2003) data
that are NOT used again for validation:

  1. u_wall_w_m2_k  : chosen so that the wall heat loss over the 22 cm hearth equals
                      12.8 % of the dry-feed HHV input - the heat loss Jayah et al.
                      measured by energy balance (Section 8.4). Jayah et al. also treat
                      heat loss as a % of input energy in their gasification-zone model
                      (Fig. 9).
  2. eta_boudouard  } char-reactivity / pore-diffusion effectiveness factors, fitted
  3. eta_water_gas  } to the measured CO, H2 and CO2 of Table 5 (the 2.5 cm chip
                      calibration run, identified in the paper as Run No. 7:
                      MC 14.7 % d.b., AFR 1.86). N2 is the closure, CH4 is imposed.

The nine Table 3 runs and the Fig. 5 temperatures are kept for validation.
Run:  python -m src.calibration      (prints the values to copy into src/config.py)
"""
import dataclasses
import json
from pathlib import Path
from scipy.optimize import minimize, brentq

from src.config import ReactorGeometry, FeedstockProperties, OperatingConditions, KineticConstants
from src.reactor_1d import Reactor1D

CALIB_OP = OperatingConditions(chip_size_m=0.025, air_fuel_ratio=1.86, moisture_content_db=0.147,
                               feed_rate_dry_kg_h=18.6)
TARGET_SPECIES = ("CO", "H2", "CO2")
TARGET_LOSS_PERCENT = 12.8
L_HEARTH = 0.22


def _solve(op, kin, n=80):
    return Reactor1D(ReactorGeometry(), FeedstockProperties(), op, kin).solve(L_HEARTH, n)


def u_wall_for_loss(op: OperatingConditions, kin: KineticConstants, target_percent: float) -> float:
    """Wall U (W/m2K) giving `target_percent` cumulative loss over the hearth."""
    f = lambda u: _solve(dataclasses.replace(op, u_wall_w_m2_k=u), kin).wall_loss_percent[-1] - target_percent
    return brentq(f, 1.0, 400.0, xtol=0.05)


def calibrate(data_dir: Path = Path("data"), iterations: int = 3):
    data = json.loads((data_dir / "calibration_run.json").read_text())
    measured = {k: v["measured"] for k, v in data["gas_composition_dry_vol_percent"].items()}
    kin = KineticConstants()
    op = CALIB_OP
    for _ in range(iterations):
        u = u_wall_for_loss(op, kin, TARGET_LOSS_PERCENT)
        op = dataclasses.replace(op, u_wall_w_m2_k=u)

        def obj(x):
            k = dataclasses.replace(kin, eta_boudouard=10 ** x[0], eta_water_gas=10 ** x[1])
            r = _solve(op, k)
            return sum((r.y_dry[s][-1] - measured[s]) ** 2 for s in TARGET_SPECIES)

        import math
        x0 = [math.log10(kin.eta_boudouard), math.log10(kin.eta_water_gas)]
        res = minimize(obj, x0, method="Nelder-Mead", options={"xatol": 1e-3, "fatol": 1e-4, "maxiter": 150})
        kin = dataclasses.replace(kin, eta_boudouard=10 ** res.x[0], eta_water_gas=10 ** res.x[1])
    return {"u_wall_w_m2_k": op.u_wall_w_m2_k, "eta_boudouard": kin.eta_boudouard,
            "eta_water_gas": kin.eta_water_gas, "sse": res.fun}


if __name__ == "__main__":
    print(calibrate())

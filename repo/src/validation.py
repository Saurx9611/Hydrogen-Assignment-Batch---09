"""
src/validation.py - Quantitative comparison of simulation results with Jayah et al. (2003).

  * Table 5 (calibration run)  - reported for completeness; it was used to CALIBRATE
                                 eta_boudouard, eta_water_gas (src/calibration.py), so
                                 agreement there is not independent evidence.
  * Table 3 (nine runs)        - independent validation of composition and gas flow.
  * Figure 5 (temperatures)    - independent validation of the axial gas temperature.

All statistics (MAE, RMSE, bias, R^2 about the 1:1 line, count within +/-10 %) are
computed here from the simulated and measured values; nothing is hard-coded.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List
import numpy as np

from src.config import ReactorGeometry, FeedstockProperties, OperatingConditions, KineticConstants
from src.reactor_1d import Reactor1D
from src.feedstock import calculate_syngas_lhv_mj_nm3

SPECIES = ["CO", "H2", "CO2", "CH4", "N2"]
FEED_RATE_KG_H = 18.6          # Table 4; per-run feed rates are not reported (assumption)
L_HEARTH = 0.22


def load_json_data(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def error_stats(measured, simulated) -> Dict[str, float]:
    m = np.asarray(measured, float)
    s = np.asarray(simulated, float)
    e = s - m
    ss_tot = float(np.sum((m - m.mean()) ** 2))
    return {
        "n": int(m.size),
        "MAE": float(np.mean(np.abs(e))),
        "RMSE": float(np.sqrt(np.mean(e ** 2))),
        "bias": float(np.mean(e)),
        "MAPE_percent": float(np.mean(np.abs(e) / m) * 100.0),
        "R2_vs_1to1": float(1.0 - np.sum(e ** 2) / ss_tot) if ss_tot > 0 else float("nan"),
        "within_10pct": int(np.sum(np.abs(e) / m <= 0.10)),
        "measured_std": float(m.std(ddof=0)),
    }


class ModelValidator:
    def __init__(self, data_dir: Path = None, kinetics: KineticConstants = None):
        self.data_dir = data_dir or Path("data")
        self.feed = FeedstockProperties()
        self.geo = ReactorGeometry()
        self.kin = kinetics or KineticConstants()

    def _run(self, op: OperatingConditions, length=L_HEARTH, n=150):
        return Reactor1D(self.geo, self.feed, op, self.kin).solve(length_m=length, num_points=n)

    # ------------------------------------------------------------------
    def validate_calibration_run(self) -> Dict[str, Any]:
        data = load_json_data(self.data_dir / "calibration_run.json")
        oc = data["operating_conditions"]
        op = OperatingConditions(chip_size_m=oc["chip_size_cm"] / 100.0, air_fuel_ratio=oc["air_fuel_ratio"],
                                 moisture_content_db=oc["moisture_content_percent_db"] / 100.0,
                                 feed_rate_dry_kg_h=FEED_RATE_KG_H)
        res = self._run(op, n=200)
        rows = []
        for sp in SPECIES:
            meas = data["gas_composition_dry_vol_percent"][sp]["measured"]
            jay = data["gas_composition_dry_vol_percent"][sp]["predicted"]
            sim = float(res.y_dry[sp][-1])
            rows.append({
                "Species": sp,
                "Measured (%)": meas,
                "Jayah model (%)": jay,
                "This model (%)": round(sim, 2),
                "Abs error (% pts)": round(sim - meas, 2),
                "Rel error (%)": round((sim - meas) / meas * 100.0, 1),
                "Jayah abs error (% pts)": round(jay - meas, 2),
            })
        st = error_stats([r["Measured (%)"] for r in rows], [r["This model (%)"] for r in rows])
        st_j = error_stats([r["Measured (%)"] for r in rows], [r["Jayah model (%)"] for r in rows])
        return {
            "dataset": "Table 5 (calibration run; used to fit eta_boudouard and eta_water_gas)",
            "conditions": oc,
            "comparison": rows,
            "MAE_percent": round(st["MAE"], 3),
            "RMSE_percent": round(st["RMSE"], 3),
            "Jayah_MAE_percent": round(st_j["MAE"], 3),
            "Jayah_RMSE_percent": round(st_j["RMSE"], 3),
            "exit_gas_T_K": round(float(res.t_gas_k[-1]), 1),
            "throat_T_K": round(float(res.t_gas_k[0]), 1),
            "throat_T_adiabatic_mixed_K": round(res.t_adiabatic_mixed_k, 1),
            "gas_flow_nm3_h": round(float(res.gas_flow_m3_h[-1]), 2),
            "cold_gas_efficiency_percent": round(float(res.cold_gas_efficiency_percent[-1]), 2),
            "char_conversion_percent": round(float(res.carbon_conversion[-1]) * 100.0, 2),
            "wall_loss_percent": round(float(res.wall_loss_percent[-1]), 2),
        }

    # ------------------------------------------------------------------
    def validate_nine_runs(self) -> Dict[str, Any]:
        runs = load_json_data(self.data_dir / "experimental_runs.json")["runs"]
        rows: List[Dict[str, Any]] = []
        for r in runs:
            op = OperatingConditions(chip_size_m=r["chip_size_cm"] / 100.0, air_fuel_ratio=r["air_fuel_ratio"],
                                     moisture_content_db=r["moisture_content_percent_db"] / 100.0,
                                     feed_rate_dry_kg_h=FEED_RATE_KG_H)
            res = self._run(op)
            meas = r["gas_analysis_dry_vol_percent"]
            row = {"Run": r["run_no"], "Chip Size (cm)": r["chip_size_cm"],
                   "MC (% db)": r["moisture_content_percent_db"], "AFR": r["air_fuel_ratio"],
                   "T_throat_K": round(float(res.t_gas_k[0]), 1), "T_exit_K": round(float(res.t_gas_k[-1]), 1)}
            for sp in SPECIES:
                row[f"{sp}_meas"] = meas[sp]
                row[f"{sp}_sim"] = round(float(res.y_dry[sp][-1]), 2)
            row["LHV_meas (MJ/Nm3)"] = round(calculate_syngas_lhv_mj_nm3({k: meas[k] / 100.0 for k in SPECIES}), 3)
            row["LHV_sim (MJ/Nm3)"] = round(calculate_syngas_lhv_mj_nm3({k: res.y_dry[k][-1] / 100.0 for k in SPECIES}), 3)
            row["Flow_meas (m3/h)"] = r["gas_flow_rate_m3_per_h"]
            row["Flow_sim (Nm3/h dry)"] = round(float(res.gas_flow_m3_h[-1]), 2)
            row["Implied feed (kg/h)"] = round(FEED_RATE_KG_H * r["gas_flow_rate_m3_per_h"] / float(res.gas_flow_m3_h[-1]), 1)
            row["CGE_sim (%)"] = round(float(res.cold_gas_efficiency_percent[-1]), 2)
            rows.append(row)

        stats_all, stats_indep = {}, {}
        for key in SPECIES + ["LHV"]:
            mk, sk = (f"{key}_meas", f"{key}_sim") if key != "LHV" else ("LHV_meas (MJ/Nm3)", "LHV_sim (MJ/Nm3)")
            stats_all[key] = error_stats([x[mk] for x in rows], [x[sk] for x in rows])
            sub = [x for x in rows if x["Run"] != 7]
            stats_indep[key] = error_stats([x[mk] for x in sub], [x[sk] for x in sub])
        return {
            "dataset": "Table 3 (nine experimental runs)",
            "feed_rate_assumed_kg_h": FEED_RATE_KG_H,
            "runs_table": rows,
            "statistical_summary": stats_all,
            "statistical_summary_excl_run7": stats_indep,
        }

    # ------------------------------------------------------------------
    def validate_temperature_profile(self) -> Dict[str, Any]:
        data = load_json_data(self.data_dir / "temperature_profile_fig5.json")
        pts = data["measured_experimental_points"]
        jay = data["jayah_model_curve_digitised"]
        op = OperatingConditions(chip_size_m=0.025, air_fuel_ratio=data["air_fuel_ratio"],
                                 moisture_content_db=0.147, feed_rate_dry_kg_h=FEED_RATE_KG_H)
        res = self._run(op, length=0.25, n=251)
        jz = np.array([p["z_cm"] for p in jay]); jt = np.array([p["T_K"] for p in jay])
        rows = []
        for p in pts:
            t_sim = float(np.interp(p["z_cm"] / 100.0, res.z_m, res.t_gas_k))
            t_j = float(np.interp(p["z_cm"], jz, jt))
            rows.append({"z_cm": p["z_cm"], "T_meas_K": p["T_K"], "T_sim_K": round(t_sim, 1),
                         "Error_K": round(t_sim - p["T_K"], 1), "T_Jayah_model_K": round(t_j, 1),
                         "Jayah_error_K": round(t_j - p["T_K"], 1)})
        st = error_stats([r["T_meas_K"] for r in rows], [r["T_sim_K"] for r in rows])
        st_j = error_stats([r["T_meas_K"] for r in rows], [r["T_Jayah_model_K"] for r in rows])
        return {"dataset": "Figure 5 (axial gas temperature, AFR 2.20)", "comparison": rows,
                "MAE_K": round(st["MAE"], 1), "RMSE_K": round(st["RMSE"], 1), "bias_K": round(st["bias"], 1),
                "Jayah_MAE_K": round(st_j["MAE"], 1), "Jayah_RMSE_K": round(st_j["RMSE"], 1),
                "profile": {"z_cm": (res.z_m * 100).tolist(), "T_g": res.t_gas_k.tolist(), "T_s": res.t_solid_k.tolist()}}

    # ------------------------------------------------------------------
    def export_all_tables(self, output_dir: Path = None) -> Dict[str, Any]:
        out = output_dir or Path("outputs/tables")
        out.mkdir(parents=True, exist_ok=True)

        def to_csv(path, rows):
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)

        calib = self.validate_calibration_run()
        runs = self.validate_nine_runs()
        temp = self.validate_temperature_profile()
        to_csv(out / "table5_calibration_validation.csv", calib["comparison"])
        to_csv(out / "table3_nine_runs_validation.csv", runs["runs_table"])
        to_csv(out / "fig5_temperature_validation.csv", temp["comparison"])
        temp_json = {k: v for k, v in temp.items() if k != "profile"}
        with open(out / "validation_summary.json", "w", encoding="utf-8") as f:
            json.dump({"table5_calibration": calib, "table3_nine_runs": runs, "fig5_temperature": temp_json}, f, indent=2)
        return {"calib": calib, "runs": runs, "temp": temp}

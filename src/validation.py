"""
src/validation.py - Quantitative validation engine comparing simulation outputs
against experimental measurements and benchmark data from Jayah et al. (2003).
Calculates MAE, RMSE, and MAPE across all 9 runs, the calibration run, and temperature data.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

from src.config import (
    ReactorGeometry,
    FeedstockProperties,
    OperatingConditions,
    KineticConstants,
)
from src.reactor_1d import Reactor1D, SimulationResults1D


def load_json_data(file_path: Path) -> Dict[str, Any]:
    """Helper to safely load JSON files."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


class ModelValidator:
    """Performs validation checks against Jayah et al. (2003) datasets."""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("data")
        self.feedstock = FeedstockProperties()
        self.geometry = ReactorGeometry()
        self.kinetics = KineticConstants()

    def validate_calibration_run(self) -> Dict[str, Any]:
        """
        Validate against Table 5 (p. 465):
        Run 7 calibration with 2.5 cm chips, AFR = 2.20, MC = 14.7% d.b.
        """
        calib_file = self.data_dir / "calibration_run.json"
        data = load_json_data(calib_file)

        # Set operating conditions for calibration run
        op = OperatingConditions(
            chip_size_m=0.025,
            air_fuel_ratio=2.20,
            moisture_content_db=0.147,
            feed_rate_dry_kg_h=18.6,
        )

        reactor = Reactor1D(self.geometry, self.feedstock, op, self.kinetics)
        res = reactor.solve(length_m=0.22, num_points=200)

        # Terminal gas composition at z = 22 cm
        predicted = {
            "CO": float(res.y_dry["CO"][-1]),
            "H2": float(res.y_dry["H2"][-1]),
            "CO2": float(res.y_dry["CO2"][-1]),
            "CH4": float(res.y_dry["CH4"][-1]),
            "N2": float(res.y_dry["N2"][-1]),
        }

        measured = {
            k: data["gas_composition_dry_vol_percent"][k]["measured"]
            for k in ["CO", "H2", "CO2", "CH4", "N2"]
        }
        paper_predicted = {
            k: data["gas_composition_dry_vol_percent"][k]["predicted"]
            for k in ["CO", "H2", "CO2", "CH4", "N2"]
        }

        comparison = []
        for sp in ["CO", "H2", "CO2", "CH4", "N2"]:
            pred_val = predicted[sp]
            meas_val = measured[sp]
            err = pred_val - meas_val
            pct_err = (err / meas_val) * 100.0
            comparison.append({
                "Species": sp,
                "Measured (%)": meas_val,
                "Paper Predicted (%)": paper_predicted[sp],
                "Our Simulation (%)": round(pred_val, 2),
                "Abs Error (%)": round(err, 2),
                "Rel Error (%)": round(pct_err, 2),
            })

        mae = float(np.mean([abs(c["Abs Error (%)"]) for c in comparison]))
        rmse = float(np.sqrt(np.mean([(c["Abs Error (%)"]) ** 2 for c in comparison])))

        return {
            "dataset": "Table 5 (2.5 cm chips calibration)",
            "comparison": comparison,
            "MAE_percent": round(mae, 3),
            "RMSE_percent": round(rmse, 3),
            "terminal_gas_flow_m3_h": round(float(res.gas_flow_m3_h[-1]), 2),
            "terminal_efficiency_percent": round(float(res.cold_gas_efficiency_percent[-1]), 2),
        }

    def validate_nine_runs(self) -> Dict[str, Any]:
        """
        Validate against Table 3 (p. 464):
        Nine multi-condition experimental runs across varied chip sizes, moisture, and AFR.
        """
        runs_file = self.data_dir / "experimental_runs.json"
        data = load_json_data(runs_file)
        runs = data["runs"]

        results = []
        errors_by_species = {"CO": [], "H2": [], "CO2": [], "CH4": [], "N2": []}

        for r in runs:
            run_no = r["run_no"]
            chip_size_m = r["chip_size_cm"] / 100.0
            mc_db = r["moisture_content_percent_db"] / 100.0
            afr = r["air_fuel_ratio"]
            meas_gas = r["gas_analysis_dry_vol_percent"]
            meas_flow = r["gas_flow_rate_m3_per_h"]

            # Configure and run simulation for this specific trial
            op = OperatingConditions(
                chip_size_m=chip_size_m,
                air_fuel_ratio=afr,
                moisture_content_db=mc_db,
                feed_rate_dry_kg_h=18.6,
            )

            reactor = Reactor1D(self.geometry, self.feedstock, op, self.kinetics)
            sim_res = reactor.solve(length_m=0.22, num_points=150)

            sim_co = float(sim_res.y_dry["CO"][-1])
            sim_h2 = float(sim_res.y_dry["H2"][-1])
            sim_co2 = float(sim_res.y_dry["CO2"][-1])
            sim_ch4 = float(sim_res.y_dry["CH4"][-1])
            sim_n2 = float(sim_res.y_dry["N2"][-1])
            sim_flow = float(sim_res.gas_flow_m3_h[-1])

            # Record errors
            for sp, val in [("CO", sim_co), ("H2", sim_h2), ("CO2", sim_co2), ("CH4", sim_ch4), ("N2", sim_n2)]:
                errors_by_species[sp].append(val - meas_gas[sp])

            results.append({
                "Run": run_no,
                "Chip Size (cm)": r["chip_size_cm"],
                "MC (% db)": r["moisture_content_percent_db"],
                "AFR": afr,
                "CO_meas": meas_gas["CO"],
                "CO_sim": round(sim_co, 2),
                "H2_meas": meas_gas["H2"],
                "H2_sim": round(sim_h2, 2),
                "CO2_meas": meas_gas["CO2"],
                "CO2_sim": round(sim_co2, 2),
                "CH4_meas": meas_gas["CH4"],
                "CH4_sim": round(sim_ch4, 2),
                "N2_meas": meas_gas["N2"],
                "N2_sim": round(sim_n2, 2),
                "Flow_meas (m3/h)": meas_flow,
                "Flow_sim (m3/h)": round(sim_flow, 2),
            })

        # Calculate summary statistical metrics
        summary_stats = {}
        for sp in errors_by_species:
            errs = np.array(errors_by_species[sp])
            summary_stats[sp] = {
                "MAE": round(float(np.mean(np.abs(errs))), 3),
                "RMSE": round(float(np.sqrt(np.mean(errs ** 2))), 3),
            }

        return {
            "dataset": "Table 3 (9 Experimental Runs)",
            "runs_table": results,
            "statistical_summary": summary_stats,
        }

    def validate_temperature_profile(self) -> Dict[str, Any]:
        """
        Validate axial gasification temperature against Fig. 5 digitized points.
        """
        temp_file = self.data_dir / "temperature_profile_fig5.json"
        data = load_json_data(temp_file)
        meas_points = data["measured_experimental_points"]

        op = OperatingConditions(
            chip_size_m=0.025,
            air_fuel_ratio=2.20,
            moisture_content_db=0.147,
        )
        reactor = Reactor1D(self.geometry, self.feedstock, op, self.kinetics)
        res = reactor.solve(length_m=0.25, num_points=250)

        comparison = []
        for pt in meas_points:
            z_m = pt["z_cm"] / 100.0
            t_meas = pt["T_K"]
            # Interpolate simulated T_g at this z
            t_sim = float(np.interp(z_m, res.z_m, res.t_gas_k))
            err = t_sim - t_meas
            comparison.append({
                "z_cm": pt["z_cm"],
                "T_meas_K": t_meas,
                "T_sim_K": round(t_sim, 1),
                "Abs_Error_K": round(err, 1),
                "Rel_Error_pct": round((err / t_meas) * 100.0, 2),
            })

        mae_k = float(np.mean([abs(c["Abs_Error_K"]) for c in comparison]))
        rmse_k = float(np.sqrt(np.mean([(c["Abs_Error_K"]) ** 2 for c in comparison])))

        return {
            "dataset": "Figure 5 (Axial Temperature Profile)",
            "comparison": comparison,
            "MAE_K": round(mae_k, 1),
            "RMSE_K": round(rmse_k, 1),
        }

    def export_all_tables(self, output_dir: Path = None) -> None:
        """Export all validation tables to CSV and JSON in outputs/tables/."""
        out_dir = output_dir or Path("outputs/tables")
        out_dir.mkdir(parents=True, exist_ok=True)

        def write_dict_list_to_csv(filepath: Path, rows: List[Dict[str, Any]]) -> None:
            if not rows:
                return
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

        # 1. Calibration run
        calib_res = self.validate_calibration_run()
        write_dict_list_to_csv(out_dir / "table5_calibration_validation.csv", calib_res["comparison"])

        # 2. Nine runs
        runs_res = self.validate_nine_runs()
        write_dict_list_to_csv(out_dir / "table3_nine_runs_validation.csv", runs_res["runs_table"])

        # 3. Temperature profile
        temp_res = self.validate_temperature_profile()
        write_dict_list_to_csv(out_dir / "fig5_temperature_validation.csv", temp_res["comparison"])

        # 4. Save combined JSON report
        combined_report = {
            "table5_calibration": calib_res,
            "table3_nine_runs": runs_res,
            "fig5_temperature": temp_res,
        }
        with open(out_dir / "validation_summary.json", "w", encoding="utf-8") as f:
            json.dump(combined_report, f, indent=2)

"""
run_simulation.py - End-to-end pipeline (Batch 09):
calibration check -> 1D reference/calibration cases -> 2D model -> validation ->
parametric study (Jayah Table 7) -> balances -> figures -> outputs/tables/key_results.json

    python run_simulation.py               # use calibrated values in src/config.py
    python run_simulation.py --recalibrate # re-fit U_wall, eta_boudouard, eta_water_gas first
"""

import csv
import dataclasses
import json
import sys
import time
from pathlib import Path
import numpy as np

from src.config import ReactorGeometry, FeedstockProperties, OperatingConditions, KineticConstants
from src.feedstock import BiomassAnalysis, calculate_syngas_lhv_mj_nm3
from src.reactor_1d import Reactor1D
from src.reactor_2d import Reactor2D
from src.validation import ModelValidator, load_json_data
from src.sensitivity import run_table7_study, run_operating_sweeps
from src.balances import closure
from src import plots

OUT_FIG = Path("outputs/figures")
OUT_TAB = Path("outputs/tables")

# Reference case for profiles/contours = Jayah Fig. 5 conditions (the case with temperature data)
REF_OP = OperatingConditions(chip_size_m=0.025, air_fuel_ratio=2.20, moisture_content_db=0.147, feed_rate_dry_kg_h=18.6)


def _f(x, nd=3):
    return float(round(float(x), nd))


def stoich_air_kg_per_kg(feed: FeedstockProperties) -> float:
    o2 = feed.c_percent / 12.011 + feed.h_percent / 4.032 - feed.o_percent / 31.998   # mol O2 / 100 g
    return o2 / 0.21 * 0.02897 * 1000.0 / 100.0


def main():
    t0 = time.time()
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    OUT_TAB.mkdir(parents=True, exist_ok=True)
    geo, feed, kin = ReactorGeometry(), FeedstockProperties(), KineticConstants()

    if "--recalibrate" in sys.argv:
        from src.calibration import calibrate
        print("[0] Re-calibrating against Table 5 + 12.8 % heat loss ...")
        cal = calibrate()
        print("    ", cal, "\n    -> copy these into src/config.py and re-run")
        return

    print("[1] 1D model: reference case (Fig. 5 conditions) and calibration case (Table 5 / Run 7)")
    ref = Reactor1D(geo, feed, REF_OP, kin)
    res_ref = ref.solve(0.22, 221)
    res_ref_ext = ref.solve(0.26, 261)
    print(f"    reference: T_throat {res_ref.t_gas_k[0]:.0f} K (mixed adiabatic {res_ref.t_adiabatic_mixed_k:.0f} K), "
          f"T_exit {res_ref.t_gas_k[-1]:.0f} K, CO {res_ref.y_dry['CO'][-1]:.2f} %, CGE {res_ref.cold_gas_efficiency_percent[-1]:.1f} %")

    print("[2] 2D axisymmetric model (reference case)")
    res2d = Reactor2D(geo, feed, REF_OP, kin, n_cells=12, n_z=111).solve(0.22)
    j = -1
    print(f"    exit axis {res2d.t_gas_2d[0, j]:.0f} K, wall cell {res2d.t_gas_2d[-1, j]:.0f} K, mixed {res2d.mixed_t_exit_k:.0f} K")

    print("[3] Validation against Jayah et al. (2003)")
    val = ModelValidator(kinetics=kin).export_all_tables(OUT_TAB)
    calib, runs, temp = val["calib"], val["runs"], val["temp"]
    print(f"    Table 5: MAE {calib['MAE_percent']:.2f} % pts (Jayah model {calib['Jayah_MAE_percent']:.2f})")
    for sp, s in runs["statistical_summary"].items():
        print(f"    Table 3 {sp:4s}: MAE {s['MAE']:.2f}  RMSE {s['RMSE']:.2f}  bias {s['bias']:+.2f}  R2 {s['R2_vs_1to1']:.2f}  within10 {s['within_10pct']}/9")
    print(f"    Fig. 5: MAE {temp['MAE_K']:.0f} K (Jayah model {temp['Jayah_MAE_K']:.0f} K)")

    print("[4] Parametric study (Jayah Table 7) and operating sweeps")
    study = run_table7_study()
    sweeps = run_operating_sweeps()
    bench = load_json_data(Path("data/parametric_benchmarks.json"))["parameters"]
    with open(OUT_TAB / "table7_replication.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Parameter", "Value", "Eff_22cm_model", "Eff_22cm_Jayah", "Opt_length_model_cm", "Opt_length_Jayah_cm",
                    "Eff_opt_model", "Eff_opt_Jayah", "Wall_loss_22cm_pct", "U_wall_W_m2K"])
        for key, *_ in plots.TABLE7_PANELS:
            b = bench.get(key, {})
            for i, s in enumerate(study[key]["summary"]):
                def bget(name):
                    v = b.get(name)
                    return v[i] if v and i < len(v) else ""
                w.writerow([key, s["value"], _f(s["eff_22cm"], 2), bget("efficiency_at_22cm_percent"),
                            _f(s["optimum_length_cm"], 1), bget("optimum_length_cm"), _f(s["eff_at_optimum"], 2),
                            bget("efficiency_at_optimum_length_percent"), _f(s["wall_loss_22cm_percent"], 2), _f(s["u_wall"], 1)])
    with open(OUT_TAB / "operating_sweeps.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        keys = ["value", "t_throat", "t_exit", "CO", "H2", "CO2", "lhv", "cge", "flow", "xc"]
        w.writerow(["sweep"] + keys)
        for name in ("afr", "feed"):
            for s in sweeps[name]:
                w.writerow([name] + [_f(s[k], 3) for k in keys])

    print("[5] WGS-rate sensitivity and conservation checks")
    cal_op = OperatingConditions(chip_size_m=0.025, air_fuel_ratio=1.86, moisture_content_db=0.147, feed_rate_dry_kg_h=18.6)
    r_cal = Reactor1D(geo, feed, cal_op, kin).solve(0.22, 200)
    r_fast = Reactor1D(geo, feed, cal_op, dataclasses.replace(kin, a_wgs=2.78e3)).solve(0.22, 200)
    bal = closure(res_ref)
    with open(OUT_TAB / "elemental_energy_balances.json", "w", encoding="utf-8") as f:
        json.dump(bal, f, indent=2, default=float)

    print("[6] Figures")
    ba = BiomassAnalysis(feed, REF_OP.moisture_content_db)
    a, bta, g, _ = ba.molar_formula_daf
    derived = {"lhv": ba.lhv_dry_mj_kg, "afr_stoich": stoich_air_kg_per_kg(feed), "formula": f"CH{a:.2f}O{bta:.2f}N{g:.4f}"}
    fig5 = load_json_data(Path("data/temperature_profile_fig5.json"))
    plots.plot_geometry(OUT_FIG / "fig00_geometry.png")
    plots.plot_feedstock_composition(OUT_FIG / "fig01_feedstock_composition.png", OUT_TAB / "feedstock_properties.csv", derived)
    plots.plot_species_distributions_1d(res_ref_ext, OUT_FIG / "fig02_species_distributions_1d.png")
    plots.plot_temperature_profiles_1d(Reactor1D(geo, feed, REF_OP, kin).solve(0.25, 251), fig5["measured_experimental_points"],
                                       fig5["jayah_model_curve_digitised"], OUT_FIG / "fig03_temperature_profiles_1d.png")
    plots.plot_char_conversion_and_shrinkage(res_ref_ext, OUT_FIG / "fig04_char_conversion_and_shrinkage.png")
    plots.plot_2d_temperature_contours(res2d, OUT_FIG / "fig05_temperature_contours_2d.png")
    plots.plot_2d_species_fuel_contours(res2d, OUT_FIG / "fig06_species_contours_fuel_2d.png")
    plots.plot_2d_species_oxidant_contours(res2d, OUT_FIG / "fig07_species_contours_oxidants_2d.png")
    plots.plot_table7_replication(study, bench, OUT_FIG / "fig08_table7_replication.png")
    plots.plot_validation_parity(runs["runs_table"], runs["statistical_summary"], OUT_FIG / "fig09_validation_parity_plots.png")
    plots.plot_principal_cases_comparison(runs["runs_table"], OUT_FIG / "fig10_principal_cases_comparison.png")
    plots.plot_operating_sweeps(sweeps, OUT_FIG / "fig11_operating_sweeps.png")
    plots.plot_radial_profiles(res2d, res_ref, OUT_FIG / "fig12_radial_profiles_2d.png")

    # ---------------------------------------------------------------- key results
    def zfind(arr, z_cm, res):
        return float(np.interp(z_cm / 100.0, res.z_m, arr))

    def first_z(res, frac):
        x = res.carbon_conversion
        return float(np.interp(frac * x[-1], x, res.z_m * 100)) if x[-1] > 0 else None

    k2 = {}
    for zc in (5.0, 11.0, 22.0):
        jj = int(np.argmin(np.abs(res2d.z_1d * 100 - zc)))
        k2[f"z{zc:.0f}"] = {"T_axis": _f(res2d.t_gas_2d[0, jj], 1), "T_wall_cell": _f(res2d.t_gas_2d[-2, jj], 1),
                            "CO_axis": _f(res2d.y_co_2d[0, jj], 2), "CO_wall_cell": _f(res2d.y_co_2d[-2, jj], 2),
                            "H2_axis": _f(res2d.y_h2_2d[0, jj], 2), "H2_wall_cell": _f(res2d.y_h2_2d[-2, jj], 2),
                            "Xc_axis": _f(res2d.x_c_2d[0, jj] * 100, 1), "Xc_wall_cell": _f(res2d.x_c_2d[-2, jj] * 100, 1)}
    from src.thermo import enthalpy_sensible
    gas_attrs = (("CO", "f_co"), ("H2", "f_h2"), ("CO2", "f_co2"), ("H2O", "f_h2o"), ("CH4", "f_ch4"), ("N2", "f_n2"))

    def sens_h(i):
        return (sum(getattr(res_ref, a)[i] * enthalpy_sensible(q, res_ref.t_gas_k[i]) for q, a in gas_attrs)
                + res_ref.f_c_solid[i] * enthalpy_sensible("C", res_ref.t_solid_k[i]))
    sens_drop = sens_h(0) - sens_h(-1)

    key = {
        "parameters": {"u_wall_w_m2_k": REF_OP.u_wall_w_m2_k, "eta_boudouard": kin.eta_boudouard, "eta_water_gas": kin.eta_water_gas,
                       "a_wgs": kin.a_wgs, "bed_void_fraction": REF_OP.bed_void_fraction, "throat_t_anchor_k": REF_OP.throat_t_anchor_k},
        "feedstock_derived": {k: (v if isinstance(v, str) else _f(v, 3)) for k, v in derived.items()},
        "reference_case_1d": {
            "conditions": dataclasses.asdict(REF_OP),
            "T_throat_K": _f(res_ref.t_gas_k[0], 1), "T_adiabatic_mixed_K": _f(res_ref.t_adiabatic_mixed_k, 1),
            "T_s0_K": _f(res_ref.t_solid_k[0], 1), "T_exit_K": _f(res_ref.t_gas_k[-1], 1), "Ts_exit_K": _f(res_ref.t_solid_k[-1], 1),
            "T_at": {f"z{z}": _f(zfind(res_ref_ext.t_gas_k, z, res_ref_ext), 1) for z in (2, 5, 10, 15, 22, 26)},
            "dTgs_max_K": _f(np.max(res_ref.t_gas_k - res_ref.t_solid_k), 1),
            "z_dTgs_below_10K_cm": _f(res_ref.z_m[np.argmax(np.abs(res_ref.t_gas_k - res_ref.t_solid_k) < 10)] * 100, 2),
            "exit_dry": {k: _f(v[-1], 2) for k, v in res_ref.y_dry.items()},
            "throat_dry": {k: _f(v[0], 2) for k, v in res_ref.y_dry.items()},
            "h2o_wet_in": _f(100 * res_ref.f_h2o[0] / (res_ref.f_h2o[0] + res_ref.gas_flow_m3_h[0] / 80.6904), 2),
            "h2o_wet_out": _f(100 * res_ref.f_h2o[-1] / (res_ref.f_h2o[-1] + res_ref.gas_flow_m3_h[-1] / 80.6904), 2),
            "Xc_exit_percent": _f(res_ref.carbon_conversion[-1] * 100, 2),
            "z_half_conversion_cm": _f(first_z(res_ref, 0.5), 2),
            "dp_exit_cm": _f(res_ref.d_p_m[-1] * 100, 3),
            "gas_flow_nm3_h": _f(res_ref.gas_flow_m3_h[-1], 2),
            "LHV_MJ_Nm3": _f(calculate_syngas_lhv_mj_nm3({k: v[-1] / 100 for k, v in res_ref.y_dry.items()}), 3),
            "CGE_percent": _f(res_ref.cold_gas_efficiency_percent[-1], 2),
            "wall_loss_kW": _f(res_ref.wall_loss_cum_w[-1] / 1e3, 2), "wall_loss_percent": _f(res_ref.wall_loss_percent[-1], 2),
            "energy_input_kW": _f(res_ref.energy_input_w / 1e3, 2),
            "sensible_drop_kW": _f(sens_drop / 1e3, 2),
            "wall_share_of_sensible_drop_percent": _f(100 * res_ref.wall_loss_cum_w[-1] / sens_drop, 1),
        },
        "base_case_T_at_12cm_K": _f(np.interp(0.12, study["chip_size_cm"]["curves"][3.0].z_m,
                                              study["chip_size_cm"]["curves"][3.0].t_gas_k), 0),
        "two_d": {"n_cells": res2d.n_cells, "n_z": len(res2d.z_1d), "stations": k2,
                  "mixed_exit_dry": {k: _f(v, 2) for k, v in res2d.mixed_dry_exit.items()},
                  "mixed_T_exit_K": _f(res2d.mixed_t_exit_k, 1), "wall_loss_kW": _f(res2d.wall_loss_w / 1e3, 2)},
        "calibration": {k: v for k, v in calib.items() if k != "comparison"} | {"rows": calib["comparison"]},
        "nine_runs": {"stats": runs["statistical_summary"], "stats_excl_run7": runs["statistical_summary_excl_run7"]},
        "fig5": {k: v for k, v in temp.items() if k != "profile"},
        "wgs_sensitivity_calibration_case": {
            "slow_wgs_a=2.78e-3": {k: _f(v[-1], 2) for k, v in r_cal.y_dry.items()},
            "fast_wgs_a=2.78e3": {k: _f(v[-1], 2) for k, v in r_fast.y_dry.items()},
        },
        "table7": {k: [{q: (_f(v, 2) if isinstance(v, (int, float)) else v) for q, v in s.items()} for s in study[k]["summary"]]
                   for k, *_ in plots.TABLE7_PANELS},
        "sweeps": {k: [{q: _f(v, 3) for q, v in s.items()} for s in sweeps[k]] for k in sweeps},
        "balances": json.loads(json.dumps(bal, default=float)),
        "runtime_s": None,
    }
    key["runtime_s"] = _f(time.time() - t0, 1)
    with open(OUT_TAB / "key_results.json", "w", encoding="utf-8") as f:
        json.dump(key, f, indent=2, default=float)
    print(f"Done in {time.time() - t0:.1f} s -> {OUT_FIG}, {OUT_TAB}")


if __name__ == "__main__":
    main()

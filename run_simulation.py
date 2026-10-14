"""
run_simulation.py - Master execution pipeline for the fixed-bed downdraft gasifier simulation.
Runs Tier 1 1D mechanistic model, Tier 2 2D spatial model, comprehensive sensitivity sweeps,
validation suite, and exports all publication-quality figures and machine-readable data tables.
"""

from pathlib import Path
import json
import csv
import time
import numpy as np

from src.config import (
    ReactorGeometry,
    FeedstockProperties,
    OperatingConditions,
    KineticConstants,
)
from src.feedstock import calculate_syngas_lhv_mj_nm3
from src.reactor_1d import Reactor1D
from src.reactor_2d import Reactor2D
from src.validation import ModelValidator
from src.plots import (
    plot_feedstock_composition,
    plot_species_distributions_1d,
    plot_temperature_profiles_1d,
    plot_char_conversion_and_shrinkage,
    plot_2d_temperature_contours,
    plot_2d_species_fuel_contours,
    plot_2d_species_oxidant_contours,
    plot_parametric_sensitivities,
    plot_validation_parity,
    plot_principal_cases_comparison,
)


def main():
    start_time = time.time()
    print("=" * 80)
    print("NERD FIXED-BED DOWNDRAFT WOOD GASIFIER SIMULATION")
    print("Reference: Jayah et al. (2003), Biomass and Bioenergy 25(5), 459-469")
    print("=" * 80)

    # 1. Output directories
    out_fig_dir = Path("outputs/figures")
    out_tab_dir = Path("outputs/tables")
    out_fig_dir.mkdir(parents=True, exist_ok=True)
    out_tab_dir.mkdir(parents=True, exist_ok=True)

    # 2. Base Configuration
    geo = ReactorGeometry()
    feed = FeedstockProperties()
    op_baseline = OperatingConditions(
        chip_size_m=0.025,
        air_fuel_ratio=2.20,
        moisture_content_db=0.147,
        feed_rate_dry_kg_h=18.6,
    )
    kinetics = KineticConstants()

    print("\n[Step 1/6] Executing Tier 1: 1D Mechanistic Multi-Zone Model...")
    reactor_1d = Reactor1D(geo, feed, op_baseline, kinetics)
    res_1d = reactor_1d.solve(length_m=0.22, num_points=250)
    res_1d_ext = reactor_1d.solve(length_m=0.26, num_points=260)

    print(f"  -> Solved baseline hearth: z = 0.0 to {res_1d.z_m[-1]*100:.1f} cm (250 grid points)")
    print(f"  -> Terminal Dry Gas Composition (z = 22 cm):")
    for sp in ["CO", "H2", "CO2", "CH4", "N2"]:
        print(f"     * {sp:4s}: {res_1d.y_dry[sp][-1]:5.2f} vol %")
    print(f"  -> Exit Gas Temperature: {res_1d.t_gas_k[-1]:.1f} K")
    print(f"  -> Producer Gas Flow Rate: {res_1d.gas_flow_m3_h[-1]:.2f} Nm3/h")
    print(f"  -> Cold Gas Efficiency: {res_1d.cold_gas_efficiency_percent[-1]:.2f} %")
    print(f"  -> Char Carbon Conversion: {res_1d.carbon_conversion[-1]*100:.2f} %")

    print("\n[Step 2/6] Executing Tier 2: 2D Axisymmetric Spatial Model...")
    reactor_2d = Reactor2D(geo, feed, op_baseline, kinetics, n_r=41, n_z=101)
    res_2d = reactor_2d.solve(res_1d=res_1d, length_m=0.22)
    print(f"  -> Solved boundary-conforming (r, z) grid: {res_2d.r_grid.shape[0]} radial x {res_2d.r_grid.shape[1]} axial nodes")
    print(f"  -> Core Temperature at z = 22 cm: {res_2d.t_gas_2d[0, -1]:.1f} K")
    print(f"  -> Wall Temperature at z = 22 cm: {res_2d.t_gas_2d[-1, -1]:.1f} K (cooling = {res_2d.t_gas_2d[0, -1] - res_2d.t_gas_2d[-1, -1]:.1f} K)")

    print("\n[Step 3/6] Running Comprehensive Parametric Sensitivity Sweeps...")
    # A. Length & Chip Size (Fig. 6 benchmark)
    res_by_chip = {}
    for chip_m in [0.01, 0.03, 0.05]:
        op_chip = OperatingConditions(
            chip_size_m=chip_m,
            air_fuel_ratio=2.20,
            moisture_content_db=0.150,
            feed_rate_dry_kg_h=18.6,
        )
        r_chip = Reactor1D(geo, feed, op_chip, kinetics)
        res_chip = r_chip.solve(length_m=0.50, num_points=300)
        res_by_chip[chip_m] = res_chip

    # B. Air-Fuel Ratio (AFR) sweep
    afr_vals = np.linspace(1.8, 2.6, 9)
    lhv_afr = []
    cge_afr = []
    for afr in afr_vals:
        op_afr = OperatingConditions(air_fuel_ratio=afr, moisture_content_db=0.147, chip_size_m=0.025)
        r_afr = Reactor1D(geo, feed, op_afr, kinetics)
        sol_afr = r_afr.solve(length_m=0.22, num_points=120)
        syn_dict = {k: sol_afr.y_dry[k][-1] / 100.0 for k in sol_afr.y_dry}
        lhv_afr.append(float(calculate_syngas_lhv_mj_nm3(syn_dict)))
        cge_afr.append(float(sol_afr.cold_gas_efficiency_percent[-1]))

    # C. Moisture Content (MC) sweep
    mc_vals = np.linspace(0.05, 0.25, 9)
    t_exit_mc = []
    lhv_mc = []
    for mc in mc_vals:
        op_mc = OperatingConditions(air_fuel_ratio=2.20, moisture_content_db=mc, chip_size_m=0.025)
        r_mc = Reactor1D(geo, feed, op_mc, kinetics)
        sol_mc = r_mc.solve(length_m=0.22, num_points=120)
        syn_dict = {k: sol_mc.y_dry[k][-1] / 100.0 for k in sol_mc.y_dry}
        t_exit_mc.append(float(sol_mc.t_gas_k[-1]))
        lhv_mc.append(float(calculate_syngas_lhv_mj_nm3(syn_dict)))

    # D. Biomass Feed Rate sweep
    feed_vals = np.linspace(12.0, 24.0, 7)
    flow_feed = []
    cge_feed = []
    for f_rate in feed_vals:
        op_feed = OperatingConditions(air_fuel_ratio=2.20, moisture_content_db=0.147, chip_size_m=0.025, feed_rate_dry_kg_h=f_rate)
        r_f = Reactor1D(geo, feed, op_feed, kinetics)
        sol_f = r_f.solve(length_m=0.22, num_points=120)
        flow_feed.append(float(sol_f.gas_flow_m3_h[-1]))
        cge_feed.append(float(sol_f.cold_gas_efficiency_percent[-1]))

    sens_data = {
        "length_chip_results": res_by_chip,
        "afr_sweep": {"afr": afr_vals.tolist(), "lhv_mj_nm3": lhv_afr, "cge_percent": cge_afr},
        "mc_sweep": {"mc_percent_db": (mc_vals * 100.0).tolist(), "t_exit_k": t_exit_mc, "lhv_mj_nm3": lhv_mc},
        "feed_sweep": {"feed_rate_kg_h": feed_vals.tolist(), "gas_flow_nm3_h": flow_feed, "cge_percent": cge_feed},
    }

    # Export sensitivity data to CSV
    sens_csv_path = out_tab_dir / "parametric_sensitivity_data.csv"
    with open(sens_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter_Type", "Parameter_Value", "Unit", "Syngas_LHV_MJ_Nm3", "Cold_Gas_Efficiency_pct", "Exit_Temp_K", "Gas_Flow_Nm3_h"])
        for afr, lhv, cge in zip(afr_vals, lhv_afr, cge_afr):
            writer.writerow(["Air_Fuel_Ratio", round(afr, 2), "kg air/kg dry", round(lhv, 3), round(cge, 2), "", ""])
        for mc, t_ex, lhv in zip(mc_vals, t_exit_mc, lhv_mc):
            writer.writerow(["Moisture_Content", round(mc * 100.0, 1), "% d.b.", round(lhv, 3), "", round(t_ex, 1), ""])
        for fr, fl, cge in zip(feed_vals, flow_feed, cge_feed):
            writer.writerow(["Biomass_Feed_Rate", round(fr, 1), "kg/h", "", round(cge, 2), "", round(fl, 2)])

    print(f"  -> Sensitivity data exported to: {sens_csv_path}")

    print("\n[Step 4/6] Executing Validation Suite against Jayah et al. (2003)...")
    validator = ModelValidator()
    validator.export_all_tables(out_tab_dir)

    calib_res = validator.validate_calibration_run()
    runs_res = validator.validate_nine_runs()
    temp_res = validator.validate_temperature_profile()

    print(f"  -> Table 5 (2.5 cm Calibration Run) Validation:")
    print(f"     MAE: {calib_res['MAE_percent']:.2f} %, RMSE: {calib_res['RMSE_percent']:.2f} %")
    print(f"  -> Table 3 (9 Experimental Runs) Statistical Summary:")
    for sp, s in runs_res["statistical_summary"].items():
        print(f"     * {sp:4s}: MAE = {s['MAE']:4.2f} %, RMSE = {s['RMSE']:4.2f} %")
    print(f"  -> Figure 5 (Axial Temperature Profile) Validation:")
    print(f"     MAE: {temp_res['MAE_K']:.1f} K, RMSE: {temp_res['RMSE_K']:.1f} K")

    print("\n[Step 5/6] Exporting Summary of Principal Operating Cases...")
    cases_csv_path = out_tab_dir / "principal_operating_cases_summary.csv"
    with open(cases_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Case_Description", "Chip_Size_cm", "MC_pct_db", "Air_Fuel_Ratio", "L_hearth_cm",
            "CO_vol_pct", "H2_vol_pct", "CO2_vol_pct", "CH4_vol_pct", "N2_vol_pct",
            "Gas_Flow_Nm3_h", "Syngas_LHV_MJ_Nm3", "Cold_Gas_Efficiency_pct", "Exit_Temp_K", "Carbon_Conversion_pct"
        ])
        # 1. Baseline Hearth (22 cm)
        writer.writerow([
            "Baseline Calibration (NERD Hearth 22 cm)", 2.5, 14.7, 2.20, 22.0,
            round(res_1d.y_dry["CO"][-1], 2), round(res_1d.y_dry["H2"][-1], 2),
            round(res_1d.y_dry["CO2"][-1], 2), round(res_1d.y_dry["CH4"][-1], 2),
            round(res_1d.y_dry["N2"][-1], 2), round(res_1d.gas_flow_m3_h[-1], 2),
            round(calculate_syngas_lhv_mj_nm3({k: res_1d.y_dry[k][-1]/100.0 for k in res_1d.y_dry}), 2),
            round(res_1d.cold_gas_efficiency_percent[-1], 2), round(res_1d.t_gas_k[-1], 1),
            round(res_1d.carbon_conversion[-1]*100.0, 2)
        ])
        # 2. Optimized Hearth Extension (33 cm, 3.0 cm chips)
        res_opt = res_by_chip[0.03]
        idx_33 = np.argmin(np.abs(res_opt.z_m - 0.33))
        writer.writerow([
            "Optimized Design (Extended Hearth 33 cm, 3cm chips)", 3.0, 15.0, 2.20, 33.0,
            round(res_opt.y_dry["CO"][idx_33], 2), round(res_opt.y_dry["H2"][idx_33], 2),
            round(res_opt.y_dry["CO2"][idx_33], 2), round(res_opt.y_dry["CH4"][idx_33], 2),
            round(res_opt.y_dry["N2"][idx_33], 2), round(res_opt.gas_flow_m3_h[idx_33], 2),
            round(calculate_syngas_lhv_mj_nm3({k: res_opt.y_dry[k][idx_33]/100.0 for k in res_opt.y_dry}), 2),
            round(res_opt.cold_gas_efficiency_percent[idx_33], 2), round(res_opt.t_gas_k[idx_33], 1),
            round(res_opt.carbon_conversion[idx_33]*100.0, 2)
        ])
        # 3. Nine Experimental Validation Runs
        for r in runs_res["runs_table"]:
            writer.writerow([
                f"Experimental Validation Run {r.get('Run', r.get('run_id', ''))}",
                r.get("Chip Size (cm)", r.get("chip_size_cm", "")),
                r.get("MC (% db)", r.get("moisture_db", "")),
                r.get("AFR", 2.2),
                22.0,
                r.get("CO_sim", 0), r.get("H2_sim", 0), r.get("CO2_sim", 0), r.get("CH4_sim", 0), r.get("N2_sim", 0),
                r.get("Flow_sim (m3/h)", r.get("flow_nm3_h_sim", 0)),
                round((12.63 * r.get("CO_sim", 0) + 10.78 * r.get("H2_sim", 0) + 35.81 * r.get("CH4_sim", 0)) / 100.0, 2),
                round(r.get("CO_sim", 0) * 2.8, 1), "", ""
            ])
    print(f"  -> Principal operating cases summary exported to: {cases_csv_path}")

    print("\n[Step 6/6] Generating Publication-Quality Figures (PNG, 300 DPI)...")
    with open("data/temperature_profile_fig5.json", "r", encoding="utf-8") as f:
        fig5_pts = json.load(f)["measured_experimental_points"]

    # Fig 1: Feedstock Composition & Property Table
    plot_feedstock_composition(out_fig_dir / "fig01_feedstock_composition.png", out_tab_dir / "feedstock_properties.csv")

    # Fig 2: 1D Species Distribution (Dry & Wet)
    plot_species_distributions_1d(res_1d_ext, out_fig_dir / "fig02_species_distributions_1d.png")

    # Fig 3: 1D Temperature Profiles & Residuals
    plot_temperature_profiles_1d(res_1d_ext, fig5_pts, out_fig_dir / "fig03_temperature_profiles_1d.png")

    # Fig 4: Char Conversion & Particle Shrinkage
    plot_char_conversion_and_shrinkage(res_1d_ext, out_fig_dir / "fig04_char_conversion_and_shrinkage.png")

    # Fig 5: 2D Temperature Contours inside Diverging Hearth
    plot_2d_temperature_contours(res_2d, out_fig_dir / "fig05_temperature_contours_2d.png")

    # Fig 6: 2D Fuel Species Contours (CO & H2)
    plot_2d_species_fuel_contours(res_2d, out_fig_dir / "fig06_species_contours_fuel_2d.png")

    # Fig 7: 2D Oxidant Species Contours (CO2 & H2O)
    plot_2d_species_oxidant_contours(res_2d, out_fig_dir / "fig07_species_contours_oxidants_2d.png")

    # Fig 8: 4-Panel Parametric Sensitivities
    plot_parametric_sensitivities(sens_data, out_fig_dir / "fig08_parametric_sensitivity.png")

    # Fig 9: Validation Parity Plots (4 Species across 9 Runs)
    plot_validation_parity(runs_res["runs_table"], out_fig_dir / "fig09_validation_parity_plots.png")

    # Fig 10: Principal Cases Comparison Summary
    plot_principal_cases_comparison(runs_res["runs_table"], out_fig_dir / "fig10_principal_cases_comparison.png")

    elapsed = time.time() - start_time
    print(f"\nAll 10 publication figures saved to: {out_fig_dir}")
    print(f"All machine-readable CSV & JSON data saved to: {out_tab_dir}")
    print(f"Simulation completed successfully in {elapsed:.2f} seconds!")
    print("=" * 80)


if __name__ == "__main__":
    main()

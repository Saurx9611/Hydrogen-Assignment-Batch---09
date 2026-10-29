"""
scripts/make_report_tables.py - Generate LaTeX tables and number macros for the report
directly from outputs/tables/*. Every simulated number in the report comes from here.

    python scripts/make_report_tables.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "outputs" / "tables"
OUT = ROOT / "report" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

k = json.loads((TAB / "key_results.json").read_text())
val = json.loads((TAB / "validation_summary.json").read_text())


def rows(name):
    with open(TAB / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(x, nd=2):
    return f"{float(x):.{nd}f}"


# --------------------------------------------------------------------- macros
M = {}
ref = k["reference_case_1d"]
cal = k["calibration"]
f5 = k["fig5"]
p = k["parameters"]
st = k["nine_runs"]["stats"]
st7 = k["nine_runs"]["stats_excl_run7"]
td = k["two_d"]
bal = k["balances"]
M.update({
    "Uwall": fmt(p["u_wall_w_m2_k"], 1), "etaB": fmt(p["eta_boudouard"], 3), "etaWG": fmt(p["eta_water_gas"], 3),
    "AFRstoich": fmt(k["feedstock_derived"]["afr_stoich"], 2), "LHVwood": fmt(k["feedstock_derived"]["lhv"], 2),
    "ERref": fmt(2.20 / k["feedstock_derived"]["afr_stoich"], 2), "ERcal": fmt(1.86 / k["feedstock_derived"]["afr_stoich"], 2),
    "Formula": k["feedstock_derived"]["formula"].replace("CH", "CH$_{").replace("O", "}$O$_{").replace("N", "}$N$_{") + "}$",
    "TthroatRef": fmt(ref["T_throat_K"], 0), "TadRef": fmt(ref["T_adiabatic_mixed_K"], 0), "TsZeroRef": fmt(ref["T_s0_K"], 0),
    "TexitRef": fmt(ref["T_exit_K"], 0), "TtenRef": fmt(ref["T_at"]["z10"], 0), "TfiveRef": fmt(ref["T_at"]["z5"], 0),
    "dTgsMax": fmt(ref["dTgs_max_K"], 0), "zEquil": fmt(ref["z_dTgs_below_10K_cm"], 1),
    "COexitRef": fmt(ref["exit_dry"]["CO"]), "HtwoExitRef": fmt(ref["exit_dry"]["H2"]), "COtwoExitRef": fmt(ref["exit_dry"]["CO2"]),
    "CHfourExitRef": fmt(ref["exit_dry"]["CH4"]), "NtwoExitRef": fmt(ref["exit_dry"]["N2"]),
    "COthroatRef": fmt(ref["throat_dry"]["CO"]), "HtwoThroatRef": fmt(ref["throat_dry"]["H2"]), "COtwoThroatRef": fmt(ref["throat_dry"]["CO2"]),
    "HtwoOinRef": fmt(ref["h2o_wet_in"], 1), "HtwoOoutRef": fmt(ref["h2o_wet_out"], 1),
    "XcRef": fmt(ref["Xc_exit_percent"], 1), "zHalfRef": fmt(ref["z_half_conversion_cm"], 1), "dpExitRef": fmt(ref["dp_exit_cm"], 2),
    "FlowRef": fmt(ref["gas_flow_nm3_h"], 1), "LHVRef": fmt(ref["LHV_MJ_Nm3"], 2), "CGERef": fmt(ref["CGE_percent"], 1),
    "WallkWRef": fmt(ref["wall_loss_kW"], 1), "WallPctRef": fmt(ref["wall_loss_percent"], 1), "QinRef": fmt(ref["energy_input_kW"], 1),
    "CalMAE": fmt(cal["MAE_percent"]), "CalRMSE": fmt(cal["RMSE_percent"]), "CalMAEJ": fmt(cal["Jayah_MAE_percent"]),
    "CalRMSEJ": fmt(cal["Jayah_RMSE_percent"]), "CalTthroat": fmt(cal["throat_T_K"], 0), "CalTad": fmt(cal["throat_T_adiabatic_mixed_K"], 0),
    "CalXc": fmt(cal["char_conversion_percent"], 1), "CalCGE": fmt(cal["cold_gas_efficiency_percent"], 1),
    "CalTexit": fmt(cal["exit_gas_T_K"], 0), "CalFlow": fmt(cal["gas_flow_nm3_h"], 1),
    "TempMAE": fmt(f5["MAE_K"], 0), "TempRMSE": fmt(f5["RMSE_K"], 0), "TempBias": fmt(f5["bias_K"], 0),
    "TempMAEJ": fmt(f5["Jayah_MAE_K"], 0), "TempRMSEJ": fmt(f5["Jayah_RMSE_K"], 0),
    "TwoDaxisTexit": fmt(td["stations"]["z22"]["T_axis"], 0), "TwoDwallTexit": fmt(td["stations"]["z22"]["T_wall_cell"], 0),
    "TwoDaxisTfive": fmt(td["stations"]["z5"]["T_axis"], 0), "TwoDwallTfive": fmt(td["stations"]["z5"]["T_wall_cell"], 0),
    "TwoDmixT": fmt(td["mixed_T_exit_K"], 0), "TwoDwallkW": fmt(td["wall_loss_kW"], 1),
    "TwoDCOaxis": fmt(td["stations"]["z22"]["CO_axis"], 1), "TwoDCOwall": fmt(td["stations"]["z22"]["CO_wall_cell"], 1),
    "TwoDHtwoaxis": fmt(td["stations"]["z22"]["H2_axis"], 1), "TwoDHtwowall": fmt(td["stations"]["z22"]["H2_wall_cell"], 1),
    "TwoDXcAxisEleven": fmt(td["stations"]["z11"]["Xc_axis"], 1), "TwoDXcWallExit": fmt(td["stations"]["z22"]["Xc_wall_cell"], 1),
    "TwoDXcAxisFive": fmt(td["stations"]["z5"]["Xc_axis"], 1),
    "TwoDmixCO": fmt(td["mixed_exit_dry"]["CO"]), "TwoDmixHtwo": fmt(td["mixed_exit_dry"]["H2"]),
    "TwoDmixCOtwo": fmt(td["mixed_exit_dry"]["CO2"]), "TwoDmixNtwo": fmt(td["mixed_exit_dry"]["N2"]),
    "TwoDcells": str(td["n_cells"]), "TwoDnz": str(td["n_z"]),
    "EnergyResidual": fmt(bal["energy"]["residual_percent_of_feed_HHV"], 2),
    "WGSfastCO": fmt(k["wgs_sensitivity_calibration_case"]["fast_wgs_a=2.78e3"]["CO"], 1),
    "WGSfastHtwo": fmt(k["wgs_sensitivity_calibration_case"]["fast_wgs_a=2.78e3"]["H2"], 1),
    "WGSfastCOtwo": fmt(k["wgs_sensitivity_calibration_case"]["fast_wgs_a=2.78e3"]["CO2"], 1),
    "Runtime": fmt(k["runtime_s"], 0),
    "WallShare": fmt(ref["wall_share_of_sensible_drop_percent"], 0),
    "RxnShare": fmt(100 - ref["wall_share_of_sensible_drop_percent"], 0),
    "SensDrop": fmt(ref["sensible_drop_kW"], 1),
    "BaseTtwelve": fmt(k["base_case_T_at_12cm_K"], 0),
})
for sp, tag in (("CO", "CO"), ("H2", "Htwo"), ("CO2", "COtwo"), ("CH4", "CHfour"), ("N2", "Ntwo"), ("LHV", "LHV")):
    M[f"MAE{tag}"] = fmt(st[sp]["MAE"])
    M[f"RMSE{tag}"] = fmt(st[sp]["RMSE"])
    M[f"Bias{tag}"] = f"{st[sp]['bias']:+.2f}"
    M[f"Rsq{tag}"] = fmt(st[sp]["R2_vs_1to1"])
    M[f"Within{tag}"] = str(st[sp]["within_10pct"])
    M[f"Std{tag}"] = fmt(st[sp]["measured_std"])
    M[f"MAEx{tag}"] = fmt(st7[sp]["MAE"])
    M[f"Biasx{tag}"] = f"{st7[sp]['bias']:+.2f}"

runs = rows("table3_nine_runs_validation.csv")
imp = [float(r["Implied feed (kg/h)"]) for r in runs]
M["ImpliedFeedMin"], M["ImpliedFeedMax"] = fmt(min(imp), 1), fmt(max(imp), 1)
ratio = [float(r["Flow_sim (Nm3/h dry)"]) / float(r["Flow_meas (m3/h)"]) for r in runs]
M["FlowRatioMin"], M["FlowRatioMax"] = fmt(min(ratio) * 100, 0), fmt(max(ratio) * 100, 0)
tt = [float(r["T_throat_K"]) for r in runs]
M["RunTthroatMin"], M["RunTthroatMax"] = fmt(min(tt), 0), fmt(max(tt), 0)

t7 = {}
for r in rows("table7_replication.csv"):
    t7.setdefault(r["Parameter"], []).append(r)
names = {"chip_size_cm": "Chip", "moisture_content_percent_db": "MC", "heat_loss_percent_input_energy": "Loss",
         "throat_angle_degrees": "Angle", "air_temperature_k": "Air"}
for key, tag in names.items():
    for i, r in enumerate(t7[key]):
        sfx = "ABC"[i]
        M[f"Eff{tag}{sfx}"] = fmt(r["Eff_22cm_model"], 1)
        M[f"Opt{tag}{sfx}"] = fmt(r["Opt_length_model_cm"], 0)
        M[f"EffOpt{tag}{sfx}"] = fmt(r["Eff_opt_model"], 1)
        M[f"U{tag}{sfx}"] = fmt(r["U_wall_W_m2K"], 0)

sw = k["sweeps"]
M["AFRCGElo"], M["AFRCGEhi"] = fmt(sw["afr"][0]["cge"], 1), fmt(sw["afr"][-1]["cge"], 1)
M["AFRTlo"], M["AFRThi"] = fmt(sw["afr"][0]["t_throat"], 0), fmt(sw["afr"][-1]["t_throat"], 0)
M["AFRXclo"], M["AFRXchi"] = fmt(sw["afr"][0]["xc"] * 100, 0), fmt(sw["afr"][-1]["xc"] * 100, 0)
lh = [s["lhv"] for s in sw["afr"]]
M["AFRLHVmin"], M["AFRLHVmax"] = fmt(min(lh), 2), fmt(max(lh), 2)
M["FeedFlowLo"], M["FeedFlowHi"] = fmt(sw["feed"][0]["flow"], 1), fmt(sw["feed"][-1]["flow"], 1)
M["FeedCGElo"], M["FeedCGEhi"] = fmt(sw["feed"][0]["cge"], 1), fmt(sw["feed"][-1]["cge"], 1)
M["FeedTlo"], M["FeedThi"] = fmt(sw["feed"][0]["t_exit"], 0), fmt(sw["feed"][-1]["t_exit"], 0)

with open(OUT / "macros.tex", "w", encoding="utf-8") as f:
    f.write("% AUTO-GENERATED by scripts/make_report_tables.py - do not edit\n")
    for name, v in M.items():
        assert name.isalpha(), name
        f.write(f"\\newcommand{{\\R{name}}}{{{v}}}\n")

# --------------------------------------------------------------------- tables
cr = cal["rows"]
lab = {"CO": "CO", "H2": r"H$_2$", "CO2": r"CO$_2$", "CH4": r"CH$_4$\textsuperscript{a}", "N2": r"N$_2$"}
with open(OUT / "table_calibration.tex", "w") as f:
    for r in cr:
        f.write(f"{lab[r['Species']]} & {r['Measured (%)']:.1f} & {r['Jayah model (%)']:.1f} & {r['This model (%)']:.2f} & "
                f"{r['Abs error (% pts)']:+.2f} & {r['Jayah abs error (% pts)']:+.2f} \\\\\n")

with open(OUT / "table_ninerun_composition.tex", "w") as f:
    for r in runs:
        cells = [r["Run"], r["Chip Size (cm)"], r["MC (% db)"], r["AFR"], fmt(r["T_throat_K"], 0)]
        for sp in ("CO", "H2", "CO2", "N2"):
            cells.append(f"{float(r[sp + '_meas']):.1f} / {float(r[sp + '_sim']):.1f}")
        f.write(" & ".join(cells) + " \\\\\n")

with open(OUT / "table_ninerun_stats.tex", "w") as f:
    for sp, labl in (("CO", "CO"), ("H2", r"H$_2$"), ("CO2", r"CO$_2$"), ("N2", r"N$_2$"), ("CH4", r"CH$_4$\textsuperscript{a}"), ("LHV", r"LHV (MJ/Nm$^3$)")):
        s = st[sp]
        f.write(f"{labl} & {s['MAE']:.2f} & {s['RMSE']:.2f} & {s['bias']:+.2f} & {s['measured_std']:.2f} & "
                f"{s['R2_vs_1to1']:.2f} & {s['within_10pct']}/9 & {st7[sp]['MAE']:.2f} \\\\\n")

with open(OUT / "table_flow.tex", "w") as f:
    for r in runs:
        f.write(f"{r['Run']} & {float(r['LHV_meas (MJ/Nm3)']):.2f} & {float(r['LHV_sim (MJ/Nm3)']):.2f} & "
                f"{float(r['Flow_meas (m3/h)']):.1f} & {float(r['Flow_sim (Nm3/h dry)']):.1f} & {float(r['Implied feed (kg/h)']):.1f} & "
                f"{float(r['CGE_sim (%)']):.1f} \\\\\n")

with open(OUT / "table_temperature.tex", "w") as f:
    for r in f5["comparison"]:
        f.write(f"{r['z_cm']:.1f} & {r['T_meas_K']:.0f} & {r['T_sim_K']:.0f} & {r['Error_K']:+.0f} & "
                f"{r['T_Jayah_model_K']:.0f} & {r['Jayah_error_K']:+.0f} \\\\\n")

pname = {"chip_size_cm": ("Chip size", "{:.0f} cm"), "moisture_content_percent_db": ("Moisture", "{:.0f} \\% d.b."),
         "heat_loss_percent_input_energy": ("Heat loss", "{:.0f} \\%"), "throat_angle_degrees": ("Throat angle", "{:.0f}$^\\circ$"),
         "air_temperature_k": ("Air temperature", "{:.0f} K")}
with open(OUT / "table_table7.tex", "w") as f:
    for key in names:
        nm, vf = pname[key]
        for i, r in enumerate(t7[key]):
            def j(col):
                return r[col] if r[col] not in ("", None) else "--"
            first = nm if i == 0 else ""
            f.write(f"{first} & {vf.format(float(r['Value']))} & {fmt(r['Eff_22cm_model'], 1)} & {j('Eff_22cm_Jayah')} & "
                    f"{fmt(r['Opt_length_model_cm'], 0)} & {fmt(r['Opt_length_Jayah_cm'], 0) if r['Opt_length_Jayah_cm'] else '--'} & {fmt(r['Eff_opt_model'], 1)} & "
                    f"{j('Eff_opt_Jayah')} & {fmt(r['Wall_loss_22cm_pct'], 1)} \\\\\n")
        f.write("\\midrule\n")

print(f"wrote {len(M)} macros and tables to {OUT}")

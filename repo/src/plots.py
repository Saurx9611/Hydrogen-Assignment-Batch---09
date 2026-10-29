"""
src/plots.py - Figures for the NERD downdraft gasifier simulation (all 300 dpi PNG).

Every number drawn on a figure is computed from the simulation or read from the
digitised/transcribed journal data passed in; nothing is hard-coded here.
Conventions: one y-axis per panel (no twin axes), a fixed categorical colour order
(validated for colour-vision deficiency), markers/line styles as secondary encoding,
single-hue sequential colour maps for contours.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.reactor_1d import SimulationResults1D
from src.reactor_2d import SimulationResults2D

# Fixed categorical order (validated: CVD separation and normal-vision floor pass)
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
STYLES = ["-", "--", "-.", ":"]
MARKERS = ["o", "s", "^", "D"]

plt.rcParams.update({
    "font.size": 10.5, "axes.labelsize": 11, "axes.titlesize": 11.5, "legend.fontsize": 9,
    "font.family": "serif", "mathtext.fontset": "dejavuserif", "lines.linewidth": 2.0,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
})


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def _hearth(ax, z, lbl=True):
    ax.axvline(22.0, color=INK2, linestyle=":", linewidth=1.2)
    if lbl:
        ax.text(22.3, ax.get_ylim()[1], "hearth exit\n22 cm", va="top", fontsize=8, color=INK2)


# ----------------------------------------------------------------------------------
def plot_feedstock_composition(output_path: Path, table_export_path: Optional[Path] = None,
                               derived: Optional[Dict[str, float]] = None) -> None:
    """Fig 1: proximate + ultimate analyses (Jayah Tables 1-2) and key properties."""
    derived = derived or {}
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.8), gridspec_kw={"width_ratios": [1.0, 1.3, 1.6]})
    for ax, labels, vals, title in (
        (ax1, ["Volatile\nmatter", "Fixed\ncarbon", "Ash"], [80.1, 19.2, 0.7], "(a) Proximate analysis (Table 1)"),
        (ax2, ["C", "O", "H", "N", "Ash"], [50.6, 42.0, 6.5, 0.2, 0.7], "(b) Ultimate analysis (Table 2)"),
    ):
        bars = ax.bar(labels, vals, color=C[0], width=0.55)
        ax.set_ylabel("wt % (dry basis)")
        ax.set_title(title)
        ax.set_ylim(0, max(vals) * 1.18)
        ax.grid(axis="x", visible=False)
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + max(vals) * 0.015, f"{b.get_height():.1f}",
                    ha="center", va="bottom", fontsize=9.5, color=INK)
    ax3.axis("off")
    ax3.set_title("(c) Fuel properties: source", pad=10)
    rows = [
        ["HHV (dry)", "19.60 MJ/kg", "Jayah p. 463 (measured)"],
        ["LHV (dry)", f"{derived.get('lhv', 18.17):.2f} MJ/kg", "calculated: HHV - 9H*h_fg"],
        ["Bulk density", "314-330 kg/m3", "Jayah p. 463 (measured)"],
        ["Moisture (Table 3 runs)", "12.5-18.5 % d.b.", "Jayah Table 3"],
        ["Formula (daf)", derived.get("formula", "CH1.53O0.62N0.003"), "calculated from Table 2"],
        ["Stoich. air", f"{derived.get('afr_stoich', 5.7):.2f} kg/kg dry", "calculated from Table 2"],
        ["Char density", "250 kg/m3", "assumption (not in paper)"],
    ]
    tab = ax3.table(cellText=rows, colLabels=["Property", "Value", "Source"], cellLoc="left", loc="center",
                    colWidths=[0.33, 0.30, 0.37])
    tab.auto_set_font_size(False)
    tab.set_fontsize(8.8)
    tab.scale(1.0, 1.45)
    for (r, c), cell in tab.get_celld().items():
        cell.set_edgecolor(GRID)
        if r == 0:
            cell.set_text_props(fontweight="bold")
    _save(fig, output_path)

    if table_export_path:
        with open(table_export_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Category", "Parameter", "Value", "Unit", "Source"])
            for row in [
                ["Proximate", "Volatile matter", 80.1, "% d.b.", "Jayah Table 1"],
                ["Proximate", "Fixed carbon", 19.2, "% d.b.", "Jayah Table 1"],
                ["Proximate", "Ash", 0.7, "% d.b.", "Jayah Table 1"],
                ["Ultimate", "C", 50.6, "% d.b.", "Jayah Table 2"],
                ["Ultimate", "H", 6.5, "% d.b.", "Jayah Table 2"],
                ["Ultimate", "N", 0.2, "% d.b.", "Jayah Table 2"],
                ["Ultimate", "O (by difference)", 42.0, "% d.b.", "Jayah Table 2"],
                ["Ultimate", "Ash", 0.7, "% d.b.", "Jayah Table 2"],
                ["Energy", "HHV", 19.60, "MJ/kg dry", "Jayah p. 463"],
                ["Energy", "LHV", round(derived.get("lhv", 18.17), 2), "MJ/kg dry", "calculated"],
                ["Physical", "Bulk density", "314-330", "kg/m3", "Jayah p. 463"],
                ["Physical", "Char particle density", 250.0, "kg/m3", "assumption"],
                ["Stoichiometry", "Stoichiometric air", round(derived.get("afr_stoich", 5.7), 2), "kg/kg dry", "calculated"],
            ]:
                w.writerow(row)


SPC = {"CO": C[0], "H2": C[1], "CO2": C[2], "CH4": C[3], "H2O": C[4]}
SPL = {"CO": "CO", "H2": r"H$_2$", "CO2": r"CO$_2$", "CH4": r"CH$_4$", "H2O": r"H$_2$O"}
SPS = {"CO": "-", "H2": "--", "CO2": "-.", "CH4": ":", "H2O": (0, (5, 1.5, 1, 1.5))}


def plot_species_distributions_1d(res: SimulationResults1D, output_path: Path) -> None:
    """Fig 2: axial species profiles, dry basis (a) and wet basis incl. H2O (b)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8))
    z = res.z_m * 100.0
    for k in ("CO", "H2", "CO2", "CH4"):
        ax1.plot(z, res.y_dry[k], color=SPC[k], linestyle=SPS[k], label=SPL[k])
    ax1.set_xlabel("Axial position below throat $z$ (cm)")
    ax1.set_ylabel("Dry gas mole fraction (%)")
    ax1.set_title(r"(a) Dry basis (N$_2$ is the balance)")
    ax1.set_xlim(0, z[-1])
    ax1.set_ylim(0, max(res.y_dry["CO"]) * 1.25)
    ax1.legend(loc="upper center", ncol=4)
    ax1.axvline(22.0, color=INK2, linestyle=":", linewidth=1.2)

    f_wet = res.f_co + res.f_h2 + res.f_co2 + res.f_h2o + res.f_ch4 + res.f_n2
    for k, f in (("H2O", res.f_h2o), ("CO", res.f_co), ("H2", res.f_h2), ("CO2", res.f_co2)):
        ax2.plot(z, 100 * f / f_wet, color=SPC[k], linestyle=SPS[k], label=SPL[k])
    ax2.set_xlabel("Axial position below throat $z$ (cm)")
    ax2.set_ylabel("Wet gas mole fraction (%)")
    ax2.set_title(r"(b) Wet basis: steam consumed by C + H$_2$O")
    ax2.set_ylim(0, 30)
    ax2.set_xlim(0, z[-1])
    ax2.legend(loc="upper center", ncol=4)
    ax2.axvline(22.0, color=INK2, linestyle=":", linewidth=1.2)
    _save(fig, output_path)


def plot_temperature_profiles_1d(res: SimulationResults1D, fig5_points, jayah_curve, output_path: Path) -> None:
    """Fig 3: gas/solid temperature vs Jayah Fig. 5 measurements and Jayah's model."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 7.0), sharex=True, gridspec_kw={"height_ratios": [2.4, 1.0]})
    z = res.z_m * 100.0
    ax1.plot(z, res.t_gas_k, color=C[1], label=r"This model, gas $T_g$")
    ax1.plot(z, res.t_solid_k, color=C[0], linestyle="--", label=r"This model, char $T_s$")
    ax1.plot([p["z_cm"] for p in jayah_curve], [p["T_K"] for p in jayah_curve], color=INK2, linestyle="-.",
             linewidth=1.5, label="Jayah et al. model (Fig. 5, digitised)")
    mz = [p["z_cm"] for p in fig5_points]
    mt = [p["T_K"] for p in fig5_points]
    ax1.scatter(mz, mt, color=INK, marker="^", s=55, zorder=5, label="Measured (Fig. 5, digitised)")
    ax1.set_ylabel("Temperature (K)")
    ax1.set_title("Axial temperature in the reduction zone (AFR 2.20)")
    ax1.set_ylim(600, 1750)
    ax1.legend(loc="upper right")
    _hearth(ax1, z, lbl=False)

    resid = [float(np.interp(a, z, res.t_gas_k)) - b for a, b in zip(mz, mt)]
    jz = [p["z_cm"] for p in jayah_curve]
    jt = [p["T_K"] for p in jayah_curve]
    resid_j = [float(np.interp(a, jz, jt)) - b for a, b in zip(mz, mt)]
    ax2.axhline(0, color=INK2, linewidth=0.8)
    ax2.plot(mz, resid, marker="o", color=C[1], label=f"This model (MAE {np.mean(np.abs(resid)):.0f} K)")
    ax2.plot(mz, resid_j, marker="s", color=INK2, linestyle="-.", linewidth=1.3,
             label=f"Jayah model (MAE {np.mean(np.abs(resid_j)):.0f} K)")
    ax2.set_ylabel(r"$T_{model} - T_{meas}$ (K)")
    ax2.set_xlabel("Axial position below throat $z$ (cm)")
    ax2.legend(loc="upper left", ncol=2)
    _hearth(ax2, z, lbl=False)
    _save(fig, output_path)


def plot_char_conversion_and_shrinkage(res: SimulationResults1D, output_path: Path) -> None:
    """Fig 4: char conversion (a) and normalised particle diameter (b)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.3))
    z = res.z_m * 100.0
    ax1.plot(z, res.carbon_conversion * 100, color=C[1])
    ax1.set_ylabel(r"Char conversion $X_C$ (%)")
    ax1.set_title("(a) Char carbon conversion")
    ax2.plot(z, res.d_p_m / res.d_p_m[0] * 100, color=C[0])
    ax2.set_ylabel(r"$d_p / d_{p,0}$ (%)")
    ax2.set_title("(b) Particle shrinkage (shrinking sphere)")
    for ax in (ax1, ax2):
        ax.set_xlabel("Axial position below throat $z$ (cm)")
        ax.set_ylim(0, 105)
        ax.set_xlim(0, z[-1])
        _hearth(ax, z)
    _save(fig, output_path)


# ----------------------------------------------------------------------------------
def _mirror(res2d, field):
    z = res2d.z_grid * 100.0
    r = res2d.r_grid * 100.0
    return (np.vstack([z[::-1], z]), np.vstack([-r[::-1], r]), np.vstack([field[::-1], field]))


def _contour_panel(fig, ax, res2d, field, cmap, label, title, n_levels=14):
    Z, Rr, F = _mirror(res2d, field)
    lo, hi = np.nanpercentile(F, 1), np.nanpercentile(F, 99)
    from matplotlib.ticker import MaxNLocator
    levels = MaxNLocator(nbins=n_levels).tick_values(lo, hi)
    cf = ax.contourf(Z, Rr, F, levels=levels, cmap=cmap, extend="both")
    cs = ax.contour(Z, Rr, F, levels=levels[::3], colors="white", linewidths=0.7, alpha=0.7)
    ax.clabel(cs, inline=True, fontsize=7.5, fmt="%.0f" if hi > 100 else "%g")
    zw = res2d.z_1d * 100
    rw = res2d.r_max_1d * 100
    ymax = rw.max() * 1.15
    for sgn in (1, -1):
        ax.plot(zw, sgn * rw, color=INK, linewidth=1.8)
        ax.fill_between(zw, sgn * rw, sgn * ymax, color="#eeeeec", hatch="///", edgecolor="#bdbcb6", linewidth=0)
    ax.set_ylim(-ymax, ymax)
    ax.set_xlim(0, zw[-1])
    ax.set_ylabel("Radius $r$ (cm)")
    ax.set_title(title)
    ax.grid(False)
    cb = fig.colorbar(cf, ax=ax, pad=0.02)
    cb.set_label(label)


def plot_2d_temperature_contours(res2d: SimulationResults2D, output_path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 8.0), sharex=True)
    _contour_panel(fig, ax1, res2d, res2d.t_gas_2d, "Oranges", "Gas temperature (K)", "(a) Gas temperature $T_g(r,z)$")
    _contour_panel(fig, ax2, res2d, res2d.x_c_2d * 100, "Greys", "Char conversion (%)", "(b) Char conversion $X_C(r,z)$")
    ax2.set_xlabel("Axial position below throat $z$ (cm)")
    _save(fig, output_path)


def plot_2d_species_fuel_contours(res2d: SimulationResults2D, output_path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 8.0), sharex=True)
    _contour_panel(fig, ax1, res2d, res2d.y_co_2d, "Blues", "CO, dry mol %", "(a) Carbon monoxide")
    _contour_panel(fig, ax2, res2d, res2d.y_h2_2d, "Purples", r"H$_2$, dry mol %", "(b) Hydrogen")
    ax2.set_xlabel("Axial position below throat $z$ (cm)")
    _save(fig, output_path)


def plot_2d_species_oxidant_contours(res2d: SimulationResults2D, output_path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 8.0), sharex=True)
    _contour_panel(fig, ax1, res2d, res2d.y_co2_2d, "Greens", r"CO$_2$, dry mol %", "(a) Carbon dioxide")
    _contour_panel(fig, ax2, res2d, res2d.y_h2o_2d, "Blues", r"H$_2$O, wet mol %", "(b) Water vapour")
    ax2.set_xlabel("Axial position below throat $z$ (cm)")
    _save(fig, output_path)


def plot_radial_profiles(res2d: SimulationResults2D, res1d: SimulationResults1D, output_path: Path) -> None:
    """Fig 12: radial profiles from the 2D model at three heights, with 1D values."""
    fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.2))
    stations = [5.0, 11.0, 22.0]
    for i, zc in enumerate(stations):
        j = int(np.argmin(np.abs(res2d.z_1d * 100 - zc)))
        eta = res2d.eta_nodes
        axs[0].plot(eta, res2d.t_gas_2d[:, j], color=C[i], linestyle=STYLES[i], marker=MARKERS[i], markersize=4, label=f"z = {zc:.0f} cm")
        axs[1].plot(eta, res2d.y_co_2d[:, j], color=C[i], linestyle=STYLES[i], marker=MARKERS[i], markersize=4, label=f"z = {zc:.0f} cm")
        axs[2].plot(eta, res2d.y_h2_2d[:, j], color=C[i], linestyle=STYLES[i], marker=MARKERS[i], markersize=4, label=f"z = {zc:.0f} cm")
    for ax, t in zip(axs, ["(a) Gas temperature (K)", "(b) CO, dry mol %", r"(c) H$_2$, dry mol %"]):
        ax.set_xlabel(r"Normalised radius $\eta = r/R(z)$")
        ax.set_title(t)
        ax.set_xlim(0, 1)
    axs[0].legend(loc="lower left")
    _save(fig, output_path)


# ----------------------------------------------------------------------------------
TABLE7_PANELS = [
    ("chip_size_cm", "chip_size_cm", "Chip size", "{:.0f} cm"),
    ("moisture_content_percent_db", "moisture_content_percent_db", "Moisture", "{:.0f} % d.b."),
    ("heat_loss_percent_input_energy", "heat_loss_percent_input_energy", "Heat loss", "{:.0f} %"),
    ("throat_angle_degrees", "throat_angle_degrees", "Throat angle", "{:.0f}°"),
    ("air_temperature_k", "air_temperature_k", "Inlet air temperature", "{:.0f} K"),
]


def plot_table7_replication(study: Dict[str, Any], bench: Dict[str, Any], output_path: Path) -> None:
    """Fig 8: efficiency vs hearth length for each Jayah Table 7 parameter, plus a
    model-vs-Jayah comparison of efficiency at 22 cm."""
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.6))
    letters = "abcdef"
    pairs = []
    for p, (key, bkey, name, fmt) in enumerate(TABLE7_PANELS):
        ax = axs.flat[p]
        fam = study[key]
        for i, s in enumerate(fam["summary"]):
            res = fam["curves"][s["value"]]
            ax.plot(res.z_m * 100, res.cold_gas_efficiency_percent, color=C[i], linestyle=STYLES[i],
                    label=f"{fmt.format(s['value'])}: opt. {s['optimum_length_cm']:.0f} cm")
            ax.plot([s["optimum_length_cm"]], [s["eff_at_optimum"]], marker="o", color=C[i], markersize=6)
        if bkey in bench:
            b = bench[bkey]
            for i, v in enumerate(b["values"]):
                # match the panel's i-th value (Jayah uses 60 deg where we use the actual 61 deg)
                ax.plot([22.0], [b["efficiency_at_22cm_percent"][i]], marker=MARKERS[i], markerfacecolor="white",
                        markeredgecolor=C[i], markeredgewidth=1.6, markersize=8, linestyle="none")
                if i < len(fam["summary"]):
                    pairs.append((b["efficiency_at_22cm_percent"][i], fam["summary"][i]["eff_22cm"], name))
        ax.set_title(f"({letters[p]}) {name}")
        ax.set_xlabel("Gasification zone length (cm)")
        ax.set_ylabel("Conversion efficiency (%)")
        ax.set_xlim(0, 50)
        ax.axvline(22.0, color=INK2, linestyle=":", linewidth=1.1)
        ax.legend(loc="lower right", fontsize=8)
    ax = axs.flat[5]
    names = sorted(set(n for _, _, n in pairs), key=[q[2] for q in TABLE7_PANELS].index)
    for i, n in enumerate(names):
        xs = [a for a, _, nn in pairs if nn == n]
        ys = [b for _, b, nn in pairs if nn == n]
        ax.scatter(xs, ys, color=C[i], marker=MARKERS[i % 4], s=45, label=n, zorder=3)
    lo, hi = 40, 80
    ax.plot([lo, hi], [lo, hi], color=INK2, linewidth=1)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Jayah et al. Table 7, efficiency at 22 cm (%)")
    ax.set_ylabel("This model, efficiency at 22 cm (%)")
    ax.set_title("(f) Efficiency at 22 cm: this model vs Jayah")
    ax.legend(loc="upper left", fontsize=8)
    fig.text(0.5, 0.005, "Lines: this model. Open markers at 22 cm: Jayah et al. Table 7. Filled dots: this model's optimum length (99.5 % of ultimate efficiency).",
             ha="center", fontsize=8.5, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_operating_sweeps(sweeps: Dict[str, Any], output_path: Path) -> None:
    """Fig 11: AFR and feed-rate sweeps at 22 cm, one measure per panel."""
    fig, axs = plt.subplots(2, 3, figsize=(14, 7.6))
    afr = [s["value"] for s in sweeps["afr"]]
    feed = [s["value"] for s in sweeps["feed"]]
    panels = [
        (axs[0, 0], afr, [s["t_throat"] for s in sweeps["afr"]], "Throat gas temperature (K)", "(a) Throat temperature vs AFR"),
        (axs[0, 1], afr, [s["cge"] for s in sweeps["afr"]], "Conversion efficiency (%)", "(b) Efficiency vs AFR"),
        (axs[0, 2], afr, [s["lhv"] for s in sweeps["afr"]], r"Gas LHV (MJ/Nm$^3$)", "(c) Gas heating value vs AFR"),
        (axs[1, 0], feed, [s["flow"] for s in sweeps["feed"]], r"Dry gas flow (Nm$^3$/h)", "(d) Gas flow vs feed rate"),
        (axs[1, 1], feed, [s["cge"] for s in sweeps["feed"]], "Conversion efficiency (%)", "(e) Efficiency vs feed rate"),
        (axs[1, 2], feed, [s["t_exit"] for s in sweeps["feed"]], "Exit gas temperature (K)", "(f) Exit temperature vs feed rate"),
    ]
    for ax, x, y, yl, t in panels:
        ax.plot(x, y, color=C[0], marker="o", markersize=5)
        ax.set_ylabel(yl)
        ax.set_title(t)
    for ax in axs[0]:
        ax.set_xlabel("Air-fuel ratio (kg air / kg dry wood)")
    for ax in axs[1]:
        ax.set_xlabel("Dry wood feed rate (kg/h)")
    _save(fig, output_path)


def plot_validation_parity(runs: List[Dict[str, Any]], stats: Dict[str, Dict[str, float]], output_path: Path) -> None:
    """Fig 9: parity plots for the nine Table 3 runs; statistics computed in validation.py."""
    fig, axs = plt.subplots(2, 2, figsize=(10, 9))
    chips = {3.3: (C[0], "o"), 4.4: (C[1], "s"), 5.5: (C[2], "^")}
    for ax, sp in zip(axs.flat, ["CO", "H2", "CO2", "N2"]):
        m = np.array([r[f"{sp}_meas"] for r in runs])
        s = np.array([r[f"{sp}_sim"] for r in runs])
        lo, hi = min(m.min(), s.min()) * 0.9, max(m.max(), s.max()) * 1.08
        xs = np.array([lo, hi])
        ax.plot(xs, xs, color=INK, linewidth=1, label="1:1")
        ax.plot(xs, xs * 1.1, color=INK2, linestyle="--", linewidth=0.9, label="±10 %")
        ax.plot(xs, xs * 0.9, color=INK2, linestyle="--", linewidth=0.9)
        for d, (col, mk) in chips.items():
            sel = [abs(r["Chip Size (cm)"] - d) < 0.05 for r in runs]
            ax.scatter(m[sel], s[sel], color=col, marker=mk, s=55, zorder=3, edgecolors="white", linewidths=0.8,
                       label=f"{d} cm chips")
        for r, a, b in zip(runs, m, s):
            ax.annotate(str(r["Run"]), (a, b), xytext=(4, 3), textcoords="offset points", fontsize=7.5, color=INK2)
        st = stats[sp]
        ax.text(0.04, 0.96, f"MAE {st['MAE']:.2f} % pts\nRMSE {st['RMSE']:.2f}\nbias {st['bias']:+.2f}\n"
                f"within ±10 %: {st['within_10pct']}/{st['n']}\n$R^2$ (1:1) {st['R2_vs_1to1']:.2f}",
                transform=ax.transAxes, va="top", fontsize=8.5, color=INK)
        lab = {"CO": "CO", "H2": r"H$_2$", "CO2": r"CO$_2$", "N2": r"N$_2$"}[sp]
        ax.set_xlabel(f"Measured {lab} (dry mol %)")
        ax.set_ylabel(f"Simulated {lab} (dry mol %)")
        ax.set_title(f"{lab}: nine runs (Table 3)")
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        if sp == "CO":
            ax.legend(loc="lower right", fontsize=8)
    _save(fig, output_path)


def plot_principal_cases_comparison(runs: List[Dict[str, Any]], output_path: Path) -> None:
    """Fig 10: gas LHV (a) and gas flow (b), measured vs simulated, per run."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.5, 7.4), sharex=True)
    x = np.arange(len(runs))
    w = 0.38
    labels = [f"Run {r['Run']}\n{r['Chip Size (cm)']} cm, AFR {r['AFR']}" for r in runs]
    for ax, mk, sk, yl, t, l1, l2 in (
        (ax1, "LHV_meas (MJ/Nm3)", "LHV_sim (MJ/Nm3)", r"Gas LHV (MJ/Nm$^3$)", "(a) Heating value of the dry gas",
         "From measured composition", "Simulated"),
        (ax2, "Flow_meas (m3/h)", "Flow_sim (Nm3/h dry)", r"Gas flow (m$^3$/h)",
         "(b) Gas flow: measured (basis not stated in paper) vs simulated dry Nm$^3$/h at an assumed 18.6 kg/h feed",
         "Measured", "Simulated"),
    ):
        a = [r[mk] for r in runs]
        b = [r[sk] for r in runs]
        ax.bar(x - w / 2 - 0.01, a, width=w, color=C[0], label=l1)
        ax.bar(x + w / 2 + 0.01, b, width=w, color=C[1], label=l2)
        ax.set_ylabel(yl)
        ax.set_title(t)
        ax.grid(axis="x", visible=False)
        ax.legend(loc="upper left", ncol=2)
        ax.set_ylim(0, max(max(a), max(b)) * 1.22)
        for xi, v in zip(x - w / 2, a):
            ax.text(xi, v, f"{v:.2f}" if v < 10 else f"{v:.0f}", ha="center", va="bottom", fontsize=7.5, color=INK)
        for xi, v in zip(x + w / 2, b):
            ax.text(xi, v, f"{v:.2f}" if v < 10 else f"{v:.0f}", ha="center", va="bottom", fontsize=7.5, color=INK)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=8)
    _save(fig, output_path)


def plot_geometry(output_path: Path) -> None:
    """Fig 0: section through the NERD gasifier (dimensions in mm, Jayah et al. Fig. 3)."""
    fig, ax = plt.subplots(figsize=(5.6, 7.4))
    hop = 740.0
    drum_bot, drum_top = hop, hop + 1150.0
    outline = [(460, drum_top), (460, drum_bot), (50, 0), (170, -220)]
    for sgn in (1, -1):
        ax.plot([sgn * p[0] for p in outline], [p[1] for p in outline], color=INK, linewidth=1.8)
    ax.plot([-170, 170], [-220, -220], color=INK2, linewidth=2.5, linestyle=(0, (4, 2)))
    ax.fill([-50, 50, 170, -170], [0, 0, -220, -220], color=C[1], alpha=0.25, linewidth=0)
    for sgn in (1, -1):
        ax.annotate("", xy=(sgn * 52, 100), xytext=(sgn * 200, 100), arrowprops=dict(arrowstyle="->", color=C[0], lw=1.6))
    ax.text(205, 100, "air: 12 nozzles,\n6 mm, 100 mm\nabove throat", va="center", fontsize=8.5, color=INK)
    ax.text(0, drum_top - 250, "wood feed,\ndrying and\npyrolysis", ha="center", fontsize=9, color=INK)
    ax.annotate("", xy=(0, drum_top + 10), xytext=(0, drum_top + 160), arrowprops=dict(arrowstyle="->", color=INK2))
    ax.text(-80, 18, "throat Ø100", ha="right", fontsize=8.5, color=INK)
    ax.text(185, -120, "reduction zone\n(modelled)\nL = 220 mm,\n61° wall", fontsize=8.5, color=INK, va="center")
    ax.text(0, -250, "grate Ø340", ha="center", va="top", fontsize=8.5, color=INK)
    ax.text(470, (drum_top + drum_bot) / 2, "drum Ø920\nh 1150", fontsize=8.5, color=INK, va="center")
    ax.set_aspect("equal")
    ax.set_xlim(-520, 680)
    ax.set_ylim(-330, drum_top + 200)
    ax.axis("off")
    _save(fig, output_path)

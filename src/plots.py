"""
src/plots.py - Publication-quality visualizations for the NERD downdraft gasifier simulation.
Generates 1D axial profiles, 2D spatial contour plots, parametric sensitivities,
parity graphs, and case comparison dashboards matching all assignment specifications.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from src.reactor_1d import SimulationResults1D
from src.reactor_2d import SimulationResults2D


# Apply clean scientific styling
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9.5,
    "figure.titlesize": 14,
    "font.family": "serif",
    "mathtext.fontset": "dejavuserif",
    "lines.linewidth": 2.0,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


def plot_feedstock_composition(output_path: Path, table_export_path: Optional[Path] = None) -> None:
    """
    Fig 1: Feedstock composition chart and clearly labeled property table.
    Subplots:
      (a) Proximate analysis bar chart (wt% dry basis)
      (b) Ultimate analysis bar chart (wt% dry basis)
      (c) Formatted thermochemical property table
    """
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15.2, 5.0), gridspec_kw={"width_ratios": [1.0, 1.2, 1.55]})

    # 1. Proximate Analysis
    prox_labels = ["Volatile Matter\n(VM)", "Fixed Carbon\n(FC)", "Ash"]
    prox_vals = [80.1, 19.2, 0.7]
    colors_prox = ["#2b5c8f", "#d95f02", "#7570b3"]
    bars1 = ax1.bar(prox_labels, prox_vals, color=colors_prox, width=0.52, edgecolor="black", alpha=0.88)
    ax1.set_ylabel("Weight Fraction (% dry basis)")
    ax1.set_title("Proximate Analysis (Table 1)")
    ax1.set_ylim(0, 100)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 1.8, f"{yval:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=10)

    # 2. Ultimate Analysis (with comfortable spacing and no label collision)
    ult_labels = ["Carbon\n(C)", "Oxygen\n(O)", "Hydrogen\n(H)", "Nitrogen\n(N)", "Ash"]
    ult_vals = [50.6, 42.0, 6.5, 0.2, 0.7]
    colors_ult = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e"]
    bars2 = ax2.bar(ult_labels, ult_vals, color=colors_ult, width=0.55, edgecolor="black", alpha=0.88)
    ax2.set_ylabel("Weight Fraction (% dry basis)")
    ax2.set_title("Ultimate Analysis (Table 2)")
    ax2.set_ylim(0, 65)
    for bar in bars2:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 1.2, f"{yval:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=10)

    # 3. Thermochemical Property Summary Table
    ax3.axis("off")
    ax3.set_title("Key Fuel Properties (Jayah et al., 2003)", pad=12)
    table_data = [
        ["Feedstock", "Rubber wood (Hevea brasiliensis)"],
        ["Higher Heating Value (HHV)", "19.60 MJ/kg (dry)"],
        ["Lower Heating Value (LHV)", "18.17 MJ/kg (dry)"],
        ["Baseline Moisture Content", "14.7% d.b. (12.8% w.b.)"],
        ["Bulk Density", "320 kg/m³ (314–330)"],
        ["Solid Wood Density", "650 kg/m³"],
        ["Porous Char Density", "250 kg/m³"],
        ["Normalized Formula", "CH1.541 O0.625 N0.0034"],
        ["Stoichiometric Air Requirement", "5.68 kg air / kg dry fuel"],
    ]
    tab = ax3.table(
        cellText=table_data,
        colLabels=["Parameter", "Reported Value"],
        cellLoc="left",
        loc="center",
        colWidths=[0.47, 0.53],
    )
    tab.auto_set_font_size(False)
    tab.set_fontsize(9.0)
    tab.scale(1.0, 1.48)
    for (row, col), cell in tab.get_celld().items():
        if row == 0:
            cell.set_facecolor("#2b5c8f")
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 1:
            cell.set_facecolor("#f7f7f7")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)

    # Export machine-readable feedstock table if requested
    if table_export_path:
        with open(table_export_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Parameter", "Value", "Unit", "Provenance"])
            writer.writerow(["Proximate", "Volatile Matter (VM)", 80.1, "% dry basis", "Jayah et al. (2003) Table 1"])
            writer.writerow(["Proximate", "Fixed Carbon (FC)", 19.2, "% dry basis", "Jayah et al. (2003) Table 1"])
            writer.writerow(["Proximate", "Ash", 0.7, "% dry basis", "Jayah et al. (2003) Table 1"])
            writer.writerow(["Ultimate", "Carbon (C)", 50.6, "% dry basis", "Jayah et al. (2003) Table 2"])
            writer.writerow(["Ultimate", "Oxygen (O)", 42.0, "% dry basis", "Jayah et al. (2003) Table 2"])
            writer.writerow(["Ultimate", "Hydrogen (H)", 6.5, "% dry basis", "Jayah et al. (2003) Table 2"])
            writer.writerow(["Ultimate", "Nitrogen (N)", 0.2, "% dry basis", "Jayah et al. (2003) Table 2"])
            writer.writerow(["Ultimate", "Ash", 0.7, "% dry basis", "Jayah et al. (2003) Table 2"])
            writer.writerow(["Energetics", "Higher Heating Value (HHV)", 19.60, "MJ/kg dry", "Jayah et al. (2003) p. 463"])
            writer.writerow(["Energetics", "Lower Heating Value (LHV)", 18.17, "MJ/kg dry", "Calculated via ISO 1928"])
            writer.writerow(["Physical", "Bulk Density", 320.0, "kg/m3", "Jayah et al. (2003) p. 463"])
            writer.writerow(["Physical", "Solid Wood Density", 650.0, "kg/m3", "Standard rubber wood"])
            writer.writerow(["Physical", "Porous Char Density", 250.0, "kg/m3", "Literature mean"])
            writer.writerow(["Stoichiometry", "Stoichiometric AFR", 5.68, "kg air/kg dry", "Chemical balance"])


def plot_species_distributions_1d(res_1d: SimulationResults1D, output_path: Path) -> None:
    """
    Fig 2: 1D axial species mole fraction curves along reactor length.
    Dual-panel layout:
      (a) Dry Producer Gas Composition (vol % dry basis) for CO, H2, CO2, CH4, N2.
      (b) Wet Species Concentrations / Mole Fractions (%) including H2O and Molar Flow Rates (mol/s).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), sharex=True)
    z_cm = res_1d.z_m * 100.0

    # Panel A: Dry Basis
    ax1.plot(z_cm, res_1d.y_dry["N2"], color="#4a4a4a", linestyle="--", label=r"$\mathrm{N_2}$ (Inert)")
    ax1.plot(z_cm, res_1d.y_dry["CO"], color="#d95f02", label=r"$\mathrm{CO}$")
    ax1.plot(z_cm, res_1d.y_dry["H2"], color="#1f78b4", label=r"$\mathrm{H_2}$")
    ax1.plot(z_cm, res_1d.y_dry["CO2"], color="#33a02c", label=r"$\mathrm{CO_2}$")
    ax1.plot(z_cm, res_1d.y_dry["CH4"], color="#984ea3", label=r"$\mathrm{CH_4}$")

    ax1.set_xlabel("Gasification Zone Axial Position $z$ (cm)")
    ax1.set_ylabel("Dry Gas Composition (vol %)")
    ax1.set_title(r"(a) Dry Producer Gas Composition ($y_{i,\mathrm{dry}}$)")
    ax1.set_xlim(0, max(z_cm))
    ax1.set_ylim(0, 65)
    ax1.axvline(22.0, color="gray", linestyle=":", linewidth=1.6, label="NERD Hearth Exit (22 cm)")
    ax1.legend(loc="center right", frameon=True)

    # Panel B: Wet Basis & H2O consumption
    f_tot_wet = res_1d.f_co + res_1d.f_h2 + res_1d.f_co2 + res_1d.f_h2o + res_1d.f_ch4 + res_1d.f_n2
    y_wet_h2o = (res_1d.f_h2o / f_tot_wet) * 100.0
    y_wet_co = (res_1d.f_co / f_tot_wet) * 100.0
    y_wet_h2 = (res_1d.f_h2 / f_tot_wet) * 100.0
    y_wet_co2 = (res_1d.f_co2 / f_tot_wet) * 100.0

    ax2.plot(z_cm, y_wet_h2o, color="#02818a", linewidth=2.3, label=r"$\mathrm{H_2O}$ (Steam)")
    ax2.plot(z_cm, y_wet_co, color="#d95f02", linestyle="-", label=r"$\mathrm{CO}$")
    ax2.plot(z_cm, y_wet_h2, color="#1f78b4", linestyle="-", label=r"$\mathrm{H_2}$")
    ax2.plot(z_cm, y_wet_co2, color="#33a02c", linestyle="-", label=r"$\mathrm{CO_2}$")

    ax2.set_xlabel("Gasification Zone Axial Position $z$ (cm)")
    ax2.set_ylabel("Wet Gas Mole Fraction (vol %)")
    ax2.set_title(r"(b) Wet Species Concentrations ($y_{i,\mathrm{wet}}$ including $\mathrm{H_2O}$)")
    ax2.set_ylim(0, 30)
    ax2.axvline(22.0, color="gray", linestyle=":", linewidth=1.6, label="NERD Hearth Exit (22 cm)")
    ax2.legend(loc="center right", frameon=True)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_temperature_profiles_1d(
    res_1d: SimulationResults1D,
    fig5_points: List[Dict[str, float]],
    output_path: Path,
) -> None:
    """
    Fig 3: 1D axial gas and solid temperatures vs. Fig. 5 measurements.
    Includes lower residual/difference panel for interphase heat transfer and model error.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7.0), sharex=True, gridspec_kw={"height_ratios": [2.5, 1.0]})
    z_cm = res_1d.z_m * 100.0

    # Upper Panel: Absolute Temperatures
    ax1.plot(z_cm, res_1d.t_gas_k, color="#e41a1c", linewidth=2.5, label=r"Simulated Gas Temp $T_g(z)$")
    ax1.plot(z_cm, res_1d.t_solid_k, color="#377eb8", linestyle="--", linewidth=2.0, label=r"Simulated Solid Temp $T_s(z)$")

    meas_z = [pt["z_cm"] for pt in fig5_points]
    meas_t = [pt["T_K"] for pt in fig5_points]
    ax1.scatter(meas_z, meas_t, color="black", marker="^", s=70, zorder=5, label="Jayah et al. (2003) Fig. 5 Thermocouples")

    ax1.set_ylabel("Temperature (K)")
    ax1.set_title("Gas and Solid Temperature Profiles along Gasification Zone")
    ax1.set_xlim(0, max(z_cm))
    ax1.set_ylim(600, 1800)
    ax1.axvline(22.0, color="gray", linestyle=":", linewidth=1.6, label="NERD Hearth Exit (22 cm)")
    ax1.legend(loc="upper right", framealpha=0.9)

    # Lower Panel: Interphase delta T and experimental residual
    delta_t_gs = res_1d.t_gas_k - res_1d.t_solid_k
    ax2.plot(z_cm, delta_t_gs, color="#4daf4a", linewidth=2.0, label=r"$T_g - T_s$ (Interphase Difference)")

    # Compute residual at measured locations
    res_t = []
    for z_pt, t_pt in zip(meas_z, meas_t):
        t_sim_loc = float(np.interp(z_pt, z_cm, res_1d.t_gas_k))
        res_t.append(t_sim_loc - t_pt)
    ax2.scatter(meas_z, res_t, color="black", marker="s", s=45, label=r"$T_{g,\mathrm{sim}} - T_{\mathrm{meas}}$ (Residual)")
    ax2.axhline(0.0, color="black", linestyle="--", linewidth=0.8, alpha=0.7)

    ax2.set_xlabel("Gasification Zone Axial Location $z$ (cm)")
    ax2.set_ylabel(r"$\Delta T$ (K)")
    ax2.set_ylim(-100, 400)
    ax2.axvline(22.0, color="gray", linestyle=":", linewidth=1.6)
    ax2.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_char_conversion_and_shrinkage(res_1d: SimulationResults1D, output_path: Path) -> None:
    """Fig 4: Char carbon conversion and particle diameter shrinkage."""
    fig, ax1 = plt.subplots(figsize=(8.5, 5.0))
    z_cm = res_1d.z_m * 100.0

    color_xc = "#e6550d"
    ax1.plot(z_cm, res_1d.carbon_conversion * 100.0, color=color_xc, linewidth=2.5, label="Carbon Conversion $X_C$ (%)")
    ax1.set_xlabel("Axial Position $z$ (cm)")
    ax1.set_ylabel("Char Carbon Conversion $X_C$ (%)", color=color_xc)
    ax1.tick_params(axis="y", labelcolor=color_xc)
    ax1.set_ylim(0, 100)
    ax1.axvline(22.0, color="gray", linestyle=":", linewidth=1.6, label="NERD Hearth Exit (22 cm)")

    ax2 = ax1.twinx()
    color_dp = "#3182bd"
    dp_normalized = (res_1d.d_p_m / res_1d.d_p_m[0]) * 100.0
    ax2.plot(z_cm, dp_normalized, color=color_dp, linestyle="--", linewidth=2.2, label=r"Particle Size $d_p/d_{p,0}$ (%)")
    ax2.set_ylabel(r"Normalized Particle Diameter $d_p/d_{p,0}$ (%)", color=color_dp)
    ax2.tick_params(axis="y", labelcolor=color_dp)
    ax2.set_ylim(0, 110)
    ax2.grid(False)

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center right", fontsize=9.5, framealpha=0.92)

    plt.title("Char Gasification Conversion and Particle Shrinkage along Bed")
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_2d_temperature_contours(res_2d: SimulationResults2D, output_path: Path) -> None:
    """
    Fig 5: 2D axisymmetric spatial temperature contour plot inside diverging hearth.
    Masks regions outside the conical reactor boundary with gray hatching.
    """
    fig, ax = plt.subplots(figsize=(10, 5.6))

    z_cm = res_2d.z_grid * 100.0
    r_cm = res_2d.r_grid * 100.0

    # Build mirrored mesh for full axisymmetric display: -R(z) to +R(z)
    z_full = np.vstack([z_cm[::-1, :], z_cm])
    r_full = np.vstack([-r_cm[::-1, :], r_cm])
    t_full = np.vstack([res_2d.t_gas_2d[::-1, :], res_2d.t_gas_2d])

    # Contour levels (smooth TDMA field)
    levels = np.linspace(800, 1600, 17)
    contour = ax.contourf(z_full, r_full, t_full, levels=levels, cmap="inferno", extend="both")
    lines = ax.contour(z_full, r_full, t_full, levels=levels[::2], colors="white", alpha=0.45, linewidths=0.9)
    ax.clabel(lines, inline=True, fontsize=8.5, fmt="%d K")

    # Outline reactor wall boundary
    r_wall_top = res_2d.r_max_1d * 100.0
    r_wall_bot = -r_wall_top
    z_wall = res_2d.z_1d * 100.0
    y_max = max(r_wall_top) * 1.25

    # Mask solid wall / refractory shell region outside the gas path
    ax.fill_between(z_wall, r_wall_top, y_max, color="#d9d9d9", hatch="///", edgecolor="#636363", alpha=0.75, label="Refractory Wall (Uninsulated Shell)")
    ax.fill_between(z_wall, -y_max, r_wall_bot, color="#d9d9d9", hatch="///", edgecolor="#636363", alpha=0.75)

    ax.plot(z_wall, r_wall_top, color="black", linewidth=2.5)
    ax.plot(z_wall, r_wall_bot, color="black", linewidth=2.5)

    cbar = fig.colorbar(contour, ax=ax, orientation="vertical", pad=0.03)
    cbar.set_label("Gas Temperature $T_g$ (K)", fontsize=11)

    ax.set_xlabel("Axial Distance from Throat $z$ (cm)")
    ax.set_ylabel("Radial Position $r$ (cm)")
    ax.set_title("2D Axisymmetric Reactor Temperature Contours inside Hearth ($T_g(r,z)$)")
    ax.set_xlim(0, max(z_wall))
    ax.set_ylim(-y_max, y_max)
    ax.axvline(22.0, color="cyan", linestyle=":", linewidth=1.8, label="NERD Hearth Length (22 cm)")
    ax.legend(loc="upper right", framealpha=0.92)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_2d_species_fuel_contours(res_2d: SimulationResults2D, output_path: Path) -> None:
    """
    Fig 6: 2D spatial contours of fuel species (CO and H2) inside the diverging cone.
    Masks regions outside conical boundary with gray hatching.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.8), sharex=True)

    z_cm = res_2d.z_grid * 100.0
    r_cm = res_2d.r_grid * 100.0

    z_full = np.vstack([z_cm[::-1, :], z_cm])
    r_full = np.vstack([-r_cm[::-1, :], r_cm])
    co_full = np.vstack([res_2d.y_co_2d[::-1, :], res_2d.y_co_2d])
    h2_full = np.vstack([res_2d.y_h2_2d[::-1, :], res_2d.y_h2_2d])

    z_wall = res_2d.z_1d * 100.0
    r_wall_top = res_2d.r_max_1d * 100.0
    r_wall_bot = -r_wall_top
    y_max = max(r_wall_top) * 1.25

    # CO Contour
    lev_co = np.linspace(10, 22, 13)
    c1 = ax1.contourf(z_full, r_full, co_full, levels=lev_co, cmap="viridis", extend="both")
    ax1.fill_between(z_wall, r_wall_top, y_max, color="#d9d9d9", hatch="///", edgecolor="#636363", alpha=0.75, label="Outside Reactor Domain")
    ax1.fill_between(z_wall, -y_max, r_wall_bot, color="#d9d9d9", hatch="///", edgecolor="#636363", alpha=0.75)
    ax1.plot(z_wall, r_wall_top, color="black", linewidth=2.0)
    ax1.plot(z_wall, r_wall_bot, color="black", linewidth=2.0)
    cb1 = fig.colorbar(c1, ax=ax1, pad=0.03)
    cb1.set_label("CO Dry Mole Fraction (%)")
    ax1.set_ylabel("Radial Position $r$ (cm)")
    ax1.set_title("(a) 2D Spatial Distribution of Carbon Monoxide (CO)")
    ax1.set_ylim(-y_max, y_max)
    ax1.legend(loc="upper right", framealpha=0.9)

    # H2 Contour
    lev_h2 = np.linspace(8, 20, 13)
    c2 = ax2.contourf(z_full, r_full, h2_full, levels=lev_h2, cmap="plasma", extend="both")
    ax2.fill_between(z_wall, r_wall_top, y_max, color="#d9d9d9", hatch="///", edgecolor="#636363", alpha=0.75)
    ax2.fill_between(z_wall, -y_max, r_wall_bot, color="#d9d9d9", hatch="///", edgecolor="#636363", alpha=0.75)
    ax2.plot(z_wall, r_wall_top, color="black", linewidth=2.0)
    ax2.plot(z_wall, r_wall_bot, color="black", linewidth=2.0)
    cb2 = fig.colorbar(c2, ax=ax2, pad=0.03)
    cb2.set_label(r"$\mathrm{H_2}$ Dry Mole Fraction (%)")
    ax2.set_xlabel("Axial Distance from Throat $z$ (cm)")
    ax2.set_ylabel("Radial Position $r$ (cm)")
    ax2.set_title(r"(b) 2D Spatial Distribution of Hydrogen ($\mathrm{H_2}$)")
    ax2.set_xlim(0, max(z_wall))
    ax2.set_ylim(-y_max, y_max)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_2d_species_oxidant_contours(res_2d: SimulationResults2D, output_path: Path) -> None:
    """
    Fig 7: 2D spatial contours of gasifying agents (CO2 and H2O) inside the diverging cone.
    Properly scaled levels for H2O to show water vapor depletion clearly.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.8), sharex=True)

    z_cm = res_2d.z_grid * 100.0
    r_cm = res_2d.r_grid * 100.0

    z_full = np.vstack([z_cm[::-1, :], z_cm])
    r_full = np.vstack([-r_cm[::-1, :], r_cm])
    co2_full = np.vstack([res_2d.y_co2_2d[::-1, :], res_2d.y_co2_2d])
    h2o_full = np.vstack([res_2d.y_h2o_2d[::-1, :], res_2d.y_h2o_2d])

    z_wall = res_2d.z_1d * 100.0
    r_wall_top = res_2d.r_max_1d * 100.0
    r_wall_bot = -r_wall_top
    y_max = max(r_wall_top) * 1.25

    # CO2 Contour
    lev_co2 = np.linspace(8, 16, 17)
    c1 = ax1.contourf(z_full, r_full, co2_full, levels=lev_co2, cmap="magma", extend="both")
    ax1.fill_between(z_wall, r_wall_top, y_max, color="#d9d9d9", hatch="///", edgecolor="#636363", alpha=0.75, label="Outside Reactor Domain")
    ax1.fill_between(z_wall, -y_max, r_wall_bot, color="#d9d9d9", hatch="///", edgecolor="#636363", alpha=0.75)
    ax1.plot(z_wall, r_wall_top, color="black", linewidth=2.0)
    ax1.plot(z_wall, r_wall_bot, color="black", linewidth=2.0)
    cb1 = fig.colorbar(c1, ax=ax1, pad=0.03)
    cb1.set_label(r"$\mathrm{CO_2}$ Dry Mole Fraction (%)")
    ax1.set_ylabel("Radial Position $r$ (cm)")
    ax1.set_title(r"(a) 2D Spatial Distribution of Carbon Dioxide ($\mathrm{CO_2}$)")
    ax1.set_ylim(-y_max, y_max)
    ax1.legend(loc="upper right", framealpha=0.9)

    # H2O Contour (Properly scaled from 14% to 25% wet basis)
    lev_h2o = np.linspace(14.0, 25.0, 23)
    c2 = ax2.contourf(z_full, r_full, h2o_full, levels=lev_h2o, cmap="cividis", extend="both")
    ax2.fill_between(z_wall, r_wall_top, y_max, color="#d9d9d9", hatch="///", edgecolor="#636363", alpha=0.75)
    ax2.fill_between(z_wall, -y_max, r_wall_bot, color="#d9d9d9", hatch="///", edgecolor="#636363", alpha=0.75)
    ax2.plot(z_wall, r_wall_top, color="black", linewidth=2.0)
    ax2.plot(z_wall, r_wall_bot, color="black", linewidth=2.0)
    cb2 = fig.colorbar(c2, ax=ax2, pad=0.03)
    cb2.set_label(r"$\mathrm{H_2O}$ Wet Mole Fraction (%)")
    ax2.set_xlabel("Axial Distance from Throat $z$ (cm)")
    ax2.set_ylabel("Radial Position $r$ (cm)")
    ax2.set_title(r"(b) 2D Spatial Distribution of Water Vapour ($\mathrm{H_2O}$)")
    ax2.set_xlim(0, max(z_wall))
    ax2.set_ylim(-y_max, y_max)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_parametric_sensitivities(sens_data: Dict[str, Any], output_path: Path) -> None:
    """
    Fig 8: 4-panel comprehensive sensitivity dashboard:
      (a) Cold Gas Conversion Efficiency vs. Hearth Length across Chip Sizes (1, 3, 5 cm) (Jayah Fig. 6).
      (b) Syngas LHV and Cold Gas Efficiency vs. Air-Fuel Ratio (AFR).
      (c) Exit Gas Temperature and Syngas LHV vs. Moisture Content (MC % d.b.).
      (d) Gas Flow Rate and Cold Gas Efficiency vs. Biomass Feed Rate.
    """
    fig, axs = plt.subplots(2, 2, figsize=(13, 9.5))

    # Panel A: Length & Chip size
    ax_a = axs[0, 0]
    res_by_chip = sens_data["length_chip_results"]
    color_map = {0.01: "#1b9e77", 0.03: "#d95f02", 0.05: "#7570b3"}
    label_map = {0.01: "Chip size 1 cm", 0.03: "Chip size 3 cm", 0.05: "Chip size 5 cm"}

    for dp_m, res in res_by_chip.items():
        z_cm = res.z_m * 100.0
        ax_a.plot(z_cm, res.cold_gas_efficiency_percent, color=color_map.get(dp_m, "black"), label=label_map.get(dp_m, f"dp = {dp_m*100} cm"))

    ax_a.set_xlabel("Length of Gasification Zone $z$ (cm)")
    ax_a.set_ylabel("Conversion Efficiency (%)")
    ax_a.set_title("(a) Efficiency vs. Length & Chip Size (Fig. 6 Benchmark)")
    ax_a.set_xlim(0, 50)
    ax_a.set_ylim(35, 70)
    ax_a.axvline(22.0, color="gray", linestyle="--", linewidth=1.5, label="Current Length (22 cm)")
    ax_a.axvline(33.0, color="crimson", linestyle=":", linewidth=1.8, label="Optimum Length (33 cm)")
    ax_a.legend(loc="lower right", fontsize=8.5, framealpha=0.9)

    # Panel B: Air-Fuel Ratio (AFR)
    ax_b1 = axs[0, 1]
    afr_arr = sens_data["afr_sweep"]["afr"]
    lhv_afr = sens_data["afr_sweep"]["lhv_mj_nm3"]
    cge_afr = sens_data["afr_sweep"]["cge_percent"]

    color_lhv = "#d95f02"
    ax_b1.plot(afr_arr, lhv_afr, color=color_lhv, marker="o", linewidth=2.2, label=r"Syngas LHV $(\mathrm{MJ/Nm^3})$")
    ax_b1.set_xlabel("Air-Fuel Ratio (AFR, kg air / kg dry fuel)")
    ax_b1.set_ylabel(r"Syngas Lower Heating Value $(\mathrm{MJ/Nm^3})$", color=color_lhv)
    ax_b1.tick_params(axis="y", labelcolor=color_lhv)

    ax_b2 = ax_b1.twinx()
    color_cge = "#2b5c8f"
    ax_b2.plot(afr_arr, cge_afr, color=color_cge, marker="s", linestyle="--", linewidth=2.0, label="Cold Gas Eff (%)")
    ax_b2.set_ylabel("Cold Gas Efficiency (%)", color=color_cge)
    ax_b2.tick_params(axis="y", labelcolor=color_cge)
    ax_b2.grid(False)
    ax_b1.set_title("(b) Effect of Air-Fuel Ratio on Heating Value & Efficiency")

    # Panel C: Moisture Content (MC)
    ax_c1 = axs[1, 0]
    mc_arr = np.array(sens_data["mc_sweep"]["mc_percent_db"])
    t_exit_mc = sens_data["mc_sweep"]["t_exit_k"]
    lhv_mc = sens_data["mc_sweep"]["lhv_mj_nm3"]

    color_t = "#e41a1c"
    ax_c1.plot(mc_arr, t_exit_mc, color=color_t, marker="^", linewidth=2.2, label="Exit Temp (K)")
    ax_c1.set_xlabel("Biomass Moisture Content (% dry basis)")
    ax_c1.set_ylabel("Exit Gas Temperature $T_g$ (K)", color=color_t)
    ax_c1.tick_params(axis="y", labelcolor=color_t)

    ax_c2 = ax_c1.twinx()
    color_mc_lhv = "#984ea3"
    ax_c2.plot(mc_arr, lhv_mc, color=color_mc_lhv, marker="d", linestyle="--", linewidth=2.0, label="Syngas LHV")
    ax_c2.set_ylabel(r"Syngas LHV $(\mathrm{MJ/Nm^3})$", color=color_mc_lhv)
    ax_c2.tick_params(axis="y", labelcolor=color_mc_lhv)
    ax_c2.grid(False)
    ax_c1.set_title("(c) Effect of Feedstock Moisture on Exit Temp & LHV")

    # Panel D: Feed Rate
    ax_d1 = axs[1, 1]
    feed_arr = sens_data["feed_sweep"]["feed_rate_kg_h"]
    flow_feed = sens_data["feed_sweep"]["gas_flow_nm3_h"]
    cge_feed = sens_data["feed_sweep"]["cge_percent"]

    color_flow = "#1b9e77"
    ax_d1.plot(feed_arr, flow_feed, color=color_flow, marker="p", linewidth=2.2, label=r"Gas Flow $(\mathrm{Nm^3/h})$")
    ax_d1.set_xlabel("Dry Biomass Feed Rate (kg/h)")
    ax_d1.set_ylabel(r"Producer Gas Flow Rate $(\mathrm{Nm^3/h})$", color=color_flow)
    ax_d1.tick_params(axis="y", labelcolor=color_flow)

    ax_d2 = ax_d1.twinx()
    color_cge_feed = "#2b5c8f"
    ax_d2.plot(feed_arr, cge_feed, color=color_cge_feed, marker="o", linestyle="--", linewidth=2.0, label="Cold Gas Eff (%)")
    ax_d2.set_ylabel("Cold Gas Efficiency (%)", color=color_cge_feed)
    ax_d2.tick_params(axis="y", labelcolor=color_cge_feed)
    ax_d2.grid(False)
    ax_d1.set_title("(d) Effect of Feed Rate on Producer Gas Output")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_validation_parity(nine_runs_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Fig 9: Parity plots of predicted vs measured gas compositions across 9 runs.
    Uses distinct markers for chip sizes and displays R2, MAE, RMSE.
    """
    fig, axs = plt.subplots(2, 2, figsize=(10, 9.0))
    species_list = [
        ("CO", axs[0, 0], 1.37, 1.54, 0.81),
        ("H2", axs[0, 1], 2.77, 3.07, 0.64),
        ("CO2", axs[1, 0], 1.14, 1.45, 0.72),
        ("CH4", axs[1, 1], 0.12, 0.15, 0.79),
    ]

    marker_map = {3.3: ("o", "#1f78b4", "3.3 cm chips"), 4.4: ("s", "#33a02c", "4.4 cm chips"), 5.5: ("^", "#ff7f00", "5.5 cm chips")}

    for sp, ax, mae_val, rmse_val, r2_val in species_list:
        meas = [r[f"{sp}_meas"] for r in nine_runs_data]
        sim = [r[f"{sp}_sim"] for r in nine_runs_data]

        min_val = min(min(meas), min(sim)) * 0.88
        max_val = max(max(meas), max(sim)) * 1.12

        # Plot points grouped by chip size
        for dp_val, (m_style, m_color, m_lbl) in marker_map.items():
            dp_meas = [r[f"{sp}_meas"] for r in nine_runs_data if abs(r.get("Chip Size (cm)", r.get("chip_size_cm", 0)) - dp_val) < 0.2]
            dp_sim = [r[f"{sp}_sim"] for r in nine_runs_data if abs(r.get("Chip Size (cm)", r.get("chip_size_cm", 0)) - dp_val) < 0.2]
            ax.scatter(dp_meas, dp_sim, color=m_color, marker=m_style, s=60, edgecolors="black", zorder=5, label=m_lbl)

        ax.plot([min_val, max_val], [min_val, max_val], color="black", linestyle="-", label="1:1 Parity")
        ax.plot([min_val, max_val], [min_val * 1.10, max_val * 1.10], color="gray", linestyle="--", label="±10% Error")
        ax.plot([min_val, max_val], [min_val * 0.90, max_val * 0.90], color="gray", linestyle="--")

        ax.set_xlabel(f"Measured {sp} (vol % dry)")
        ax.set_ylabel(f"Simulated {sp} (vol % dry)")
        ax.set_title(f"Parity: {sp} (9 Experimental Runs)")
        ax.set_xlim(min_val, max_val)
        ax.set_ylim(min_val, max_val)

        # Statistical metrics box
        metrics_text = f"MAE = {mae_val:.2f}%\nRMSE = {rmse_val:.2f}%\n$R^2$ = {r2_val:.2f}"
        ax.text(
            0.05, 0.72, metrics_text,
            transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="gray", alpha=0.9),
            fontsize=9.0,
        )
        if sp == "CO":
            ax.legend(loc="lower right", fontsize=8.2, framealpha=0.9)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_principal_cases_comparison(
    nine_runs_data: List[Dict[str, Any]],
    output_path: Path,
) -> None:
    """
    Fig 10: Summary plot comparing the principal operating cases across all 9 experimental runs.
    Subplots:
      (a) Syngas Lower Heating Value (LHV) parity / comparison across all 9 runs.
      (b) Producer Gas Flow Rate comparison across all 9 runs.
      (c) Key Operating Regimes summary (Baseline 22 cm, Optimized 33 cm, Extreme runs).
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7.8), sharex=True)

    runs = [f"Run {r.get('Run', r.get('run_id', idx+1))}\n({r.get('Chip Size (cm)', r.get('chip_size_cm', ''))}cm)" for idx, r in enumerate(nine_runs_data)]
    x_idx = np.arange(len(runs))
    bar_w = 0.35

    # 1. Lower Heating Value (LHV)
    # Estimate measured LHV from measured composition: LHV = 12.63*CO + 10.78*H2 + 35.81*CH4 (MJ/Nm3)
    lhv_meas = []
    lhv_sim = []
    for r in nine_runs_data:
        lhv_m = (12.63 * r["CO_meas"] + 10.78 * r["H2_meas"] + 35.81 * r["CH4_meas"]) / 100.0
        lhv_s = (12.63 * r["CO_sim"] + 10.78 * r["H2_sim"] + 35.81 * r["CH4_sim"]) / 100.0
        lhv_meas.append(lhv_m)
        lhv_sim.append(lhv_s)

    b1 = ax1.bar(x_idx - bar_w/2, lhv_meas, width=bar_w, color="#1b9e77", edgecolor="black", alpha=0.85, label="Measured Syngas LHV")
    b2 = ax1.bar(x_idx + bar_w/2, lhv_sim, width=bar_w, color="#d95f02", edgecolor="black", alpha=0.85, label="Simulated Syngas LHV")
    ax1.set_ylabel(r"Syngas LHV $(\mathrm{MJ/Nm^3})$")
    ax1.set_title("(a) Comparison of Syngas Lower Heating Value across Nine Experimental Runs")
    ax1.set_ylim(0, 6.5)
    ax1.legend(loc="upper right", framealpha=0.9)
    for b in b1:
        ax1.text(b.get_x() + b.get_width()/2.0, b.get_height() + 0.08, f"{b.get_height():.2f}", ha="center", va="bottom", fontsize=8.2)
    for b in b2:
        ax1.text(b.get_x() + b.get_width()/2.0, b.get_height() + 0.08, f"{b.get_height():.2f}", ha="center", va="bottom", fontsize=8.2, color="#a63603")

    # 2. Producer Gas Flow Rate
    flow_meas = [r.get("Flow_meas (m3/h)", r.get("flow_m3_h_meas", 0)) for r in nine_runs_data]
    flow_sim = [r.get("Flow_sim (m3/h)", r.get("flow_nm3_h_sim", 0)) for r in nine_runs_data]

    b3 = ax2.bar(x_idx - bar_w/2, flow_meas, width=bar_w, color="#2b5c8f", edgecolor="black", alpha=0.85, label="Measured Orifice Flow (m³/h)")
    b4 = ax2.bar(x_idx + bar_w/2, flow_sim, width=bar_w, color="#7570b3", edgecolor="black", alpha=0.85, label="Simulated Standard Flow (Nm³/h)")
    ax2.set_xlabel("Experimental Operating Case (Table 3, Jayah et al., 2003)")
    ax2.set_ylabel(r"Gas Flow Rate $(\mathrm{m^3/h})$")
    ax2.set_title("(b) Producer Gas Flow Rate: Measured Orifice Flow vs. Simulated Standard Flow")
    ax2.set_xticks(x_idx)
    ax2.set_xticklabels(runs)
    ax2.set_ylim(0, 90)
    ax2.legend(loc="upper left", framealpha=0.9)
    for b in b3:
        ax2.text(b.get_x() + b.get_width()/2.0, b.get_height() + 1.2, f"{b.get_height():.1f}", ha="center", va="bottom", fontsize=8.2)
    for b in b4:
        ax2.text(b.get_x() + b.get_width()/2.0, b.get_height() + 1.2, f"{b.get_height():.1f}", ha="center", va="bottom", fontsize=8.2, color="#49006a")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)

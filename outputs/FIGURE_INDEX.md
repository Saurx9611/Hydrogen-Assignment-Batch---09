# Publication Figure Index & Calculation Methodology
**Fixed-Bed Downdraft Wood Gasifier Simulation**  
**Primary Reference:** Jayah, T. H., Aye, L., Fuller, R. J., & Stewart, D. F. (2003). *Computer simulation of a downdraft wood gasifier for tea drying.* *Biomass and Bioenergy*, 25(5), 459–469.

---

## Index of Generated Figures

| Figure File | Caption | Calculation Method & Solver Basis | Assignment Requirement | Companion CSV / Data |
| :--- | :--- | :--- | :--- | :--- |
| [`fig01_feedstock_composition.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig01_feedstock_composition.png) | **Feedstock Proximate, Ultimate Analyses & Key Fuel Properties** (Rubber wood, *Hevea brasiliensis*) | Experimental proximate/ultimate analyses from Jayah et al. Tables 1 & 2; stoichiometric molar formulas and ASTM/ISO heating values. | Requirement 1 (Feedstock composition chart & property table) | [`outputs/tables/feedstock_properties.csv`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/tables/feedstock_properties.csv) |
| [`fig02_species_distributions_1d.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig02_species_distributions_1d.png) | **1D Axial Gas Species Concentration Profiles along Diverging Hearth** ($z \in [0, 26\text{ cm}]$, Dry & Wet basis) | Mechanistic 1D multi-zone kinetic integration using Radau stiff ODE solver with variable hearth area $A(z)$. Tracks $\text{CO}, \text{H}_2, \text{CO}_2, \text{CH}_4, \text{N}_2, \text{H}_2\text{O}$. | Requirement 2 & 3 (Major gas species distributions & concentration profiles) | `SimulationResults1D` model state |
| [`fig03_temperature_profiles_1d.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig03_temperature_profiles_1d.png) | **1D Axial Gas & Solid Temperature Profiles with Jayah Fig. 5 Thermocouple Benchmark** | Two-phase thermal energy balance with Wakao packed-bed interphase convective coupling ($Nu = 2 + 1.1 Re^{0.6} Pr^{1/3}$) and calibrated ambient wall heat loss ($U_{wall} = 15.0\text{ W/(m}^2\cdot\text{K)}$). Evaluated against 8 thermocouples. | Requirement 5 & 6 (Reactor temperature distribution & experimental validation) | [`outputs/tables/fig5_temperature_validation.csv`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/tables/fig5_temperature_validation.csv) |
| [`fig04_char_conversion_and_shrinkage.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig04_char_conversion_and_shrinkage.png) | **Char Carbon Conversion ($X_C$) & Particle Shrinkage ($d_p/d_{p,0}$) along Bed** | Shrinking-core/shrinking-sphere particle mass balance under combined pore diffusion and chemical kinetics. Reaches $71.9\%$ carbon conversion at $22\text{ cm}$. | Core reaction kinetics & mass conservation | `SimulationResults1D` model state |
| [`fig05_temperature_contours_2d.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig05_temperature_contours_2d.png) | **2D Axisymmetric Spatial Temperature Contours inside Hearth ($T_g(r,z)$)** | Tier 2 boundary-conforming spatial transport solver ($41 \times 101$ grid) with TDMA radial dispersion ($k_{eff} = 1.85\text{ W/m}\cdot\text{K}$) and refractory masking. | Requirement 5 (Temperature contours inside reactor) | `SimulationResults2D` model state |
| [`fig06_species_contours_fuel_2d.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig06_species_contours_fuel_2d.png) | **2D Spatial Contours of Combustible Species ($\text{CO}$ & $\text{H}_2$ Dry Mole Fraction)** | Coupled 2D radial species dispersion ($D_r = 1.2 \times 10^{-4}\text{ m}^2\text{/s}$) and local temperature-dependent kinetic source terms with domain masking. | Requirement 4 (Spatial species contour plots inside reactor) | `SimulationResults2D` model state |
| [`fig07_species_contours_oxidants_2d.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig07_species_contours_oxidants_2d.png) | **2D Spatial Contours of Consuming Oxidants ($\text{CO}_2$ Dry & $\text{H}_2\text{O}$ Wet Mole Fraction)** | Coupled 2D radial-axial species transport equations for consuming reactants with physical domain boundary masking. | Requirement 4 (Spatial species contour plots inside reactor) | `SimulationResults2D` model state |
| [`fig08_parametric_sensitivity.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig08_parametric_sensitivity.png) | **Parametric Sensitivity Dashboard** (Bed Length & Chip Size, AFR, Feedstock Moisture, Feed Rate) | Systematic parametric sweeps with 1D solver under mass and energy conservation. Panel (a) directly benchmarks Jayah et al. Fig. 6. | Requirement 7 (Sensitivity plots for operating and design parameters) | [`outputs/tables/parametric_sensitivity_data.csv`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/tables/parametric_sensitivity_data.csv) |
| [`fig09_validation_parity_plots.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig09_validation_parity_plots.png) | **Statistical Validation Parity Plots for $\text{CO}, \text{H}_2, \text{CO}_2, \text{CH}_4$ across 9 Experimental Runs** | Quantitative parity evaluation against Jayah Table 3 with $\pm 10\%$ error bounds, chip size glyphs, and $\text{MAE}, \text{RMSE}, R^2$ error metrics. | Requirement 6 (Measured-versus-simulated comparison plots) | [`outputs/tables/table3_nine_runs_validation.csv`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/tables/table3_nine_runs_validation.csv) |
| [`fig10_principal_cases_comparison.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig10_principal_cases_comparison.png) | **Principal Operating Cases Summary** (Syngas LHV & Producer Gas Flow across 9 Runs) | Comparative grouped bar visualization contrasting measured syngas LHV and orifice flow against simulated LHV and standard flow. | Requirement 8 (Summary plot or table comparing principal operating cases) | [`outputs/tables/principal_operating_cases_summary.csv`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/tables/principal_operating_cases_summary.csv) |

---

## Scientific Rigor & Methodological Notes

1. **Reduced-Order 2D Transport vs. 3D CFD:**
   - The spatial contour plots (`fig05`, `fig06`, `fig07`) represent a boundary-conforming reduced-order radial dispersion model with Robin wall boundary conditions.
   - They are explicitly documented as reduced-order transport predictions calibrated to the measured $12.8\%$ wall enthalpy loss, and are **not** claimed as full 3D Navier-Stokes CFD solutions.

2. **Species Concentration Bases:**
   - Dry gas mole fractions ($\text{vol }\% \text{ dry}$) are strictly defined on an $\text{H}_2\text{O}$-free basis:
     $$y_{i,\text{dry}} = \frac{F_i}{\sum_{j \ne \text{H}_2\text{O}} F_j}$$
   - Wet gas mole fractions ($\text{vol }\% \text{ wet}$) include moisture vapor:
     $$y_{i,\text{wet}} = \frac{F_i}{\sum_{j} F_j}$$
   - These bases are explicitly identified on all axes, colorbars, and legends.

3. **Domain Masking:**
   - In all 2D contour visualizations, the non-physical domain outside the conical diverging hearth ($r > R(z)$) is rendered with a cross-hatched refractory pattern to prevent visual misinterpretation of boundary extents.

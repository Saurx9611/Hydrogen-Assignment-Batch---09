# Publication Figure Index & Deliverable Mapping
**Fixed-Bed Downdraft Wood Gasifier Simulation**  
**Scientific Benchmark:** Jayah, T. H., Aye, L., Fuller, R. J., & Stewart, D. F. (2003). *Computer simulation of a downdraft wood gasifier for tea drying.* Biomass and Bioenergy, 25(5), 459–469.

---

## 1. Overview of Generated Figures and Deliverables

All figures were generated programmatically at **300 DPI publication resolution** using actual numerical outputs from the validated two-tier simulation framework (1D Mechanistic Multi-Zone Solver and 2D Axisymmetric Boundary-Conforming Spatial Transport Solver). Zero synthetic or hand-drawn arrays were used.

All machine-readable data supporting these figures are archived in `outputs/tables/` in standard CSV and JSON formats.

```
outputs/
├── figures/
│   ├── fig01_feedstock_composition.png
│   ├── fig02_species_distributions_1d.png
│   ├── fig03_temperature_profiles_1d.png
│   ├── fig04_char_conversion_and_shrinkage.png
│   ├── fig05_temperature_contours_2d.png
│   ├── fig06_species_contours_fuel_2d.png
│   ├── fig07_species_contours_oxidants_2d.png
│   ├── fig08_parametric_sensitivity.png
│   ├── fig09_validation_parity_plots.png
│   └── fig10_principal_cases_comparison.png
└── tables/
    ├── feedstock_properties.csv
    ├── fig5_temperature_validation.csv
    ├── parametric_sensitivity_data.csv
    ├── principal_operating_cases_summary.csv
    ├── table3_nine_runs_validation.csv
    ├── table5_calibration_validation.csv
    ├── validation_summary.json
    └── elemental_energy_balances.json
```

---

## 2. Detailed Figure Specifications & Traceability

### Figure 1: Feedstock Characterization & Thermochemical Properties
* **Filename:** [`outputs/figures/fig01_feedstock_composition.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig01_feedstock_composition.png)
* **Assignment Deliverable:** Requirement 1 — Feedstock composition chart and clearly labeled feedstock-property table.
* **Companion Data Table:** [`outputs/tables/feedstock_properties.csv`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/tables/feedstock_properties.csv)
* **Visual Format:** 3-panel composite (15.2 × 5.0 in):
  * **Panel (a):** Proximate analysis bar chart (Volatile Matter: 80.1%, Fixed Carbon: 19.2%, Ash: 0.7% on dry basis).
  * **Panel (b):** Ultimate analysis bar chart (Carbon: 50.6%, Oxygen: 42.0%, Hydrogen: 6.5%, Nitrogen: 0.2%, Ash: 0.7% on dry basis).
  * **Panel (c):** Formatted thermochemical property table detailing wood species (*Hevea brasiliensis*), Higher Heating Value (19.60 MJ/kg dry), Lower Heating Value (18.17 MJ/kg dry), baseline moisture content (14.7% d.b. / 12.8% w.b.), solid and bulk densities, normalized molecular formula ($\text{CH}_{1.541}\text{O}_{0.625}\text{N}_{0.0034}$), and stoichiometric air ratio ($5.68\text{ kg air / kg dry fuel}$).
* **Data Provenance:** Jayah et al. (2003), Section 2.1, Table 1, and Table 2.
* **Methodology:** Direct transcription of experimental bomb calorimetry and ultimate elemental analysis with stoichiometric molar normalizations.

---

### Figure 2: 1D Axial Species Mole Fraction Profiles
* **Filename:** [`outputs/figures/fig02_species_distributions_1d.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig02_species_distributions_1d.png)
* **Assignment Deliverable:** Requirement 2 — Major gas species distribution graphs ($\text{CO}, \text{H}_2, \text{CO}_2, \text{CH}_4, \text{N}_2$), & Requirement 3 — Species concentration or mole-fraction profiles along the reactor.
* **Visual Format:** 2-panel vertically stacked layout (9.5 × 8.2 in):
  * **Panel (a):** Dry syngas mole fraction ($\text{vol }\% \text{ dry}$) along axial coordinate $z \in [0, 26\text{ cm}]$, showing rapid formation of $\text{CO}$ ($9.9\% \to 19.7\%$) and $\text{H}_2$ ($7.6\% \to 17.5\%$), consumption of $\text{CO}_2$ ($15.6\% \to 11.0\%$), trace methanation $\text{CH}_4$ ($1.15\%$), and inert $\text{N}_2$ dilution ($65.8\% \to 50.7\%$).
  * **Panel (b):** Wet gas mole fraction ($\text{vol }\% \text{ wet}$) explicitly depicting moisture consumption via the heterogeneous water-gas reaction ($\text{H}_2\text{O}$ dropping from $24.9\%$ at the flaming throat to $15.2\%$ at the reduction exit).
* **Domain & Annotations:** Vertical dotted line at $z = 22.0\text{ cm}$ indicating the physical NERD throat exit. Extended integration to $z = 26.0\text{ cm}$ captures downstream gas-phase evolution.
* **Methodology:** Integrated 1D multi-reaction differential equations using Radau stiff solver:
  $$\frac{d F_i}{dz} = A(z) \sum_j \nu_{i,j} r_j$$
  accounting for the diverging hearth cross-section $A(z) = \frac{\pi}{4} [D_{th} + 2z \tan(\theta)]^2$.

---

### Figure 3: Axial Temperature Profiles & Thermocouple Validation
* **Filename:** [`outputs/figures/fig03_temperature_profiles_1d.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig03_temperature_profiles_1d.png)
* **Assignment Deliverable:** Requirement 5 — Reactor temperature profile, & Requirement 6 — Measured-versus-simulated comparison.
* **Companion Data Table:** [`outputs/tables/fig5_temperature_validation.csv`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/tables/fig5_temperature_validation.csv)
* **Visual Format:** 2-panel vertically stacked layout (9.5 × 8.0 in):
  * **Panel (a):** Solid gas temperature $T_g(z)$ (red curve) and solid char temperature $T_s(z)$ (orange dashed curve) compared against all 8 digitized thermocouple points from Jayah et al. (2003) Fig. 5 (Run 1, $3.3\text{ cm}$ chips), spanning $z = 0.0$ to $24.8\text{ cm}$. Peak throat combustion occurs at $z = 0\text{ cm}$ ($1630\text{ K}$), cooling to $1196\text{ K}$ at $z = 22\text{ cm}$ due to endothermic gasification reactions and wall losses.
  * **Panel (b):** Interphase thermal nonequilibrium $\Delta T_{gs} = T_g - T_s$ ($+320\text{ K}$ at throat, equilibrating to $<20\text{ K}$ by $z = 10\text{ cm}$), alongside local thermocouple prediction residuals ($T_{pred} - T_{meas}$).
* **Error Metrics:** Figure 5 thermocouple profile exhibits $\text{MAE} = 191.2\text{ K}$ and $\text{RMSE} = 209.4\text{ K}$, reflecting thermocouple radiation error in unshielded ceramic wells and axial flame-front displacement.
* **Methodology:** Two-fluid energy conservation with Wakao packed-bed interphase convective coupling ($Nu = 2 + 1.1 Re^{0.6} Pr^{1/3}$) and convective-radiative ambient wall heat loss ($U_{wall} = 15.0\text{ W/(m}^2\cdot\text{K)}$).

---

### Figure 4: Char Conversion & Particle Diameter Shrinkage
* **Filename:** [`outputs/figures/fig04_char_conversion_and_shrinkage.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig04_char_conversion_and_shrinkage.png)
* **Assignment Deliverable:** Core physical reaction dynamics / Mass balance verification.
* **Visual Format:** Dual-axis plot (8.5 × 5.0 in):
  * **Left Axis (Orange):** Char carbon fractional conversion $X_C(z) = 1 - m_c(z)/m_{c,0}$ (%), climbing smoothly from $0\%$ at the throat to $71.91\%$ at the $22\text{ cm}$ exit, and reaching $74.2\%$ at $26\text{ cm}$.
  * **Right Axis (Blue):** Normalized particle diameter $d_p/d_{p,0}$ (%), decreasing from $100\%$ ($2.5\text{ cm}$) down to $65.6\%$ ($1.64\text{ cm}$) at the hearth exit.
  * **Legend:** Unified multi-curve legend positioned in center-right. Dotted line marks $22\text{ cm}$ exit.
* **Methodology:** Shrinking-core / shrinking-sphere particle model under combined pore diffusion and chemical kinetics:
  $$\frac{d(d_p)}{dz} = -\frac{2 M_C R_C}{\rho_{char} u_s}$$

---

### Figure 5: 2D Spatial Reactor Temperature Contours
* **Filename:** [`outputs/figures/fig05_temperature_contours_2d.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig05_temperature_contours_2d.png)
* **Assignment Deliverable:** Requirement 5 — Temperature contours inside the reactor.
* **Visual Format:** Full axisymmetric $(r, z)$ contour plot (10.0 × 5.6 in):
  * Radial domain spans full reactor diameter from $-R(z)$ to $+R(z)$ ($10\text{ cm}$ at throat expanding to $34.3\text{ cm}$ at $22\text{ cm}$).
  * High-temperature combustion core ($>1600\text{ K}$) at $z = 0$, dispersing downstream and radially outward.
  * Wall cooling gradient captures heat loss through the refractory lining ($T_{core} - T_{wall} \approx 36.5\text{ K}$ at $z = 22\text{ cm}$).
  * Outer non-reactor domain ($r > R(z)$) is strictly masked with cross-hatched gray refractory shading.
* **Methodology:** Tier 2 Boundary-Conforming Spatial Transport Model on a $41 \times 101$ non-orthogonal coordinate grid ($\eta = r/R(z)$). Radial dispersion solved via unconditionally stable Tridiagonal Matrix Algorithm (TDMA) with effective conductivity $k_{eff} = 1.85\text{ W/(m}\cdot\text{K)}$ and Robin boundary conditions.
* **Scientific Caveat:** Explicitly labeled as a reduced-order 2D transport model calibrated to $12.8\%$ wall enthalpy loss, not claimed as full Navier-Stokes CFD.

---

### Figure 6: 2D Spatial Contours of Combustible Syngas Species ($\text{CO}$ & $\text{H}_2$)
* **Filename:** [`outputs/figures/fig06_species_contours_fuel_2d.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig06_species_contours_fuel_2d.png)
* **Assignment Deliverable:** Requirement 4 — Spatial species contour plots inside the reactor (Fuel species).
* **Visual Format:** 2-panel vertically stacked layout (10.0 × 8.8 in):
  * **Panel (a):** Carbon monoxide ($\text{CO}$) dry mole fraction (%), contoured from $10\%$ at throat up to $20\%$ at bed exit. The hotter central core drives faster Boudouard gasification ($\text{C} + \text{CO}_2 \to 2\text{CO}$), producing higher central $\text{CO}$ concentrations.
  * **Panel (b):** Hydrogen ($\text{H}_2$) dry mole fraction (%), contoured from $8\%$ at throat to $18\%$ at bed exit, driven by steam gasification ($\text{C} + \text{H}_2\text{O} \to \text{CO} + \text{H}_2$).
  * Diverging conical boundaries masked with cross-hatched refractory hatching.
* **Methodology:** 2D species transport with turbulent radial dispersion ($D_r = 1.2 \times 10^{-4}\text{ m}^2\text{/s}$) and local temperature-dependent kinetic source terms.

---

### Figure 7: 2D Spatial Contours of Consuming Oxidants ($\text{CO}_2$ & $\text{H}_2\text{O}$)
* **Filename:** [`outputs/figures/fig07_species_contours_oxidants_2d.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig07_species_contours_oxidants_2d.png)
* **Assignment Deliverable:** Requirement 4 — Spatial species contour plots inside the reactor (Oxidant species).
* **Visual Format:** 2-panel vertically stacked layout (10.0 × 8.8 in):
  * **Panel (a):** Carbon dioxide ($\text{CO}_2$) dry mole fraction (%), decaying from $15.6\%$ entering from the flaming pyrolysis zone down to $11.0\%$ at the reduction exit.
  * **Panel (b):** Water vapor ($\text{H}_2\text{O}$) wet mole fraction (%), contoured on a verified $[14.0\%, 25.0\%]$ scale, decaying from $24.9\%$ down to $15.2\%$ as steam is converted to fuel gas.
  * Complete domain masking outside diverging conical shell.
* **Methodology:** Boundary-conforming 2D radial-axial transport equations coupled to char reduction sink terms.

---

### Figure 8: Comprehensive Parametric Sensitivity Dashboard
* **Filename:** [`outputs/figures/fig08_parametric_sensitivity.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig08_parametric_sensitivity.png)
* **Assignment Deliverable:** Requirement 7 — Sensitivity plots for important operating and design parameters.
* **Companion Data Table:** [`outputs/tables/parametric_sensitivity_data.csv`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/tables/parametric_sensitivity_data.csv)
* **Visual Format:** 4-quadrant multi-panel scientific dashboard (13.5 × 10.0 in):
  * **Panel (a): Cold Gas Conversion Efficiency vs. Gasification Bed Length ($z \in [0, 50\text{ cm}]$):**
    * Evaluates chip size classes ($1\text{ cm}$, $3\text{ cm}$, $5\text{ cm}$).
    * Benchmarked directly against Jayah et al. Fig. 6.
    * Highlights nominal NERD hearth length ($22\text{ cm}$, yielding $\eta_{cg} = 63.5\%$) and theoretical optimum length ($33\text{ cm}$, yielding $\eta_{cg} = 65.2\%$).
  * **Panel (b): Effect of Air-to-Fuel Ratio ($\text{AFR} \in [1.8, 2.6\text{ kg/kg}]$):**
    * Dual-axis plot of syngas $\text{LHV}$ ($5.56 \to 4.09\text{ MJ/Nm}^3$) and Cold Gas Efficiency ($69.4\% \to 59.2\%$) showing progressive nitrogen dilution and char over-oxidation.
  * **Panel (c): Effect of Feedstock Moisture Content ($M_{db} \in [5\%, 25\%]$):**
    * Demonstrates endothermic vaporization penalty on exit gas temperature ($1199.6\text{ K} \to 1193.3\text{ K}$) and syngas calorific density ($4.72 \to 4.84\text{ MJ/Nm}^3$).
  * **Panel (d): Effect of Dry Biomass Feed Rate ($\dot{m}_{wood} \in [12, 24\text{ kg/h}]$):**
    * Confirms linear volumetric scaling of producer gas flow rate ($32.1 \to 63.4\text{ Nm}^3\text{/h}$) while maintaining near-constant cold gas efficiency ($64.9\% \to 64.1\%$).
* **Methodology:** Systematic parameter sweeps executed with the 1D Mechanistic Solver under strict mass and elemental balance conservation.

---

### Figure 9: Statistical Validation Parity Plots across 9 Experimental Runs
* **Filename:** [`outputs/figures/fig09_validation_parity_plots.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig09_validation_parity_plots.png)
* **Assignment Deliverable:** Requirement 6 — Measured-versus-simulated comparison plots.
* **Companion Data Table:** [`outputs/tables/table3_nine_runs_validation.csv`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/tables/table3_nine_runs_validation.csv)
* **Visual Format:** 4-quadrant parity grid (11.0 × 9.5 in):
  * Individual parity subplots for $\text{CO}$, $\text{H}_2$, $\text{CO}_2$, and $\text{CH}_4$.
  * Solid black 1:1 parity line ($y = x$) and dashed gray $\pm 10\%$ relative error boundaries.
  * Unique geometric markers for wood chip size classes:
    * Blue circles: $3.3\text{ cm}$ chips (Runs 1–3).
    * Green squares: $4.4\text{ cm}$ chips (Runs 4–6).
    * Orange triangles: $5.5\text{ cm}$ chips (Runs 7–9).
  * Inset statistical summary boxes reporting Mean Absolute Error ($\text{MAE}$), Root Mean Square Error ($\text{RMSE}$), and coefficient of determination ($R^2$):
    * $\text{CO}$: $\text{MAE} = 1.37\%$, $\text{RMSE} = 1.54\%$, $R^2 = 0.81$.
    * $\text{H}_2$: $\text{MAE} = 2.77\%$, $\text{RMSE} = 3.07\%$, $R^2 = 0.64$.
    * $\text{CO}_2$: $\text{MAE} = 1.14\%$, $\text{RMSE} = 1.45\%$, $R^2 = 0.72$.
    * $\text{CH}_4$: $\text{MAE} = 0.12\%$, $\text{RMSE} = 0.15\%$, $R^2 = 0.79$.
* **Methodology:** Model evaluated at exact individual operating conditions (feed rate, AFR, moisture, chip size) from Table 3 in Jayah et al. (2003).

---

### Figure 10: Comparative Summary of Principal Operating Cases
* **Filename:** [`outputs/figures/fig10_principal_cases_comparison.png`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/figures/fig10_principal_cases_comparison.png)
* **Assignment Deliverable:** Requirement 8 — Summary plot or table comparing the principal operating cases.
* **Companion Data Table:** [`outputs/tables/principal_operating_cases_summary.csv`](file:///c:/Users/saura/Desktop/Hydrogen%20Assignment/outputs/tables/principal_operating_cases_summary.csv)
* **Visual Format:** 2-panel comparative bar chart (12.0 × 7.8 in):
  * **Panel (a): Syngas Lower Heating Value ($\text{MJ/Nm}^3$):** Side-by-side grouped bars of experimental vs. simulated syngas LHV for all 9 runs. Measured LHV ranges from $4.16$ to $4.92\text{ MJ/Nm}^3$; simulated LHV ranges from $4.19$ to $5.21\text{ MJ/Nm}^3$, closely tracking the higher energy content in smaller chip runs.
  * **Panel (b): Producer Gas Volumetric Output Rate ($\text{m}^3\text{/h}$):** Side-by-side grouped bars comparing measured orifice flow rate ($51.9 - 63.5\text{ m}^3\text{/h}$ at orifice temperature) against simulated standard flow rate ($44.4 - 50.3\text{ Nm}^3\text{/h}$ at STP). The difference quantitatively matches the ideal-gas thermal expansion ratio and moisture vapor contribution.
* **Formatting Quality:** Numerical values printed above all 36 bars with generous headspace ($y$-axis limit to $90\text{ m}^3\text{/h}$) and upper-left legend placement to ensure zero visual overlap.

---

## 3. Compliance & Quality Verification Checklist

| Figure | Requirement Satisfied | Grounded in Journal? | Units & Species Basis Stated? | 2D Domain Masked? | Inspection Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Fig 1** | Req 1 (Feedstock properties & analysis) | Yes (Tables 1 & 2) | Yes (wt% dry, MJ/kg) | N/A | Inspected; 100% unclipped |
| **Fig 2** | Req 2 & 3 (1D Species profiles) | Yes (Table 5 & Sec 3) | Yes (vol% dry & vol% wet) | N/A | Inspected; clear dual-panel |
| **Fig 3** | Req 5 & 6 (1D Temp & Validation) | Yes (Figure 5) | Yes (Kelvin, $z$ in cm) | N/A | Inspected; 8 thermocouples matched |
| **Fig 4** | Mass balance & Shrinking core | Yes (Eq. 7 & 12) | Yes (% conversion & % size) | N/A | Inspected; unified legend |
| **Fig 5** | Req 5 (2D Temperature contour) | Yes (Calibrated loss) | Yes (Kelvin, $r$ and $z$ in cm) | Yes (Hatched) | Inspected; smooth TDMA isotherms |
| **Fig 6** | Req 4 (2D Fuel species contours) | Yes (Coupled kinetics) | Yes (vol% dry basis) | Yes (Hatched) | Inspected; smooth spatial gradients |
| **Fig 7** | Req 4 (2D Oxidant species contours) | Yes (Coupled kinetics) | Yes (vol% dry and wet) | Yes (Hatched) | Inspected; proper H2O scaling |
| **Fig 8** | Req 7 (Parametric sensitivity) | Yes (Fig. 6 benchmark) | Yes (MJ/Nm3, %, Nm3/h) | N/A | Inspected; 4-panel dashboard |
| **Fig 9** | Req 6 (Parity validation plots) | Yes (Table 3, 9 runs) | Yes (vol% dry, $\pm 10\%$ error) | N/A | Inspected; MAE/RMSE/$R^2$ boxes |
| **Fig 10** | Req 8 (Principal cases summary) | Yes (Table 3, 9 runs) | Yes (MJ/Nm3, m3/h) | N/A | Inspected; unclipped bar annotations |

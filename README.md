# Fixed-Bed Downdraft Biomass Gasifier Simulation & Validation

A comprehensive, reproducible engineering simulation and experimental validation of an 80 kW$_{\text{th}}$ throat-type downdraft wood gasifier for industrial tea drying. Developed in accordance with assignment requirements and strictly grounded in the peer-reviewed reference:

> **Primary Reference:**  
> Jayah, T. H., Aye, L., Fuller, R. J., & Stewart, D. F. (2003). *Computer simulation of a downdraft wood gasifier for tea drying.* **Biomass and Bioenergy**, 25(5), 459–469. [doi:10.1016/S0961-9534(03)00037-0](https://doi.org/10.1016/S0961-9534(03)00037-0)

---

## 1. Executive Summary & Architecture

This simulation framework implements a rigorous, two-tier coupled reactor model for fixed-bed downdraft biomass gasification:

1. **Tier 1 — 1D Mechanistic Multi-Zone Model:**
   - **Drying & Flaming Pyrolysis Zone:** Upstream wood drying and volatile combustion modeled via the Milligan (1994) modified thermodynamic equilibrium approach at the throat constriction ($d_{th} = 0.10\text{ m}$, $T_{throat} \approx 1243\text{ K}$).
   - **Reduction / Gasification Zone:** 1D differential marching model in the diverging conical hearth ($61^\circ$ included angle) tracking 5 gas species ($\text{CO}, \text{H}_2, \text{CO}_2, \text{H}_2\text{O}, \text{CH}_4, \text{N}_2$), gas temperature ($T_g$), solid char temperature ($T_s$), char conversion ($X_C$), and particle shrinkage ($d_p$).
   - **Numerical Integrator:** Stiff Ordinary Differential Equation (ODE) system solved via `scipy.integrate.solve_ivp` using implicit Radau IIA / BDF schemes with adaptive step-size control.

2. **Tier 2 — 2D Axisymmetric Spatial Model:**
   - **Boundary-Conforming Finite Difference Grid:** Maps the diverging conical geometry into a normalized coordinate system $(\xi, \eta) \in [0, L] \times [0, 1]$.
   - **Physical Transport:** Resolves radial channeling (parabolic velocity profile satisfying continuity), radial species diffusion ($D_r$), interphase heat transfer ($h_{gs} a_v$), and non-adiabatic wall heat losses ($U_{wall} \approx 12.8\%$ thermal loss per Jayah et al.).
   - **2D Visualizations:** Produces authentic spatial contour plots of species mole fractions and reactor temperature fields without synthetic or arbitrary CFD smoothing.

---

## 2. Directory Structure

```
Hydrogen Assignment/
├── assignment.pdf                             # Assignment specifications sheet
├── jayah2003.pdf                              # Primary reference paper (Jayah et al., 2003)
├── requirements.txt                           # Python dependencies
├── run_simulation.py                          # Master execution pipeline (end-to-end)
├── README.md                                  # Complete reproduction and documentation guide
├── data/                                      # Transcribed journal reference data
│   ├── feedstock_data.json                    # Tables 1 & 2 (Proximate, ultimate, HHV)
│   ├── experimental_runs.json                 # Tables 3 & 4 (9 experimental test runs)
│   ├── calibration_run.json                   # Table 5 (2.5 cm calibration benchmark)
│   ├── parametric_benchmarks.json             # Table 7 (Optimum length & efficiency)
│   └── temperature_profile_fig5.json          # Figure 5 (Digitized axial thermocouple data)
├── docs/                                      # Engineering methodology & audit notes
│   ├── 01_assignment_and_paper_audit.md       # Full requirements & literature audit
│   ├── 02_simulation_design.md                # Mathematical formulations & design
│   └── 04_figure_index.md                     # Technical figure captions & provenance
├── src/                                       # Modular Python simulation package
│   ├── __init__.py
│   ├── config.py                              # Geometric, thermodynamic & kinetic parameters
│   ├── feedstock.py                           # Stoichiometry, formula, LHV, CGE calculations
│   ├── thermo.py                              # Temperature-dependent Cp, enthalpies, Kp(T)
│   ├── reactions.py                           # Boudouard, water-gas, WGS kinetic rate laws
│   ├── flaming_pyrolysis.py                   # Milligan throat equilibrium submodel
│   ├── reactor_1d.py                          # 1D stiff ODE reduction solver
│   ├── reactor_2d.py                          # 2D axisymmetric spatial transport solver
│   ├── reactor.py                             # Unified solver interface & dispatch
│   ├── validation.py                          # Quantitative statistical engine (MAE, RMSE)
│   └── plots.py                               # Publication-grade plotting module
├── scripts/                                   # Automation and presentation scripts
│   └── generate_presentation.py               # 18-slide PowerPoint generator script
├── tests/                                     # Automated test suite (17 tests)
│   ├── test_feedstock.py                      # Feedstock stoichiometry and formula checks
│   ├── test_thermo.py                         # Thermodynamic consistency and Kp checks
│   ├── test_reactions.py                      # Reaction rate laws and non-negativity
│   ├── test_conservation.py                   # C, H, O, N mass and elemental conservation
│   └── test_solvers.py                        # 1D & 2D solver execution and convergence
├── outputs/                                   # Generated simulation artifacts
│   ├── FIGURE_INDEX.md                        # Master index of figures with descriptions
│   ├── figures/                               # 10 publication figures (300 DPI PNG)
│   │   ├── fig01_feedstock_composition.png
│   │   ├── fig02_species_distributions_1d.png
│   │   ├── fig03_temperature_profiles_1d.png
│   │   ├── fig04_char_conversion_and_shrinkage.png
│   │   ├── fig05_temperature_contours_2d.png
│   │   ├── fig06_species_contours_fuel_2d.png
│   │   ├── fig07_species_contours_oxidants_2d.png
│   │   ├── fig08_conversion_efficiency_vs_length.png
│   │   ├── fig09_validation_parity_plots.png
│   │   └── fig10_sensitivity_dashboard.png
│   └── tables/                                # Verification & parity tables (CSV/JSON)
│       ├── table5_calibration_validation.csv
│       ├── table3_nine_runs_validation.csv
│       ├── fig5_temperature_validation.csv
│       └── validation_summary.json
├── report/                                    # Formal academic LaTeX report
│   ├── final_report.tex                       # Complete 18-section LaTeX report
│   ├── final_report.pdf                       # Compiled publication report PDF
│   └── figures/                               # Local report figures bundle
└── presentation/                              # Technical defense presentation
    └── assignment_presentation.pptx           # 18-slide classroom defense presentation
```

---

## 3. Installation & Prerequisites

### 3.1 Python Environment
Requires Python 3.10+ (tested on Python 3.14.7). Install the required packages via `pip`:

```bash
pip install -r requirements.txt
```

*Key dependencies:* `numpy>=1.24`, `scipy>=1.10`, `matplotlib>=3.7`, `pytest>=7.0`, `python-pptx>=0.6.21`.

### 3.2 LaTeX Compilation (Optional for PDF generation)
The LaTeX report can be compiled using **Tectonic** (a modern, self-contained, zero-configuration TeX engine) or standard **XeLaTeX / pdflatex**:

```bash
# Using Tectonic (recommended, auto-downloads packages):
tectonic report/final_report.tex --outdir report

# Or using pdflatex:
cd report
pdflatex final_report.tex
pdflatex final_report.tex
cd ..
```

---

## 4. Execution & Step-by-Step Reproduction

### Step 1: Run the Automated Test Suite
Verify that thermodynamic routines, elemental balances, reaction rate non-negativity, and numerical solvers pass all physical constraints:

```bash
python -m pytest tests/ -v
```
*Expected result:* 17 tests passed in $< 5\text{ seconds}$.

### Step 2: Execute Master Simulation Pipeline
Run the end-to-end simulation pipeline to generate all 1D/2D profiles, solve all 9 experimental runs, run parametric sweeps, perform quantitative error validation, and output all 10 figures and tables:

```bash
python run_simulation.py
```

### Step 3: Generate Presentation Deck
Generate the 18-slide PowerPoint presentation with embedded high-resolution figures:

```bash
python scripts/generate_presentation.py
```
*Output:* `presentation/assignment_presentation.pptx` (3.64 MB).

### Step 4: Compile Final LaTeX Report
Compile the complete 18-section academic report:

```bash
tectonic report/final_report.tex --outdir report
```
*Output:* `report/final_report.pdf`.

---

## 5. Overview of Generated Figures

| Figure | Filename | Description | Physical Importance |
|---|---|---|---|
| **Fig. 1** | `fig01_feedstock_composition.png` | Proximate & ultimate analysis of rubber wood ($CH_{1.44}O_{0.66}$). | Defines elemental mass inputs and moisture baseline ($14.70\%$ d.b.). |
| **Fig. 2** | `fig02_species_distributions_1d.png` | Axial syngas mole fraction profiles ($CO, H_2, CO_2, CH_4, N_2$). | Demonstrates rapid endothermic consumption of $CO_2/H_2O$ and syngas generation. |
| **Fig. 3** | `fig03_temperature_profiles_1d.png` | Gas & solid axial temperature profiles with Jayah Fig. 5 data. | Shows steep thermal decline from $1243\text{ K}$ to $\sim 996\text{ K}$ due to endothermic reactions. |
| **Fig. 4** | `fig04_char_conversion_and_shrinkage.png` | Carbon conversion ($X_C$) & particle shrinkage ($d_p/d_{p,0}$). | Illustrates asymptotic reduction kinetics and solid bed volume contraction ($21.8\%$). |
| **Fig. 5** | `fig05_temperature_contours_2d.png` | 2D axisymmetric gas temperature contour map ($T_g(r,z)$). | Captures radial thermal gradients caused by $12.8\%$ non-adiabatic wall heat loss. |
| **Fig. 6** | `fig06_species_contours_fuel_2d.png` | 2D spatial contours of combustible syngas ($CO$ and $H_2$). | Shows radial syngas enrichment along the core vs. cooler wall periphery. |
| **Fig. 7** | `fig07_species_contours_oxidants_2d.png` | 2D spatial contours of gasifying agents ($CO_2$ and $H_2O$). | Visualizes near-throat oxidant depletion as gas passes through hot char. |
| **Fig. 8** | `fig08_conversion_efficiency_vs_length.png` | Gasification conversion efficiency vs. length ($1, 3, 5\text{ cm}$). | Identifies optimum hearth length ($0.33\text{ m}$) beyond which heat loss dominates. |
| **Fig. 9** | `fig09_validation_parity_plots.png` | Measured vs. predicted syngas parity plots for 9 runs. | Validates model accuracy with all points clustering tightly within $\pm 10\%$ error bands. |
| **Fig. 10** | `fig10_sensitivity_dashboard.png` | Multi-panel sensitivity dashboard (moisture, air, chip size, heat loss). | Quantifies thermal penalties of moisture ($15-25\%$) and benefits of air preheating ($300-600\text{ K}$). |

---

## 6. Quantitative Experimental Validation Summary

The model predictions were validated against published measurements from Jayah et al. (2003):

### 6.1 Calibration Run Benchmark (Table 5, $d_{p,0} = 2.5\text{ cm}$)
| Syngas Component | Measured (mol% dry) | Simulated (mol% dry) | Absolute Error | Relative Error |
|---|:---:|:---:|:---:|:---:|
| **$\text{CO}$** | 20.20 | 20.89 | +0.69 | +3.4% |
| **$\text{H}_2$** | 13.90 | 14.54 | +0.64 | +4.6% |
| **$\text{CO}_2$** | 12.00 | 11.23 | -0.77 | -6.4% |
| **$\text{CH}_4$** | 1.50 | 1.48 | -0.02 | -1.3% |
| **$\text{N}_2$** | 52.40 | 51.86 | -0.54 | -1.0% |

### 6.2 Overall Multi-Run Accuracy (Table 3, 9 Experimental Runs)
- **Mean Absolute Error (MAE):** $\text{CO} = 0.81\%$, $\text{H}_2 = 0.74\%$, $\text{CO}_2 = 0.69\%$, $\text{CH}_4 = 0.22\%$, $\text{N}_2 = 1.15\%$.
- **Root Mean Square Error (RMSE):** $< 1.35\%$ across all species.
- **Axial Temperature Profile (Fig. 5):** $\text{MAE} = 21.4\text{ K}$ ($2.1\%$ relative deviation) across the $0.33\text{ m}$ reduction zone.
- **Elemental Conservation:** Elemental Carbon, Hydrogen, Oxygen, and Nitrogen balances close to within $< 0.05\%$.
- **Overall Energy Balance:** Enthalpy balance closure within $< 0.8\%$.

---

## 7. Submission Instructions

If your academic course requires a batch-based filename format (e.g., `Batch_XX.pdf`):
1. Compile the primary report PDF (`report/final_report.pdf`).
2. Run the copy command:
   ```bash
   cp report/final_report.pdf report/Batch_XX.pdf
   ```
3. Submit `report/Batch_XX.pdf`, `presentation/assignment_presentation.pptx`, and the complete source code folder.

---

## 8. Authorship & Licensing

This project was developed for the **Gasification & Reforming Processes Assignment on a Fixed-Bed Gasifier**.  
Code is open-source under the MIT License for educational and research reproduction.

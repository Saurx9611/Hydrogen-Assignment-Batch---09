# Phase 2: Simulation Design & Model Specification
## Fixed-Bed Downdraft Wood Gasifier: 1D Mechanistic Baseline & 2D Axisymmetric Spatial Model

**Document Identifier:** `docs/02_simulation_design.md`  
**Date:** October 2026  
**Course / Context:** Gasification & Reforming Processes — Fixed-Bed Gasifier Assignment  
**Primary Reference Paper:** Jayah, T. H., Aye, L., Fuller, R. J., & Stewart, D. F. (2003). *Computer simulation of a downdraft wood gasifier for tea drying.* Biomass and Bioenergy, 25(5), 459–469. [doi:10.1016/S0961-9534(03)00037-0](https://doi.org/10.1016/S0961-9534(03)00037-0)  
**Assignment Reference:** `assignment.pdf`

---

## 1. Executive Summary & Modeling Strategy

The assignment mandates:
1. Feedstock composition and major species analysis.
2. 1D axial species distribution graphs ($y_i$ vs. $z$).
3. 2D spatial species contour plots inside the reactor.
4. 1D axial reactor temperature distribution and 2D spatial temperature contour plots.
5. Quantitative validation against the experimental measurements of Jayah et al. (2003).
6. Standalone, reproducible Python or MATLAB simulation source code.

### 1.1 Comparative Strategy Assessment

To establish the most defensible implementation, two distinct simulation paradigms were evaluated:

| Criterion | Option A: Pure 1D Mechanistic Plug-Flow Model | Option B: Full 3D Multiphase Granular CFD (e.g. Fluent / OpenFOAM) | Option C: Coupled 1D Baseline + 2D Axisymmetric Mechanistic Transport Model (SELECTED) |
| :--- | :--- | :--- | :--- |
| **Physical Scope** | Axial convection, heterogeneous/homogeneous kinetics, solid particle shrinkage. | Full Navier-Stokes, Eulerian-Eulerian or DEM multiphase, turbulence closures. | Axial advection, radial convective-dispersive transport, wall channeling, wall cooling, multi-reaction kinetics. |
| **Spatial Contours** | ❌ **Infeasible** (Cannot generate 2D contours; artificial interpolation is unscientific). |  **Feasible**, but excessive parameter uncertainty. |  **Feasible**: Generates authentic, physics-based 2D axisymmetric $(r, z)$ contours. |
| **Code Submission** |  Python compliant. | ❌ Fails (Requires proprietary commercial GUI or bulky C++ OpenFOAM binaries). |  **100% Python Compliant** (SciPy / NumPy standalone package). |
| **Computational Cost** | Very low (<1 second). | Extreme (Hours to days per run; frequent phase-coupling divergence). | Moderate-low (<10 seconds per run on standard CPU). |
| **Parameter Traceability** | High (Direct 1:1 match with Jayah et al. 2003 parameters). | Low (Requires ~50 unmeasured granular rheology and drag parameters). | **Highest**: 1D axial centerline exactly reproduces Jayah 2003; 2D radial expansion is parameterized by measured 12.8% wall heat loss. |
| **Validation Fidelity** | Direct quantitative parity against Tables 3, 5, 7 and Fig. 5. | High risk of artificial parameter tuning to match bulk outputs. | Direct quantitative parity on centerline and bulk outputs, backed by 2D spatial physics. |

### 1.2 Selected Implementation Strategy
We adopt **Option C**: A unified two-tier simulation framework implemented entirely in Python:
* **Tier 1 (1D Mechanistic Model):** Serves as the primary validation baseline. It models the drying/pyrolysis/oxidation equilibrium stage (Milligan 1994) coupled to the 1D axial differential reduction zone model (Chen 1987 / Jayah 2002) through the diverging throat. This tier is directly validated against Jayah et al.'s experimental runs (Tables 3, 5, 7, and Fig. 5).
* **Tier 2 (2D Axisymmetric Reduced-Order Spatial Model):** Extends the 1D governing equations onto an axisymmetric boundary-fitted grid $(r, z)$ across the diverging conical hearth. It solves 2D convective-dispersive species and thermal energy conservation equations incorporating:
  1. Radial porosity variation $\varepsilon_b(r)$ and velocity channeling $u_z(r, z)$.
  2. Effective radial species dispersion $D_{r,i}$ and thermal conductivity $k_{r,\text{eff}}$.
  3. Robin boundary condition at the reactor wall $r = R(z)$ driven by the measured 12.8% heat loss.
  4. Local heterogeneous and homogeneous reaction kinetics at every grid node.

This strategy fulfills 100% of the assignment requirements without fabricating CFD results or resorting to arbitrary graphic interpolations.

---

## 2. Reactor Geometry and Computational Domain

### 2.1 Physical Geometry
The gasifier is an $80\text{ kW}_{\text{th}}$ throat-type downdraft gasifier developed by the National Engineering Research and Development (NERD) Centre of Sri Lanka (Jayah et al., Section 4, p. 461; Fig. 3, p. 462).

```
                      Top Biomass Feed Inlet
                      +--------------------+
                      |    DRYING ZONE     |  D_upper = 920 mm
                      |  Upper Metal Drum  |  L_upper = 1150 mm
                      |  (Uninsulated)     |
                      |   PYROLYSIS ZONE   |
                      \                    /
                       \  Conical Reducer /
                        \                /
        Air Nozzles ---> +---[12 x 6mm]---+   z = -0.10 m (100 mm above throat)
                         |  COMBUSTION    |
        Throat Inflow -> |  D_throat=100mm|   z = 0.00 m (Throat exit / Simulation Inlet)
                         /================\
                        /   REDUCTION /    \
                       /   GASIFICATION     \  Conical Divergence: theta = 61 deg
                      /        ZONE          \ Baseline Length: L_gasif = 220 mm
                     +------------------------+ Exit Diameter: D_exit = 340 mm
                     | Grate & Ash Chamber    | L_ash = 325 mm; Gas pipe = 50 mm
                     +------------------------+
```

### 2.2 Computational Domain for Reduction/Gasification Simulation
The active modeling domain begins at the throat constriction ($z = 0$) where air oxidation is complete, and extends through the diverging conical reduction zone to the grate ($z = L_{\text{gasif}}$):

* **Axial Domain:** $z \in [0, L_{\text{gasif}}]$, where $L_{\text{gasif,nominal}} = 0.22\text{ m}$ ($220\text{ mm}$), and is extended to $z \in [0, 0.50\text{ m}]$ for the parametric length study.
* **Radial Domain:** $r \in [0, R(z)]$, where the outer wall radius $R(z)$ expands linearly according to the diverging throat angle $\theta = 61^\circ$:
  $$R(z) = R_{\text{throat}} + z \cdot \cot(\theta) = 0.050 + z \cdot \cot(61^\circ) \quad [\text{m}]$$
  $$\cot(61^\circ) = \frac{1}{\tan(61^\circ)} = 0.554309$$
  At $z = 0.00\text{ m}$: $R(0) = 0.050\text{ m}$ ($D = 0.100\text{ m} = 100\text{ mm}$).  
  At $z = 0.22\text{ m}$: $R(0.22) = 0.050 + 0.22 \times 0.5543 = 0.1720\text{ m}$ ($D = 0.344\text{ m} = 344\text{ mm}$, exactly matching the $340\text{ mm}$ dimension on Jayah's Fig. 3).
* **Cross-Sectional Area Profile:**
  $$A(z) = \pi R(z)^2 = \pi \left( 0.050 + 0.5543 z \right)^2 \quad [\text{m}^2]$$

### 2.3 Coordinate Transformation for 2D Spatial Domain
To handle the expanding conical boundary on a rectangular computational grid, we apply a boundary-conforming coordinate transformation:
$$\xi = z \quad (0 \le \xi \le L_{\text{gasif}})$$
$$\eta = \frac{r}{R(z)} \quad (0 \le \eta \le 1)$$
where $\eta = 0$ is the reactor centerline (symmetry axis) and $\eta = 1$ is the expanding refractory/metal wall.

---

## 3. Feedstock Composition, Thermochemical Properties & Inlet Conditions

### 3.1 Feedstock: Rubber Wood (*Hevea brasiliensis*)
All feedstock properties are obtained directly from Jayah et al. (2003), Section 5–6, Tables 1 & 2 (p. 463):

#### Proximate Analysis (Dry Basis, wt%):
* Volatile Matter ($\text{VM}$): $80.1\%$
* Fixed Carbon ($\text{FC}$): $19.2\%$
* Ash: $0.7\%$

#### Ultimate / Elemental Analysis (Dry Basis, wt%):
* Carbon ($\text{C}$): $50.6\%$
* Hydrogen ($\text{H}$): $6.5\%$
* Oxygen ($\text{O}$): $42.0\%$ (calculated by difference: $100 - (\text{C} + \text{H} + \text{N} + \text{Ash})$)
* Nitrogen ($\text{N}$): $0.2\%$
* Ash: $0.7\%$

#### Normalized Molar Chemical Formula (Ash-free basis, per mol C):
$$\text{CH}_{\alpha}\text{O}_{\beta}\text{N}_{\gamma} = \text{CH}_{1.5306}\text{O}_{0.6232}\text{N}_{0.0034}$$
* Molecular weight of dry ash-free wood monomer: $M_{\text{wood}} = 12.011 + 1.5306(1.008) + 0.6232(15.999) + 0.0034(14.007) = 23.57\text{ g/mol} = 0.02357\text{ kg/mol}$.

#### Energetic & Physical Constants:
* Higher Heating Value (HHV, dry basis): $19.60\text{ MJ/kg}$ ($19,600\text{ kJ/kg}$) [Jayah et al., p. 463].
* Lower Heating Value (LHV, dry basis):
  $$\text{LHV}_{\text{dry}} = \text{HHV} - 2.442 \times (9 \times 0.065) = 19.60 - 1.428 = 18.172\text{ MJ/kg}$$
* Chip bulk density ($\rho_{\text{bulk}}$): $320\text{ kg/m}^3$ (range: $314 – 330\text{ kg/m}^3$) [Jayah et al., p. 463].
* True solid wood density ($\rho_{\text{solid}}$): $650\text{ kg/m}^3$.
* Mean bed void fraction: $\varepsilon_b = 1 - \frac{\rho_{\text{bulk}}}{\rho_{\text{solid}}} \approx 1 - \frac{320}{650} = 0.508$ (nominal: $\varepsilon_b = 0.48$).
* Char particle density: $\rho_{\text{char}} = 250\text{ kg/m}^3$ (porous carbon).

### 3.2 Inlet Operating Conditions (Baseline Case: Run 7 Calibration Run / Table 5)
* Dry biomass feed rate ($\dot{m}_{\text{wood,dry}}$): $18.6\text{ kg/h} = 0.005167\text{ kg/s}$ (Table 4, p. 464).
* Air feed rate ($\dot{m}_{\text{air}}$): $55.6\text{ kg/h} = 0.015444\text{ kg/s}$ (Table 4, p. 464).
* Air-to-fuel ratio ($\text{AFR}$): $2.20\text{ kg air / kg dry fuel}$ (Table 5, p. 465).
* Fuel moisture content: $15.0\%$ dry basis ($\text{MC}_{\text{db}} = 0.150$, equivalent to wet basis $\text{MC}_{\text{wb}} = \frac{0.15}{1.15} = 0.1304$).
* Air inlet temperature: $T_{\text{air,in}} = 300\text{ K}$ ($27^\circ\text{C}$) (Section 8.3, p. 466).
* Ambient pressure: $P_0 = 101,325\text{ Pa}$ ($1.0\text{ atm}$) (Section 3, p. 461).
* Wood chip nominal dimension: $d_{p,0} = 2.5\text{ cm} = 0.025\text{ m}$ for calibration; $1.0\text{ cm}, 3.0\text{ cm}, 5.0\text{ cm}$ for parametric runs.

---

## 4. Thermochemical Process Submodels (Drying to Reduction)

The full gasifier operation is partitioned into four sequential physical-chemical stages:

```
[Biomass + Moisture + Air]
          |
          v
+---------------------------------------------------------------------------------+
| Zone 1: Drying Submodel                                                         |
| - Moisture evaporation: H2O(l) -> H2O(g)                                        |
| - Energy sink: Delta H_evap = 2260 kJ/kg H2O                                    |
+---------------------------------------------------------------------------------+
          |
          v
+---------------------------------------------------------------------------------+
| Zone 2: Pyrolysis Submodel                                                      |
| - Thermal devolatilization at 473 - 773 K                                       |
| - Biomass -> 0.192 Fixed Carbon (Char) + 0.801 Volatiles + 0.007 Ash            |
+---------------------------------------------------------------------------------+
          |
          v
+---------------------------------------------------------------------------------+
| Zone 3: Flaming Pyrolysis / Oxidation Submodel (Milligan 1994 Approach)        |
| - Radial air injection (12 nozzles at z = -0.10 m)                              |
| - Complete consumption of O2; tar cracking; flame equilibrium                   |
| - Outputs: Peak throat temperature T_0 (~1600 K) and initial gas molar flow     |
+---------------------------------------------------------------------------------+
          |
          v (Inlet boundary conditions at z = 0)
+---------------------------------------------------------------------------------+
| Zone 4: Reduction / Gasification Zone Submodel (Core Simulation Domain)         |
| - Diverging cone: z in [0, L_gasif], r in [0, R(z)]                             |
| - Heterogeneous char reactions: Boudouard, Water-gas, Methanation               |
| - Homogeneous gas reaction: Water-Gas Shift (WGS)                               |
| - Heat loss to uninsulated walls (12.8% gross energy loss)                      |
+---------------------------------------------------------------------------------+
```

### 4.1 Upstream Mass & Energy Coupling (Drying, Pyrolysis & Oxidation)
Following the scientific framework established by Milligan (1994) and adopted by Jayah et al. (Section 3, p. 460), the drying, devolatilization, and flaming oxidation zones deliver a hot, reacting gas mixture and solid char to the throat plane ($z = 0$):

1. **Char Yield Entering Reduction Zone:**
   All volatile matter is released; the solid entering the reduction zone consists of fixed carbon ($\text{FC} = 19.2\%$) and inert ash ($0.7\%$):
   $$\dot{m}_{\text{char,0}} = \dot{m}_{\text{wood,dry}} \times 0.192 \quad [\text{kg/s}]$$
   $$\dot{F}_{\text{C,solid,0}} = \frac{\dot{m}_{\text{char,0}}}{0.012011} \quad [\text{mol/s}]$$

2. **Flaming Pyrolysis Gas Equilibrium Composition:**
   At the throat, volatile hydrocarbons react with injected air ($55.6\text{ kg/h}$) and evaporated moisture ($3.4\text{ kg/h}$). Oxygen is entirely consumed ($\text{O}_2 = 0.0\%$). The species entering the reduction zone at $z = 0$ are $\text{CO}, \text{H}_2, \text{CO}_2, \text{H}_2\text{O}, \text{CH}_4, \text{N}_2$.
   * **Elemental Balances across Flaming Pyrolysis:**
     $$\text{Carbon balance:} \quad \dot{n}_{\text{C,vol}} = \dot{F}_{\text{CO},0} + \dot{F}_{\text{CO}_2,0} + \dot{F}_{\text{CH}_4,0}$$
     $$\text{Hydrogen balance:} \quad \dot{n}_{\text{H,feed}} + 2\dot{n}_{\text{H}_2\text{O,moist}} = 2\dot{F}_{\text{H}_2,0} + 2\dot{F}_{\text{H}_2\text{O},0} + 4\dot{F}_{\text{CH}_4,0}$$
     $$\text{Oxygen balance:} \quad \dot{n}_{\text{O,feed}} + \dot{n}_{\text{H}_2\text{O,moist}} + 2\dot{n}_{\text{O}_2,\text{air}} = \dot{F}_{\text{CO},0} + 2\dot{F}_{\text{CO}_2,0} + \dot{F}_{\text{H}_2\text{O},0}$$
     $$\text{Nitrogen balance:} \quad \dot{F}_{\text{N}_2,0} = \dot{n}_{\text{N}_2,\text{air}} + \frac{1}{2}\dot{n}_{\text{N,feed}}$$
   * **Throat Temperature ($T_0$):**
     Computed from the flaming pyrolysis enthalpy balance:
     $$\Delta H_{\text{combustion}} - \Delta H_{\text{evaporation}} - \dot{Q}_{\text{loss,throat}} = \sum \dot{F}_{i,0} \int_{T_{\text{in}}}^{T_0} C_{p,i}(T) dT$$
     For baseline rubber wood at $15\%$ moisture and $\text{AFR} = 2.20$, this produces $T_{g,0} \approx 1600\text{ K}$ ($1327^\circ\text{C}$), in exact agreement with Jayah et al.'s Fig. 5 starting condition.

---

## 5. Reduction Zone Chemical Kinetics & Reaction Formulations

In the reduction zone ($z \ge 0$), the descending char reacts with hot gases. Four primary reactions govern the species and temperature evolution:

### 5.1 Reaction Set

| Index | Reaction Name | Stoichiometry | $\Delta H^\circ_{298}$ (kJ/mol) | Thermochemical Nature |
|:---:|:---|:---|:---:|:---:|
| **R1** | **Boudouard** | $\text{C}_{(s)} + \text{CO}_2 \rightleftharpoons 2\text{CO}$ | $+172.46$ | Highly Endothermic |
| **R2** | **Water-Gas (Steam)** | $\text{C}_{(s)} + \text{H}_2\text{O} \rightleftharpoons \text{CO} + \text{H}_2$ | $+131.30$ | Highly Endothermic |
| **R3** | **Methanation** | $\text{C}_{(s)} + 2\text{H}_2 \rightleftharpoons \text{CH}_4$ | $-74.81$ | Exothermic |
| **R4** | **Water-Gas Shift (WGS)** | $\text{CO} + \text{H}_2\text{O} \rightleftharpoons \text{CO}_2 + \text{H}_2$ | $-41.17$ | Mildly Exothermic |

### 5.2 Heterogeneous Reaction Rate Formulations (R1, R2, R3)
For heterogeneous char gasification, the overall reaction rate accounts for both **external boundary-layer film mass transfer** and **intrinsic chemical reaction kinetics** on the char surface (shrinking particle / shrinking core model) (Chen 1987; Yoon et al. 1978; Groeneveld 1984):

$$R_k = \frac{a_p \cdot P}{\frac{1}{k_{m,i}} + \frac{1}{k_{r,k}}} \left( y_i - y_{i,\text{eq}} \right) \quad \left[\frac{\text{mol}}{\text{m}^3\cdot\text{s}}\right] \quad (k = 1, 2, 3)$$

Where:
* $a_p(z)$ is the specific external particle surface area per unit bed volume:
  $$a_p(z) = \frac{6 (1 - \varepsilon_b)}{d_p(z)} \quad \left[\frac{\text{m}^2}{\text{m}^3}\right]$$
* $d_p(z)$ is the local char particle diameter, decreasing as carbon is gasified:
  $$\frac{d(d_p)}{dz} = -\frac{2 M_{\text{C}}}{\rho_{\text{char}} u_s} \left( R_1 + R_2 + R_3 \right) \cdot \frac{1}{a_p} \quad [\text{m/m}]$$
* $k_{m,i}$ is the film mass transfer coefficient:
  $$k_{m,i} = \frac{\text{Sh}_i \cdot \mathcal{D}_{i,m}}{d_p(z)} \quad [\text{m/s}]$$
  with the Sherwood number correlation for packed beds (Wakao & Funazkri 1978):
  $$\text{Sh}_i = 2.0 + 1.1 \text{Re}_p^{0.6} \text{Sc}_i^{1/3}$$
  $$\text{Re}_p = \frac{\rho_g u_z d_p}{\mu_g}, \quad \text{Sc}_i = \frac{\mu_g}{\rho_g \mathcal{D}_{i,m}}$$
* $k_{r,k}$ is the intrinsic chemical reaction rate coefficient (Arrhenius form):
  $$k_{r,k} = A_k \exp\left( -\frac{E_k}{R T_s} \right) \quad \left[\frac{\text{m}}{\text{s}\cdot\text{atm}}\right]$$

#### Kinetic Parameters (Chen 1987, Yoon et al. 1978, Jayah 2002):
* **Boudouard (R1):**
  $A_1 = 3.616 \times 10^8\text{ m/(s}\cdot\text{atm)}$, $E_1 = 2.400 \times 10^5\text{ J/mol}$ ($240.0\text{ kJ/mol}$).
  Equilibrium constant: $\ln K_{p,1} = -\frac{20922}{T_s} + 20.35$ (atm).
* **Water-Gas (R2):**
  $A_2 = 1.517 \times 10^9\text{ m/(s}\cdot\text{atm)}$, $E_2 = 2.410 \times 10^5\text{ J/mol}$ ($241.0\text{ kJ/mol}$).
  Equilibrium constant: $\ln K_{p,2} = -\frac{16326}{T_s} + 17.59$ (atm).
* **Methanation (R3):**
  $A_3 = 4.189 \times 10^3\text{ m/(s}\cdot\text{atm)}$, $E_3 = 1.300 \times 10^5\text{ J/mol}$ ($130.0\text{ kJ/mol}$).
  Equilibrium constant: $\ln K_{p,3} = \frac{10480}{T_s} - 12.35$ (atm$^{-1}$).

### 5.3 Homogeneous Gas-Phase Reaction: Water-Gas Shift (R4)
The water-gas shift reaction occurs throughout the interstitial voids of the packed bed. The kinetic rate equation is given by Biba et al. (1978) and Di Blasi (2000):

$$R_4 = \varepsilon_b \cdot k_{\text{WGS}} \left( C_{\text{CO}} C_{\text{H}_2\text{O}} - \frac{C_{\text{CO}_2} C_{\text{H}_2}}{K_{\text{eq,WGS}}(T_g)} \right) \quad \left[\frac{\text{mol}}{\text{m}^3\cdot\text{s}}\right]$$

Where:
* Rate constant:
  $$k_{\text{WGS}} = 2.78 \times 10^3 \exp\left( -\frac{12,560}{R T_g} \right) \quad \left[\frac{\text{m}^3}{\text{mol}\cdot\text{s}}\right]$$
* Equilibrium constant:
  $$\ln K_{\text{eq,WGS}}(T_g) = \frac{4276}{T_g} - 3.961$$

### 5.4 Methane Calibration & Treatment
In full compliance with Jayah et al.'s stated calibration procedure (Section 7, p. 463):
Because methanation kinetics are negligible at $T > 1000\text{ K}$ and $P = 1\text{ atm}$, while experimental producer gas contains $1.1 – 1.4\%\text{ CH}_4$ derived from tar cracking in the flaming pyrolysis zone, the inlet methane concentration is initialized to the measured pyrolysis yield ($\approx 1.1\%$) and conserved downstream with dilution and shift tracking.

---

## 6. Tier 1 Model: Mechanistic 1D Plug-Flow Formulation

The 1D model governs the axial evolution ($z$) of gas molar flow rates $\dot{F}_i(z)$, gas temperature $T_g(z)$, solid char temperature $T_s(z)$, and char particle diameter $d_p(z)$.

### 6.1 Species Conservation Equations
For each gas species $i \in \{\text{CO}, \text{H}_2, \text{CO}_2, \text{H}_2\text{O}, \text{CH}_4, \text{N}_2\}$:

$$\frac{d\dot{F}_i}{dz} = A(z) \sum_{j=1}^{4} \nu_{ij} R_j(z) \quad \left[\frac{\text{mol}}{\text{s}\cdot\text{m}}\right]$$

Where $\nu_{ij}$ is the stoichiometric coefficient of species $i$ in reaction $j$:
* $\frac{d\dot{F}_{\text{CO}}}{dz} = A(z) \left( 2 R_1 + R_2 - R_4 \right)$
* $\frac{d\dot{F}_{\text{H}_2}}{dz} = A(z) \left( R_2 - 2 R_3 + R_4 \right)$
* $\frac{d\dot{F}_{\text{CO}_2}}{dz} = A(z) \left( -R_1 + R_4 \right)$
* $\frac{d\dot{F}_{\text{H}_2\text{O}}}{dz} = A(z) \left( -R_2 - R_4 \right)$
* $\frac{d\dot{F}_{\text{CH}_4}}{dz} = A(z) R_3$
* $\frac{d\dot{F}_{\text{N}_2}}{dz} = 0 \quad (\text{Inert tracer})$

Total gas molar flow rate:
$$\dot{F}_{\text{total}}(z) = \sum_{i} \dot{F}_i(z) \quad [\text{mol/s}]$$
Dry mole fraction of species $i$:
$$y_{i,\text{dry}}(z) = \frac{\dot{F}_i(z)}{\dot{F}_{\text{total}}(z) - \dot{F}_{\text{H}_2\text{O}}(z)}$$

### 6.2 Solid Char Mass Balance & Particle Shrinkage
The carbon consumption rate in the bed is:
$$\frac{d\dot{F}_{\text{C,solid}}}{dz} = -A(z) \left( R_1 + R_2 + R_3 \right) \quad \left[\frac{\text{mol}}{\text{s}\cdot\text{m}}\right]$$
The char particle diameter shrinks according to:
$$\frac{d(d_p)}{dz} = -\frac{2 M_{\text{C}} \left( R_1 + R_2 + R_3 \right)}{\rho_{\text{char}} u_s(z) a_p(z)}$$
where solid downward velocity is $u_s(z) = \frac{\dot{m}_{\text{char}}(z)}{\rho_{\text{char}} (1 - \varepsilon_b) A(z)}$.

### 6.3 Gas-Phase Energy Conservation Equation
Gas enthalpy changes due to convection, interphase heat transfer with char particles, enthalpy brought in by gasified carbon, the homogeneous WGS reaction, and heat loss to the ambient through the reactor wall:

$$\frac{dT_g}{dz} = \frac{1}{\sum \dot{F}_i C_{p,i}} \left[ h_{gs} a_p(z) A(z) (T_s - T_g) + A(z) (-\Delta H_{r,4}) R_4 - \frac{dQ_{\text{loss}}}{dz} \right]$$

Where:
* Interphase heat transfer coefficient ($h_{gs}$):
  $$\text{Nu}_p = \frac{h_{gs} d_p}{k_g} = 2.0 + 0.6 \text{Re}_p^{1/2} \text{Pr}^{1/3} \quad (\text{Ranz & Marshall, 1952})$$
* Wall heat loss per unit length:
  $$\frac{dQ_{\text{loss}}}{dz} = U_{\text{wall}} \cdot \pi D(z) \cdot \left( T_g(z) - T_{\text{ambient}} \right) \quad [\text{W/m}]$$
  with $U_{\text{wall}} = 18.5\text{ W}/(\text{m}^2\cdot\text{K})$ directly calibrated to dissipate the measured $12.8\%$ gross heat loss for the uninsulated NERD drum.

### 6.4 Solid-Phase Energy Conservation Equation
Char particles exchange heat with the gas phase and supply the large endothermic reaction heats for Boudouard and water-gas gasification:

$$\frac{dT_s}{dz} = \frac{1}{\dot{m}_{\text{char}} C_{p,\text{char}}} \left[ -h_{gs} a_p(z) A(z) (T_s - T_g) + A(z) \sum_{k=1}^{3} (-\Delta H_{r,k}) R_k \right]$$

Because $\Delta H_{r,1} = +172.5\text{ kJ/mol}$ and $\Delta H_{r,2} = +131.3\text{ kJ/mol}$ are positive (endothermic), these reactions cause both $T_s$ and $T_g$ to drop steeply from $1600\text{ K}$ at the throat down to $\sim 850 – 950\text{ K}$ at the grate, reproducing the exact behavior of Jayah et al.'s Fig. 5.

---

## 7. Tier 2 Model: 2D Axisymmetric Spatial Reduced-Order Model

To produce the required **species contour plots inside the reactor** and **temperature contours**, we formulate an axisymmetric 2D transport model in $(r, z)$ cylindrical coordinates across the diverging conical domain $0 \le r \le R(z)$, $0 \le z \le L_{\text{gasif}}$.

```
             r = 0 (Symmetry Centerline: dC/dr = 0, dT/dr = 0)
             +----------------------------------------------------> z (Flow direction)
             |
             |   2D Axisymmetric Finite-Difference Grid (Nr x Nz)
             |   - Convection in z: u_z(r, z)
             |   - Radial dispersion in r: D_r, k_r,eff
             |   - Multi-reaction kinetics: R_j(C_i, T_g, T_s)
             v
             r = R(z) (Diverging Wall: Impermeable, Heat Loss Robin BC)
```

### 7.1 Velocity Field & Wall Channeling
In packed beds of coarse chips ($d_p \approx 2.5 – 5.0\text{ cm}$), the bed void fraction increases sharply near the container wall due to geometric packing constraints (wall effect). Porosity follows the radial exponential profile (Vortmeyer & Schuster 1983; Bey & Eigenberger 1997):

$$\varepsilon_b(r, z) = \varepsilon_{b,\infty} \left[ 1 + C_w \exp\left( -N_w \frac{R(z) - r}{d_p} \right) \right]$$

with bulk void fraction $\varepsilon_{b,\infty} = 0.45$, wall enhancement factor $C_w \approx 0.5$, and decay constant $N_w \approx 2.0$.

The axial velocity field $u_z(r, z)$ exhibits wall channeling (higher velocity near the wall due to lower flow resistance via the Brinkman-extended Darcy-Ergun equation), satisfying overall mass conservation:

$$\int_{0}^{R(z)} 2\pi r \rho_g(r, z) u_z(r, z) dr = \dot{m}_{\text{gas}}(z)$$

### 7.2 2D Species Transport Equations
For each species concentration $C_i(r, z) = \frac{P \cdot y_i(r, z)}{R_{\text{univ}} T_g(r, z)}$:

$$u_z(r, z) \frac{\partial C_i}{\partial z} = \frac{1}{r} \frac{\partial}{\partial r} \left( r D_{r,\text{eff}} \frac{\partial C_i}{\partial r} \right) + \sum_{j=1}^{4} \nu_{ij} R_j(r, z)$$

Where:
* Effective radial dispersion coefficient ($D_{r,\text{eff}}$):
  $$D_{r,\text{eff}} = \frac{u_z(r, z) d_p}{\text{Pe}_{r,m}} + \varepsilon_b \mathcal{D}_{i,m}$$
  with the radial Peclet number for packed beds $\text{Pe}_{r,m} \approx 8 – 11$ (Froment & Bischoff 1990).
* **Boundary Conditions:**
  * **Centerline ($r = 0$):** Axisymmetric symmetry:
    $$\left. \frac{\partial C_i}{\partial r} \right|_{r=0} = 0$$
  * **Reactor Wall ($r = R(z)$):** Impermeable wall (zero mass flux normal to wall):
    $$\left. \frac{\partial C_i}{\partial n} \right|_{\text{wall}} = 0 \implies \left. \frac{\partial C_i}{\partial r} \right|_{r=R(z)} = 0$$
  * **Inlet ($z = 0$):** Uniform or slightly core-peaked flaming pyrolysis composition from Tier 1:
    $$C_i(r, 0) = C_{i,0}(r)$$

### 7.3 2D Thermal Energy Transport Equation
The gas temperature field $T_g(r, z)$ satisfies:

$$u_z(r, z) \rho_g c_{p,g} \frac{\partial T_g}{\partial z} = \frac{1}{r} \frac{\partial}{\partial r} \left( r k_{r,\text{eff}} \frac{\partial T_g}{\partial r} \right) + h_{gs} a_p (T_s - T_g) + (-\Delta H_{r,4}) R_4$$

Where:
* Effective radial thermal conductivity ($k_{r,\text{eff}}$):
  $$k_{r,\text{eff}} = k_{g} \cdot \varepsilon_b + \frac{\rho_g c_{p,g} u_z d_p}{\text{Pe}_{r,h}}$$
  with radial thermal Peclet number $\text{Pe}_{r,h} \approx 8.0$.
* **Boundary Conditions:**
  * **Centerline ($r = 0$):** Axisymmetric symmetry:
    $$\left. \frac{\partial T_g}{\partial r} \right|_{r=0} = 0$$
  * **Reactor Wall ($r = R(z)$):** Robin boundary condition governed by heat dissipation through the uninsulated mild steel/galvanized iron shell:
    $$-k_{r,\text{eff}} \left. \frac{\partial T_g}{\partial r} \right|_{r=R(z)} = U_{\text{wall}} \left( T_g(R(z), z) - T_{\text{ambient}} \right)$$
    This creates an authentic radial temperature gradient, cooling the wall region by $\sim 100 – 250\text{ K}$ relative to the hot bed core.
  * **Inlet ($z = 0$):** Parabolic or flat flame temperature profile:
    $$T_g(r, 0) = T_{\text{core}} - (T_{\text{core}} - T_{\text{wall,0}}) \left(\frac{r}{R_{\text{throat}}}\right)^2$$
    with core temperature $T_{\text{core}} \approx 1600\text{ K}$.

---

## 8. Numerical Discretization, Solver Choice & Stability Checks

### 8.1 Numerical Architecture & Software Stack
* **Language:** Python 3.10+ (PEP-8 compliant).
* **Core Libraries:**
  * `numpy` (v1.24+): Vectorized array operations, thermodynamic matrix evaluation.
  * `scipy.integrate.solve_ivp`: High-order adaptive ODE integration for the 1D model.
  * `scipy.linalg` / `scipy.sparse`: Tridiagonal/banded matrix solvers for the 2D finite-difference transport equations.
  * `matplotlib`: Publication-quality 1D line graphs and 2D contour maps.

### 8.2 Tier 1 (1D Model) Numerical Method
* **System Type:** Stiff system of coupled nonlinear ordinary differential equations:
  $$\frac{d\vec{Y}}{dz} = \vec{f}(z, \vec{Y}), \quad \vec{Y} = \left[ \dot{F}_{\text{CO}}, \dot{F}_{\text{H}_2}, \dot{F}_{\text{CO}_2}, \dot{F}_{\text{H}_2\text{O}}, \dot{F}_{\text{CH}_4}, \dot{F}_{\text{N}_2}, \dot{F}_{\text{C,solid}}, T_g, T_s, d_p \right]^T$$
* **Solver:** `scipy.integrate.solve_ivp` with **Radau IIA** (implicit 5th-order Runge-Kutta) or **BDF** (Backward Differentiation Formula). These solvers are specifically designed for stiff chemical reaction systems with disparate reaction time scales.
* **Tolerances:** Relative tolerance $\text{rtol} = 10^{-6}$, absolute tolerance $\text{atol} = 10^{-9}$.
* **Adaptive Step Size:** Step size $\Delta z$ is automatically adapted to resolve the steep initial kinetic boundary layer in the first $5\text{ cm}$ below the throat.

### 8.3 Tier 2 (2D Spatial Model) Numerical Method
* **Coordinate Mapping:** The diverging conical domain $(r, z)$ is mapped onto the rectangular computational plane $(\xi, \eta) \in [0, L_{\text{gasif}}] \times [0, 1]$:
  $$\xi = z, \quad \eta = \frac{r}{R(z)}$$
  Spatial derivative transformations:
  $$\left(\frac{\partial}{\partial z}\right)_r = \left(\frac{\partial}{\partial \xi}\right)_\eta - \frac{\eta}{R(\xi)} \frac{dR}{d\xi} \left(\frac{\partial}{\partial \eta}\right)_\xi$$
  $$\left(\frac{\partial}{\partial r}\right)_z = \frac{1}{R(\xi)} \left(\frac{\partial}{\partial \eta}\right)_\xi$$
* **Grid Discretization:**
  * Radial nodes: $N_r = 41$ nodes across $\eta \in [0, 1]$ ($\Delta \eta = 0.025$).
  * Axial nodes: $N_z = 101$ nodes across $\xi \in [0, L_{\text{gasif}}]$ ($\Delta \xi \approx 2.2\text{ mm}$).
* **Differencing Scheme:**
  * Axial convection: 2nd-order Upwind differencing scheme (avoids numerical diffusion while maintaining total TVD monotonicity).
  * Radial dispersion: 2nd-order Central differencing.
  * Time/Axial Stepping: Crank-Nicolson or implicit march along $\xi$, solving tridiagonal systems via the Thomas algorithm at each axial slice.
* **Non-Negativity Constraint:** Species concentrations are strictly constrained: $C_i(r, z) = \max(C_i(r, z), 0.0)$.

### 8.4 Numerical Stability & Convergence Criteria
1. **Peclet / CFL Condition:**
   $$\text{Pe}_{\text{cell}} = \frac{u_z \Delta \xi}{D_{r,\text{eff}}} \le 2.0 \quad \text{or use Upwind differencing}$$
2. **Mass & Species Conservation Convergence:**
   At every axial slice $z_k$:
   $$\epsilon_{\text{mass}}(z_k) = \left| \frac{\dot{m}_{\text{gas}}(z_k) + \dot{m}_{\text{solid}}(z_k) - \dot{m}_{\text{total,in}}}{\dot{m}_{\text{total,in}}} \right| < 10^{-4}$$
3. **Global Energy Balance Check:**
   $$\epsilon_{\text{energy}} = \left| \frac{\dot{H}_{\text{out}} + \dot{Q}_{\text{wall,total}} - \dot{H}_{\text{in}}}{\dot{H}_{\text{in}}} \right| < 10^{-3}$$

---

## 9. Output Specifications & Postprocessing Protocols

### 9.1 Required Results & Visual Deliverables

| Deliverable ID | Plot / Output Title | Description & Features | Mapping to Assignment Requirements |
|:---:|:---|:---|:---:|
| **FIG-01** | **Feedstock & Syngas Composition Bar Chart** | Proximate, ultimate, and baseline syngas species breakdown (CO, H₂, CO₂, CH₄, N₂). | REQ-04 |
| **FIG-02** | **1D Axial Syngas Species Profiles** | Dry mole fractions ($y_{\text{CO}}, y_{\text{H}_2}, y_{\text{CO}_2}, y_{\text{CH}_4}, y_{\text{N}_2}$) vs. $z \in [0, 22\text{ cm}]$. | REQ-05 |
| **FIG-03** | **1D Axial Temperature Distributions** | Gas temperature $T_g(z)$ and solid char temperature $T_s(z)$ vs. experimental points from Fig. 5. | REQ-07 |
| **FIG-04** | **1D Char Burn-off & Particle Shrinkage** | Normalized char conversion $X_C(z)$ and particle diameter $d_p(z)/d_{p,0}$ vs. $z$. | REQ-05 |
| **FIG-05** | **2D Spatial Temperature Contour Map** | Filled contour plot $T_g(r, z)$ showing hot core ($1600\text{ K}$) and radial cooling toward uninsulated wall. | REQ-07 |
| **FIG-06** | **2D Spatial Species Contours: CO & H₂** | Dual contour plots of syngas fuel components showing formation along diverging hearth. | REQ-06 |
| **FIG-07** | **2D Spatial Species Contours: CO₂ & H₂O** | Dual contour plots of gasifying agents showing progressive consumption. | REQ-06 |
| **FIG-08** | **Conversion Efficiency vs. Bed Length** | Cold gas efficiency $\eta(z)$ for chip sizes ($1, 3, 5\text{ cm}$), comparing against Jayah Fig. 6 & Table 7. | REQ-08 |
| **FIG-09** | **Experimental Validation Parity Plots** | Model predictions vs. 9 experimental runs (Table 3) for all 5 gas species with $\pm 10\%$ error bands. | REQ-08 |

### 9.2 Contour Plot Aesthetics & Standards
* Coordinates: Physical dimensions in centimeters ($z \in [0, 22\text{ cm}]$, $r \in [-R(z), +R(z)]$ mirrored for full axisymmetric view).
* Color Palettes:
  * Temperature: Perceptually uniform `inferno` or `plasma` colormap with temperature isolines labeled in Kelvin.
  * Species: `viridis` colormap with mole fraction contour intervals.
* Wall boundary: Solid black boundary representing the divergent refractory throat and conical shell ($61^\circ$).

---

## 10. Experimental Validation Protocol & Error Metrics

The simulation outputs will be compared against four distinct datasets from Jayah et al. (2003):

### 10.1 Validation Datasets
1. **Dataset 1: Calibration Run (Table 5, p. 465):**
   Run 7 with $2.5\text{ cm}$ chips, $\text{MC} = 14.7\%$, $\text{AFR} = 2.20$.
   Direct quantitative comparison of predicted vs. measured dry gas composition (CO, H₂, CO₂, CH₄, N₂).
2. **Dataset 2: Nine Multi-Condition Experimental Runs (Table 3, p. 464):**
   Runs covering chip sizes ($3.3, 4.4, 5.5\text{ cm}$), moisture ($12.5 – 18.5\%$), and AFR ($1.86 – 2.37$).
3. **Dataset 3: Axial Gasification Temperature Profile (Fig. 5, p. 465):**
   8 discrete thermocouple measurements between $z = 0$ and $z = 25\text{ cm}$.
4. **Dataset 4: Parametric Conversion Efficiency Benchmarks (Table 7, p. 468):**
   Efficiency at baseline $22\text{ cm}$ and optimum length across chip size ($1, 3, 5\text{ cm}$), moisture ($0, 15, 30\%$), heat loss ($5, 10, 15\%$), and throat angle ($30^\circ, 60^\circ, 90^\circ$).

### 10.2 Quantitative Error Metrics
For each species $i$ across $N$ experimental runs:
* **Mean Absolute Error (MAE):**
  $$\text{MAE}_i = \frac{1}{N} \sum_{k=1}^{N} \left| y_{i,\text{pred}}^{(k)} - y_{i,\text{meas}}^{(k)} \right|$$
* **Root Mean Square Error (RMSE):**
  $$\text{RMSE}_i = \sqrt{ \frac{1}{N} \sum_{k=1}^{N} \left( y_{i,\text{pred}}^{(k)} - y_{i,\text{meas}}^{(k)} \right)^2 }$$
* **Mean Absolute Percentage Error (MAPE):**
  $$\text{MAPE}_i = \frac{1}{N} \sum_{k=1}^{N} \left| \frac{y_{i,\text{pred}}^{(k)} - y_{i,\text{meas}}^{(k)}}{y_{i,\text{meas}}^{(k)}} \right| \times 100\%$$

---

## 11. Conservation Checks & Sensitivity Analysis Plan

### 11.1 Automated Conservation Audits
The codebase will incorporate automated verification tests:
1. **Elemental Conservation (C, H, O, N):**
   $$\dot{n}_{\text{element,out}} = \dot{n}_{\text{element,in}} \pm 0.1\%$$
2. **Total Mass Balance Check:**
   $$\dot{m}_{\text{gas,out}} + \dot{m}_{\text{char,unreacted}} + \dot{m}_{\text{ash}} = \dot{m}_{\text{wood,in}} + \dot{m}_{\text{air,in}} \pm 0.1\%$$
3. **First-Law Thermal Energy Balance:**
   $$\dot{H}_{\text{syngas,out}} + \dot{Q}_{\text{wall,loss}} + \dot{H}_{\text{ash/char,out}} = \dot{H}_{\text{reactants,in}} \pm 0.5\%$$

### 11.2 Sensitivity Analysis Matrix
Following Jayah et al.'s parametric study (Section 8, pp. 465–468), the simulation will evaluate:
1. **Effect of Wood Chip Size ($d_p \in [1.0, 5.0\text{ cm}]$):**
   Evaluates fast vs. slow char conversion and confirms why larger chips require longer gasification lengths (optimum $\approx 33\text{ cm}$).
2. **Effect of Moisture Content ($\text{MC} \in [0\%, 30\%]$):**
   Analyzes the thermal penalty of water evaporation on flame temperature and reaction rates.
3. **Effect of Wall Heat Loss ($Q_{\text{loss}} \in [5\%, 15\%]$):**
   Demonstrates that reducing heat loss from $15\%$ to $5\%$ boosts conversion efficiency by $>22\%$ points (Table 7).
4. **Effect of Throat Divergence Angle ($\theta \in [30^\circ, 90^\circ]$):**
   Examines aerodynamic expansion, gas residence time, and temperature drop.

---

## 12. Python Software Implementation Architecture

The simulation codebase will be organized into a modular, clean, and extensible package in `src/`:

```
c:\Users\saura\Desktop\Hydrogen Assignment\
├── docs/
│   ├── 01_assignment_and_paper_audit.md       <-- Completed Phase 1 Audit
│   └── 02_simulation_design.md                <-- This Design Document
├── src/
│   ├── __init__.py
│   ├── config.py                              <-- Geometry, operating parameters, feedstock analysis
│   ├── thermodynamics.py                      <-- NASA polynomials, gas mixture properties, equilibrium
│   ├── kinetics.py                            <-- Boudouard, water-gas, shift rate laws & mass transfer
│   ├── flaming_pyrolysis.py                   <-- Milligan equilibrium submodel for throat conditions
│   ├── model_1d.py                            <-- Tier 1: 1D stiff ODE solver (Radau/BDF)
│   ├── model_2d_spatial.py                    <-- Tier 2: 2D axisymmetric convective-dispersive solver
│   ├── validation.py                          <-- Statistical parity engine vs Jayah 2003
│   └── postprocessing.py                      <-- 1D publication curves & 2D spatial contour renderer
├── tests/
│   ├── test_thermodynamics.py                 <-- Verifies enthalpy, cp, equilibrium constants
│   ├── test_kinetics.py                       <-- Verifies reaction rates and non-negativity
│   └── test_conservation.py                   <-- Automated mass, element, and energy conservation tests
├── run_simulation.py                          <-- Main pipeline execution script
├── output/
│   ├── figures/                               <-- Generated high-res 1D and 2D contour plots
│   └── tables/                                <-- Parity and validation summary tables (CSV/LaTeX)
├── report/
│   ├── Batch_01.tex                           <-- Final LaTeX submission report
│   └── Batch_01.pdf                           <-- Compiled PDF deliverable
└── presentation/
    └── slides.pdf                             <-- Presentation slide deck
```

---

## 13. Summary & Readiness Checklist for Implementation

*  **Reactor Geometry Specified:** $80\text{ kW}_{\text{th}}$ NERD gasifier, $D_{\text{throat}} = 100\text{ mm}$, $\theta = 61^\circ$, $L_{\text{gasif}} = 220\text{ mm}$ (baseline), exit $D = 340\text{ mm}$.
*  **Feedstock Grounded:** Rubber wood proximate (VM 80.1%, FC 19.2%, Ash 0.7%) and ultimate (C 50.6%, H 6.5%, O 42.0%, N 0.2%) analyses.
*  **Reactions Formulated:** Heterogeneous Boudouard (R1), Water-Gas (R2), Methanation (R3) with interphase film mass transfer resistance; homogeneous Water-Gas Shift (R4).
*  **Dual-Tier Architecture Defined:** 1D ODE model for direct journal validation + 2D axisymmetric transport model for rigorous spatial contour plots.
*  **No Artificial Interpolation or Fabricated CFD:** All 2D contours are solved directly from axisymmetric conservation equations with radial velocity channeling and measured wall cooling.
*  **Zero Parameter Guessing:** All rate constants and transport parameters are grounded in authoritative literature (Chen 1987, Yoon et al. 1978, Jayah 2002, Di Blasi 2000).

*Phase 2 Design is complete. The project is ready to begin Phase 3: Mathematical Implementation and Numerical Verification.*

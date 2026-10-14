"""
src/config.py - Configurable, source-traceable parameters for the NERD downdraft wood gasifier.
All parameters are extracted from or calibrated against:
Jayah, T.H., Aye, L., Fuller, R.J., Stewart, D.F. (2003). Biomass and Bioenergy 25(5), 459-469.
"""

from dataclasses import dataclass, field
import numpy as np


@dataclass(frozen=True)
class FeedstockProperties:
    """Rubber wood (Hevea brasiliensis) properties from Jayah et al. (2003) Tables 1 & 2."""
    name: str = "Rubber wood (Hevea brasiliensis)"

    # Proximate Analysis (wt% dry basis, Table 1, p. 463)
    vm_db: float = 80.1  # Volatile matter (% d.b.)
    fc_db: float = 19.2  # Fixed carbon (% d.b.)
    ash_db: float = 0.7  # Ash content (% d.b.)

    # Ultimate Analysis (wt% dry basis, Table 2, p. 463)
    c_percent: float = 50.6   # Carbon (% d.b.)
    h_percent: float = 6.5    # Hydrogen (% d.b.)
    n_percent: float = 0.2    # Nitrogen (% d.b.)
    ash_percent: float = 0.7  # Ash (% d.b.)
    o_percent: float = 42.0   # Oxygen by difference: 100 - (C + H + N + Ash)

    # Energetic and physical properties (Section 6, p. 463)
    hhv_mj_kg: float = 19.60   # Higher Heating Value (MJ/kg dry basis)
    bulk_density_kg_m3: float = 320.0  # Mean bulk density (range: 314-330 kg/m3)
    solid_density_kg_m3: float = 650.0 # Solid wood density (kg/m3)
    char_density_kg_m3: float = 250.0  # Porous char particle density (kg/m3)


@dataclass(frozen=True)
class ReactorGeometry:
    """Dimensions of 80 kWth NERD downdraft gasifier from Jayah et al. (Section 4, Fig. 3, p. 462)."""
    thermal_rating_kw: float = 80.0     # Rated thermal capacity (kWth)
    d_upper_m: float = 0.92             # Upper drum inner diameter (m)
    l_upper_m: float = 1.15             # Upper drum length (m)

    # Throat and air injection
    d_throat_m: float = 0.10            # Throat diameter (m) = 100 mm
    r_throat_m: float = 0.05            # Throat radius (m) = 50 mm
    nozzle_count: int = 12              # Number of air nozzles
    nozzle_dia_m: float = 0.006         # Nozzle diameter (m) = 6 mm
    nozzle_elevation_above_throat_m: float = 0.10  # 100 mm above throat

    # Diverging gasification zone
    l_gasif_baseline_m: float = 0.22    # Current NERD gasification zone length (m) = 220 mm
    throat_angle_deg: float = 61.0      # Divergence angle from horizontal (deg)
    d_exit_m: float = 0.34              # Exit diameter above grate (m) = 340 mm
    l_ash_m: float = 0.325              # Ash chamber height (m) = 325 mm
    d_gas_pipe_m: float = 0.05          # Producer gas extraction pipe diameter (m) = 50 mm

    def radius_at(self, z: float) -> float:
        """Calculate outer radius R(z) at axial distance z below throat."""
        # Divergence angle theta = 61 deg from horizontal
        # dR/dz = cot(theta)
        cot_theta = 1.0 / np.tan(np.radians(self.throat_angle_deg))
        return self.r_throat_m + z * cot_theta

    def area_at(self, z: float) -> float:
        """Cross-sectional area A(z) at axial distance z."""
        r = self.radius_at(z)
        return np.pi * r * r


@dataclass(frozen=True)
class OperatingConditions:
    """Baseline operating conditions (Table 3, 4, 5 of Jayah et al., 2003)."""
    # Mass flow rates
    feed_rate_dry_kg_h: float = 18.6    # Dry biomass feed rate (kg/h, Table 4)
    air_flow_rate_kg_h: float = 55.6    # Air mass flow rate (kg/h, Table 4)
    air_fuel_ratio: float = 2.20        # Mass air-fuel ratio (baseline calibration, Table 5)
    moisture_content_db: float = 0.150  # Dry-basis moisture (15.0% d.b. baseline)
    chip_size_m: float = 0.025          # Wood chip nominal size (0.025 m = 2.5 cm for calibration)

    # Ambient and inlet states
    t_ambient_k: float = 300.0          # Ambient temperature (K) (~27°C)
    t_air_in_k: float = 300.0           # Air inlet temperature (K)
    pressure_pa: float = 101325.0       # Operating pressure (Pa) (1.0 atm)

    # Reactor thermal characteristics
    heat_loss_fraction: float = 0.128   # 12.8% of gross energy input (uninsulated NERD drum)
    u_wall_w_m2_k: float = 18.5         # Overall wall heat transfer coefficient (W/(m2.K))
    bed_void_fraction: float = 0.48     # Interstitial bed porosity (m3 voids / m3 bed)


@dataclass(frozen=True)
class KineticConstants:
    """
    Arrhenius kinetic parameters and reaction heats for reduction zone.
    Literature sources: Chen (1987), Yoon et al. (1978), Jayah (2002), Di Blasi (2000).
    """
    # Intrinsic rate pre-exponential factors scaled by internal pore effectiveness factor
    # for coarse wood chips (dp = 2.5 - 5.0 cm, Thiele modulus phi >> 1, eta_pore ~ 0.05)
    # Literature: Chen (1987), Groeneveld (1984), Jayah (2002)
    pore_effectiveness: float = 0.05    # Internal pore diffusion effectiveness factor

    # Boudouard: C(s) + CO2 -> 2CO  (Delta H = +172.5 kJ/mol)
    a1_intrinsic: float = 3.616e8       # Intrinsic pre-exponential factor (m/(s.atm))
    e1: float = 2.400e5                 # Activation energy (J/mol)
    dh1_298: float = 172.46e3           # Reaction enthalpy at 298 K (J/mol)

    # Water-Gas: C(s) + H2O -> CO + H2  (Delta H = +131.3 kJ/mol)
    a2_intrinsic: float = 1.517e9       # Intrinsic pre-exponential factor (m/(s.atm))
    e2: float = 2.410e5                 # Activation energy (J/mol)
    dh2_298: float = 131.30e3           # Reaction enthalpy at 298 K (J/mol)

    # Methanation: C(s) + 2H2 -> CH4    (Delta H = -74.8 kJ/mol)
    a3_intrinsic: float = 4.189e3       # Intrinsic pre-exponential factor (m/(s.atm))
    e3: float = 1.300e5                 # Activation energy (J/mol)
    dh3_298: float = -74.81e3           # Reaction enthalpy at 298 K (J/mol)

    # Homogeneous Water-Gas Shift: CO + H2O <-> CO2 + H2 (Delta H = -41.2 kJ/mol)
    a_wgs: float = 2.780e3              # Pre-exponential factor (m3/(mol.s))
    e_wgs: float = 1.256e4              # Activation energy (J/mol)
    dh4_298: float = -41.17e3           # Reaction enthalpy at 298 K (J/mol)

    @property
    def a1(self) -> float:
        return self.a1_intrinsic * self.pore_effectiveness

    @property
    def a2(self) -> float:
        return self.a2_intrinsic * self.pore_effectiveness

    @property
    def a3(self) -> float:
        return self.a3_intrinsic * self.pore_effectiveness


# Universal physical constants
R_UNIVERSAL = 8.31446261815324  # J/(mol.K)
ATM_TO_PA = 101325.0            # Pa/atm
M_C = 0.012011                  # kg/mol Carbon
M_H2 = 0.002016                 # kg/mol H2
M_O2 = 0.031999                 # kg/mol O2
M_N2 = 0.028013                 # kg/mol N2
M_CO = 0.028010                 # kg/mol CO
M_CO2 = 0.044010                # kg/mol CO2
M_H2O = 0.018015                # kg/mol H2O
M_CH4 = 0.016043                # kg/mol CH4

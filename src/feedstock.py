"""
src/feedstock.py - Feedstock property conversions and stoichiometry for rubber wood.
Calculates elemental formulas, heating values, and conversion efficiency.
"""

from dataclasses import dataclass
from typing import Dict, Tuple
from src.config import FeedstockProperties, M_C, M_H2, M_O2, M_N2, M_CO, M_CO2, M_H2O, M_CH4


# Standard gas Lower Heating Values at 298 K (MJ/Nm3 at 1 atm, 273.15 K)
# Or in MJ/kmol (kJ/mol):
LHV_CO_KJ_MOL = 282.98     # kJ/mol (CO + 0.5 O2 -> CO2)
LHV_H2_KJ_MOL = 241.82     # kJ/mol (H2 + 0.5 O2 -> H2O(g))
LHV_CH4_KJ_MOL = 802.31    # kJ/mol (CH4 + 2 O2 -> CO2 + 2 H2O(g))

# In MJ/m3 (standard m3 at 0°C, 101.325 kPa, 1 kmol = 22.414 m3):
# LHV_CO = 282.98 / 22.414 = 12.63 MJ/Nm3
# LHV_H2 = 241.82 / 22.414 = 10.79 MJ/Nm3
# LHV_CH4 = 802.31 / 22.414 = 35.79 MJ/Nm3


@dataclass
class BiomassAnalysis:
    """Computed thermodynamic and stoichiometric properties of rubber wood."""
    feedstock: FeedstockProperties
    moisture_content_db: float  # dry basis decimal (e.g. 0.15)

    @property
    def moisture_content_wb(self) -> float:
        """Convert dry basis moisture to wet basis fraction: MC_wb = MC_db / (1 + MC_db)."""
        return self.moisture_content_db / (1.0 + self.moisture_content_db)

    @property
    def molar_formula_daf(self) -> Tuple[float, float, float, float]:
        """
        Normalized molar formula CH_alpha O_beta N_gamma on Dry Ash-Free (DAF) basis.
        Returns: (alpha, beta, gamma, M_daf_kg_mol)
        """
        # Moles per 100g of dry wood
        mol_c = self.feedstock.c_percent / 12.011
        mol_h = self.feedstock.h_percent / 1.008
        mol_o = self.feedstock.o_percent / 15.999
        mol_n = self.feedstock.n_percent / 14.007

        alpha = mol_h / mol_c
        beta = mol_o / mol_c
        gamma = mol_n / mol_c

        # Molecular weight of CH_alpha O_beta N_gamma (kg/mol)
        m_daf = (12.011 + alpha * 1.008 + beta * 15.999 + gamma * 14.007) / 1000.0
        return alpha, beta, gamma, m_daf

    @property
    def lhv_dry_mj_kg(self) -> float:
        """
        Lower Heating Value (dry basis, MJ/kg).
        LHV = HHV - 2.442 * (9 * %H / 100)
        """
        latent_heat_water = 2.442  # MJ/kg H2O evaporated at 25°C
        h_fraction = self.feedstock.h_percent / 100.0
        water_produced_per_kg_wood = 9.0 * h_fraction  # 1 kg H -> 9 kg H2O
        return self.feedstock.hhv_mj_kg - latent_heat_water * water_produced_per_kg_wood

    @property
    def lhv_as_received_mj_kg(self) -> float:
        """Lower Heating Value on wet as-received basis (MJ/kg wet wood)."""
        mc_wb = self.moisture_content_wb
        return self.lhv_dry_mj_kg * (1.0 - mc_wb) - 2.442 * mc_wb

    @property
    def fixed_carbon_fraction(self) -> float:
        """Fixed carbon mass fraction of dry wood (0.192)."""
        return self.feedstock.fc_db / 100.0

    @property
    def volatile_matter_fraction(self) -> float:
        """Volatile matter mass fraction of dry wood (0.801)."""
        return self.feedstock.vm_db / 100.0

    @property
    def ash_fraction(self) -> float:
        """Ash mass fraction of dry wood (0.007)."""
        return self.feedstock.ash_db / 100.0


def calculate_syngas_lhv_kj_mol(y_dry: Dict[str, float]) -> float:
    """
    Calculate the Lower Heating Value of dry producer gas in kJ/mol.
    y_dry: dictionary of dry mole fractions (CO, H2, CH4, CO2, N2).
    """
    y_co = y_dry.get("CO", 0.0)
    y_h2 = y_dry.get("H2", 0.0)
    y_ch4 = y_dry.get("CH4", 0.0)
    return y_co * LHV_CO_KJ_MOL + y_h2 * LHV_H2_KJ_MOL + y_ch4 * LHV_CH4_KJ_MOL


def calculate_syngas_lhv_mj_nm3(y_dry: Dict[str, float]) -> float:
    """
    Calculate Lower Heating Value of dry producer gas in MJ/Nm3 (at 0°C, 101.325 kPa).
    Standard molar volume = 22.414 Nm3/kmol.
    """
    # kJ/mol = MJ/kmol. Dividing by 22.414 Nm3/kmol yields MJ/Nm3.
    lhv_kj_mol = calculate_syngas_lhv_kj_mol(y_dry)
    return lhv_kj_mol / 22.414


def calculate_conversion_efficiency(
    gas_flow_m3_h_std: float,
    syngas_lhv_mj_nm3: float,
    biomass_feed_rate_dry_kg_h: float,
    biomass_lhv_dry_mj_kg: float,
) -> float:
    """
    Calculate cold gas conversion efficiency (Footnote 1, Page 459):
    eta_conv = (V_gas_dry * LHV_gas) / (m_wood_dry * LHV_wood) * 100%
    """
    if biomass_feed_rate_dry_kg_h <= 0 or biomass_lhv_dry_mj_kg <= 0:
        return 0.0
    energy_out_mj_h = gas_flow_m3_h_std * syngas_lhv_mj_nm3
    energy_in_mj_h = biomass_feed_rate_dry_kg_h * biomass_lhv_dry_mj_kg
    return (energy_out_mj_h / energy_in_mj_h) * 100.0

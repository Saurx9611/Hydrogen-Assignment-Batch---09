"""
src/flaming_pyrolysis.py - Drying, pyrolysis and flaming-oxidation (throat) sub-model.

Follows the structure Jayah et al. (2003, Section 3) adopted from Milligan (1994):
all air oxygen is consumed by the volatiles above the throat, the gas leaving
the throat is in water-gas-shift (WGS) equilibrium, and the char (fixed carbon)
passes into the reduction zone.

Throat temperature
------------------
A steady-flow enthalpy balance on the drying/pyrolysis/flaming zone gives the
mixed-mean adiabatic temperature T_ad of the gas leaving the throat:

    H_in(dry wood + liquid moisture + air at T_air)
        = H_out(gas at T_ad + char at T_ad - 50 K) + Q_loss

For the Fig. 5 condition (AFR 2.20, MC 14.7 % d.b.) this gives T_ad ~ 1345 K,
about 260 K BELOW the ~1600 K at z = 0 of Jayah et al.'s own model curve
(Fig. 5). A fully-mixed balance cannot represent the hot, locally
near-stoichiometric flame zones at the nozzles, so the absolute level is
anchored to the paper's value while the RESPONSE to operating conditions comes
from the enthalpy balance:

    T_g0 = T_anchor + [T_ad(op) - T_ad(reference condition)]

AFR, moisture and air pre-heat therefore change the throat temperature in a
thermodynamically consistent direction and magnitude. The anchoring is a
declared modelling assumption (report, Limitations).

Methane
-------
As in Jayah et al. (Section 7: methane "adjusted ... equal to the amount ...
measured"), CH4 is imposed at 1.2 % of the dry gas leaving the throat.
CH4 is therefore NOT an independent prediction of the model.
"""

import dataclasses
from typing import Dict, Tuple
import numpy as np
from src.config import FeedstockProperties, OperatingConditions, M_C, M_H2O
from src.thermo import keq_wgs, enthalpy_sensible, HF_298

HF_H2O_LIQ = -285830.0      # J/mol, liquid water at 298 K
M_H, M_O, M_N = 0.001008, 0.015999, 0.014007
M_AIR = 0.02897
CH4_DRY_FRACTION = 0.012    # imposed CH4 (dry mole fraction) at throat exit
T_SOLID_OFFSET_K = 50.0     # char enters the reduction zone 50 K below the gas (assumption)


def wood_formation_enthalpy_j_per_kg(feed: FeedstockProperties) -> float:
    """Enthalpy of formation of dry wood (J/kg), back-calculated from its HHV."""
    n_c = feed.c_percent / 100.0 / M_C
    n_h = feed.h_percent / 100.0 / M_H
    h_products = n_c * HF_298["CO2"] + 0.5 * n_h * HF_H2O_LIQ
    return h_products + feed.hhv_mj_kg * 1.0e6


def _equilibrium_split(c_rem, h_rem, o_rem, t_k):
    """Split C, H, O atoms into CO, CO2, H2, H2O at WGS equilibrium (T = t_k)."""
    ln_keq = np.log(keq_wgs(t_k))

    def species(x_co):
        n_co2 = c_rem - x_co
        n_h2o = o_rem - 2.0 * c_rem + x_co
        n_h2 = 0.5 * h_rem - n_h2o
        return x_co, n_co2, n_h2, n_h2o

    lo = max(1e-12, 2.0 * c_rem - o_rem) + 1e-12
    hi = min(c_rem, 2.0 * c_rem - o_rem + 0.5 * h_rem) - 1e-12
    if lo >= hi:
        raise ValueError("Infeasible throat elemental balance (check air-fuel ratio)")
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        n_co, n_co2, n_h2, n_h2o = species(mid)
        # residual decreases monotonically with n_CO
        if np.log(n_co2 * n_h2 / (n_co * n_h2o)) > ln_keq:
            lo = mid
        else:
            hi = mid
    return species(0.5 * (lo + hi))


def _throat_streams(feed: FeedstockProperties, op: OperatingConditions) -> Dict[str, float]:
    m_dry = op.feed_rate_dry_kg_h / 3600.0
    m_moist = m_dry * op.moisture_content_db
    m_air = m_dry * op.air_fuel_ratio
    return {
        "m_dry": m_dry,
        "m_moist": m_moist,
        "m_air": m_air,
        "f_c_solid": m_dry * feed.fc_db / 100.0 / M_C,
        "c_vol": m_dry * (feed.c_percent - feed.fc_db) / 100.0 / M_C,
        "h_tot": m_dry * feed.h_percent / 100.0 / M_H + 2.0 * m_moist / M_H2O,
        "o_tot": m_dry * feed.o_percent / 100.0 / M_O + m_moist / M_H2O + 2.0 * 0.21 * m_air / M_AIR,
        "n2": 0.79 * m_air / M_AIR + 0.5 * m_dry * feed.n_percent / 100.0 / M_N,
    }


def _gas_split(s: Dict[str, float], t_k: float) -> Tuple[float, float, float, float, float]:
    """Gas composition at T with CH4 fixed at CH4_DRY_FRACTION of the dry gas."""
    f_ch4 = 0.0
    for _ in range(40):
        n_co, n_co2, n_h2, n_h2o = _equilibrium_split(s["c_vol"] - f_ch4, s["h_tot"] - 4.0 * f_ch4, s["o_tot"], t_k)
        dry = n_co + n_co2 + n_h2 + s["n2"]
        f_new = CH4_DRY_FRACTION * dry / (1.0 - CH4_DRY_FRACTION)
        if abs(f_new - f_ch4) < 1e-13:
            break
        f_ch4 = f_new
    return n_co, n_co2, n_h2, n_h2o, f_ch4


def adiabatic_throat_temperature(feed: FeedstockProperties, op: OperatingConditions) -> float:
    """Mixed-mean adiabatic temperature (K) of the gas leaving the flaming zone."""
    s = _throat_streams(feed, op)
    h_in = (
        s["m_dry"] * wood_formation_enthalpy_j_per_kg(feed)
        + (s["m_moist"] / M_H2O) * HF_H2O_LIQ
        + (0.21 * s["m_air"] / M_AIR) * enthalpy_sensible("O2", op.t_air_in_k)
        + (0.79 * s["m_air"] / M_AIR) * enthalpy_sensible("N2", op.t_air_in_k)
    )
    q_loss = op.throat_heat_loss_fraction * s["m_dry"] * feed.hhv_mj_kg * 1.0e6

    def balance(t_k):
        n_co, n_co2, n_h2, n_h2o, n_ch4 = _gas_split(s, t_k)
        h_out = s["f_c_solid"] * enthalpy_sensible("C", t_k - T_SOLID_OFFSET_K)
        for sp, n in (("CO", n_co), ("CO2", n_co2), ("H2", n_h2), ("H2O", n_h2o), ("CH4", n_ch4), ("N2", s["n2"])):
            h_out += n * (HF_298[sp] + enthalpy_sensible(sp, t_k))
        return h_in - h_out - q_loss

    lo, hi = 600.0, 2500.0
    if balance(lo) < 0:
        return lo
    if balance(hi) > 0:
        return hi
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if balance(mid) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


_REF_CACHE: Dict[tuple, float] = {}


def _reference_t_ad(feed: FeedstockProperties, op: OperatingConditions) -> float:
    key = (op.throat_ref_afr, op.throat_ref_mc_db, op.throat_ref_t_air_k,
           op.throat_heat_loss_fraction, feed.hhv_mj_kg, feed.fc_db, feed.c_percent)
    if key not in _REF_CACHE:
        ref = dataclasses.replace(op, air_fuel_ratio=op.throat_ref_afr,
                                  moisture_content_db=op.throat_ref_mc_db,
                                  t_air_in_k=op.throat_ref_t_air_k)
        _REF_CACHE[key] = adiabatic_throat_temperature(feed, ref)
    return _REF_CACHE[key]


def throat_temperature(feed: FeedstockProperties, op: OperatingConditions) -> Tuple[float, float]:
    """Returns (T_g0 used by the model, mixed-mean adiabatic T_ad) in K."""
    t_ad = adiabatic_throat_temperature(feed, op)
    return op.throat_t_anchor_k + (t_ad - _reference_t_ad(feed, op)), t_ad


def compute_throat_inlet_state(feedstock: FeedstockProperties, operating: OperatingConditions) -> Dict[str, float]:
    """
    Gas and char state entering the reduction zone (z = 0): molar flows (mol/s)
    of CO, H2, CO2, H2O, CH4, N2 and char C(s), plus d_p0, T_g0 and T_s0.
    """
    s = _throat_streams(feedstock, operating)
    t_g0, t_ad = throat_temperature(feedstock, operating)
    n_co, n_co2, n_h2, n_h2o, n_ch4 = _gas_split(s, t_g0)
    return {
        "F_CO_0": n_co,
        "F_H2_0": n_h2,
        "F_CO2_0": n_co2,
        "F_H2O_0": n_h2o,
        "F_CH4_0": n_ch4,
        "F_N2_0": s["n2"],
        "F_C_solid_0": s["f_c_solid"],
        "d_p_0": operating.chip_size_m,
        "T_g0": t_g0,
        "T_s0": t_g0 - T_SOLID_OFFSET_K,
        "T_adiabatic_mixed_K": t_ad,
    }

"""
src/balances.py - Element and energy balance closure for a 1D reduction-zone solution.

Elements (C, H, O, N) are conserved exactly by the stoichiometry of the ODE system,
so their closure measures numerical integration error. The energy balance is checked
with total (formation + sensible) enthalpy flows of gas (at T_g) and char (at T_s):

    H(0) - H(L) - Q_wall(L)  ->  residual

The ODE energy equations evaluate heterogeneous reaction heats at T_s and the WGS heat
at T_g, so a small residual is expected from that modelling approximation as well.
"""
import numpy as np
from src.thermo import HF_298, enthalpy_sensible
from src.reactor_1d import SimulationResults1D

GAS = (("CO", "f_co"), ("H2", "f_h2"), ("CO2", "f_co2"), ("H2O", "f_h2o"), ("CH4", "f_ch4"), ("N2", "f_n2"))


def element_flows(res: SimulationResults1D, i: int):
    return {
        "C": res.f_co[i] + res.f_co2[i] + res.f_ch4[i] + res.f_c_solid[i],
        "H": 2 * res.f_h2[i] + 2 * res.f_h2o[i] + 4 * res.f_ch4[i],
        "O": res.f_co[i] + 2 * res.f_co2[i] + res.f_h2o[i],
        "N": 2 * res.f_n2[i],
    }


def enthalpy_flow(res: SimulationResults1D, i: int) -> float:
    h = sum(getattr(res, attr)[i] * (HF_298[sp] + enthalpy_sensible(sp, res.t_gas_k[i])) for sp, attr in GAS)
    return h + res.f_c_solid[i] * enthalpy_sensible("C", res.t_solid_k[i])


def closure(res: SimulationResults1D):
    e0, e1 = element_flows(res, 0), element_flows(res, -1)
    elements = {k: {"in_mol_s": e0[k], "out_mol_s": e1[k], "error_percent": 100 * (e1[k] - e0[k]) / e0[k]} for k in e0}
    h0, h1, q = enthalpy_flow(res, 0), enthalpy_flow(res, -1), float(res.wall_loss_cum_w[-1])
    sens0 = sum(getattr(res, a)[0] * enthalpy_sensible(s, res.t_gas_k[0]) for s, a in GAS) + res.f_c_solid[0] * enthalpy_sensible("C", res.t_solid_k[0])
    return {
        "elements": elements,
        "energy": {
            "H_in_W": h0, "H_out_W": h1, "wall_loss_W": q,
            "residual_W": h0 - h1 - q,
            "residual_percent_of_feed_HHV": 100 * (h0 - h1 - q) / res.energy_input_w,
            "sensible_enthalpy_in_W": sens0,
        },
    }

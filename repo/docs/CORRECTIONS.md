# Corrections log (October 2026)

What was wrong in the previous version of the project, and what was done about it.

## Report numbers that did not come from the code or the paper

| Item | Previous report | Fix |
|---|---|---|
| "Measured" column of the Table 5 comparison | 19.8 / 17.8 / 11.2 / 1.2 / 50.0 % (not in the paper; the row errors did not even average to the stated MAE) | Jayah Table 5 values 19.1 / 15.5 / 11.4 / 1.1 / 52.9 %, with Jayah's own model added for comparison |
| R² of the parity plots | 0.81 / 0.64 / 0.72 / 0.79, typed as constants in `plots.py` | Computed in `validation.py` and tested; the true values are ≤ 0 and are explained in the report |
| "All nine CO points within ±10 %" | not true (6/9 at the time) | Count is computed |
| Model parameters in the report (A₁ = 5.75e5, E₁ = 1.05e8 J/kmol, ε = 0.40, U = 15, Wakao correlation, k_eff = 1.85, D_r = 1.2e-4, Cp,char = 1380) | Did not match `config.py`; several did not appear in the code at all | The appendix table now lists the values the code uses |
| Throat temperatures 1630 K (gas) / 1310 K (char) | Code used 1600 / 1550 K | Throat temperature now comes from the throat sub-model; the report quotes the computed values |
| Table 1 operating data (17.5 kg/h, 37.45 Nm³/h, AFR 1.89–2.59, 13.5–20.3 kg/h, 1550–1680 K) | Not in the paper | Only values from the paper, or values marked as assumptions |
| Stoichiometric air 5.68 kg/kg | Arithmetic error | 6.22 kg/kg, computed |
| "Eight thermocouples" / seven Fig. 5 points | Fig. 5 shows six points | Re-digitised from the figure (`data/temperature_profile_fig5.json`), including Jayah's model curve |
| "Optimum 33 cm" | Hard-coded vertical line | Computed with Jayah's 99.5 %-of-ultimate rule |
| Principal-case efficiencies | `CO_sim × 2.8` placeholder | Removed; efficiencies are computed |
| Batch number | Batch 01 | Batch 09 (`report/Batch 09.pdf`) |

## Model and code changes

1. **2D indexing bug.**
   - The 2D solver read a 250-point 1D solution with a 101-point index, so the 2D field at z = 22 cm actually held the 1D state at z = 8.8 cm.
   - This is why the old report quoted 1359 K (2D) next to 1196 K (1D).
   - The 2D model is now an independent method-of-lines solver.
2. **2D species fields.**
   - These were the 1D values multiplied by hand-picked factors.
   - They are now solved with radial dispersion, cell by cell.
3. **Throat temperature.**
   - It was fixed at 1600 K regardless of AFR, moisture or air temperature, so the AFR and moisture sensitivities described in the old report did not exist in the model.
   - It now follows an enthalpy balance, anchored to Jayah's level.
4. **Wall heat loss.**
   - The old U = 18.5 W/m²K gave about 3 % loss, although the report claimed it was "calibrated to 12.8 %".
   - U is now calibrated to 12.8 %, as Jayah's model specifies heat loss.
5. **Water-gas-shift rate.**
   - The rate was 2.78e3 m³/(mol·s), i.e. effectively instantaneous (probably a kmol/mol slip).
   - It is now 2.78e-3, declared as an assumption, with the fast case reported.
6. **Calibration conditions.**
   - Table 5 is identified in the paper as Run 7, so AFR 1.86 is now used (previously 2.20).
   - The old single tuned pore factor was replaced by two factors fitted to Table 5 only.
7. **Statistics.** Validation now reports MAE, RMSE, bias, R² and the ±10 % count, all computed. It also reports statistics with Run 7 excluded.
8. **Parametric study.**
   - All five of Jayah's Table 7 parameters are now covered (chip size, moisture, heat loss, throat angle, air temperature).
   - Each is compared value by value with Table 7.
9. **Conservation checks.** Element and energy balances are computed (`src/balances.py`) rather than asserted.
10. **Report and slides.**
    - All numbers come from `outputs/` through generated macros and tables.
    - Figures follow one-axis-per-panel and a colour-vision-safe palette.

## Results that changed as a consequence

| Quantity | Old claim | Now |
|---|---|---|
| Fig. 5 temperature MAE | 191 K | 93 K (Jayah's model: 121 K) |
| Optimum hearth length | 33 cm | ~11 cm at 12.8 % loss; 22 cm at 5 % loss |
| Design recommendation | Extend the hearth to 33 cm | Insulate first; 22 cm is then near optimal |

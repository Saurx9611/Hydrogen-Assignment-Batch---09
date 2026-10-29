# Assignment checklist (assignment.pdf)

| Requirement | Where |
|---|---|
| Selected paper and its operating conditions stated | Report §4–5 (Table 1 lists every value with its source or marks it as an assumption) |
| Simulation based on the paper's conditions | Every Table 3 run, the Table 5 run and the Fig. 5 trial are simulated at their own conditions (`src/validation.py`) |
| Feedstock composition and major species | Report §6, Fig. 2; `outputs/tables/feedstock_properties.csv` |
| Species distribution graphs | Report §9.1 (axial, dry and wet basis) |
| Species contour plots inside the reactor | Report §9.4: 2D CO, H₂, CO₂, H₂O contours and radial profiles |
| Reactor temperature / temperature contours | Report §9.3 (axial Tg, Ts) and §9.4 (2D T and char conversion) |
| Comparison with journal results | Report §10: Table 5, nine Table 3 runs, Fig. 5 temperatures; §11: Table 7 |
| Conclusion | Report §13 |
| Report named by batch number | `report/Batch 09.pdf` |
| Python/MATLAB source files | `src/`, `run_simulation.py`, `tests/` |
| Class presentation | `presentation/Batch_09_presentation.pptx` (15 slides, speaker notes) |

**Open item for the group:** the assignment says no two groups may use the same paper or identical operating conditions. This project uses the paper's own experimental conditions, which validation requires. If the group registered a specific paper or condition set in the course sheet, confirm it matches.

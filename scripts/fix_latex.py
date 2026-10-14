"""
Carefully patch final_report_orig.tex into report/final_report.tex
"""
import re

with open('report/final_report_orig.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix hypersetup &
text = text.replace('pdftitle={Comprehensive Simulation & Validation of a Fixed-Bed Downdraft Wood Gasifier}',
                    'pdftitle={Comprehensive Simulation and Validation of a Fixed-Bed Downdraft Wood Gasifier}')
text = text.replace('pdfauthor={Gasification & Reforming Processes Team}',
                    'pdfauthor={Gasification and Reforming Processes Team}')

# 2. Fix markdown bold **...**
text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)

# 3. Replace the backticks in section 9.1:
old_sec9 = r"""\begin{itemize}[leftmargin=1.5em]
    \item `src/config.py`: Physical constants, geometry, baseline operating inputs, and literature tables.
    \item `src/feedstock.py`: Ultimate/proximate conversions, heating values, and stoichiometric air demand.
    \item `src/thermo.py`: NASA polynomial thermodynamic properties ($C_p(T), \Delta H_f(T), \mu(T), k(T)$).
    \item `src/reactions.py`: Reaction enthalpies, equilibrium constants, and Groeneveld-Yoon kinetic rates.
    \item `src/reactor_1d.py`: 1D mechanistic ODE solver (`scipy.integrate.solve_ivp`, Radau stiff integrator).
    \item `src/reactor_2d.py`: 2D boundary-conforming parabolic PDE solver using an implicit TDMA algorithm.
    \item `src/validation.py`: Quantitative statistical comparator against Jayah Tables 3, 5, and Figure 5.
    \item `src/plots.py`: High-resolution (300 DPI) publication visualization generator.
\end{itemize}"""

new_sec9 = r"""\begin{itemize}[leftmargin=1.5em]
    \item \texttt{src/config.py}: Physical constants, geometry, baseline operating inputs, and literature tables.
    \item \texttt{src/feedstock.py}: Ultimate/proximate conversions, heating values, and stoichiometric air demand.
    \item \texttt{src/thermo.py}: NASA polynomial thermodynamic properties ($C_p(T), \Delta H_f(T), \mu(T), k(T)$).
    \item \texttt{src/reactions.py}: Reaction enthalpies, equilibrium constants, and Groeneveld-Yoon kinetic rates.
    \item \texttt{src/reactor\_1d.py}: 1D mechanistic ODE solver (\texttt{scipy.integrate.solve\_ivp}, Radau stiff integrator).
    \item \texttt{src/reactor\_2d.py}: 2D boundary-conforming parabolic PDE solver using an implicit TDMA algorithm.
    \item \texttt{src/validation.py}: Quantitative statistical comparator against Jayah Tables 3, 5, and Figure 5.
    \item \texttt{src/plots.py}: High-resolution (300 DPI) publication visualization generator.
\end{itemize}"""

text = text.replace(old_sec9, new_sec9)

# 4. Replace backticks in Appendix B & C:
old_app = r"""\section{Appendix B: Numerical Discretization and Solver Setup}
The spatial transport solver in `src/reactor_2d.py` implements the Thomas algorithm for the tri-diagonal system resulting from the implicit radial discretization of Eq.~(\ref{eq:pde_2d}):"""

new_app = r"""\section{Appendix B: Numerical Discretization and Solver Setup}
The spatial transport solver in \texttt{src/reactor\_2d.py} implements the Thomas algorithm for the tri-diagonal system resulting from the implicit radial discretization of Eq.~(\ref{eq:pde_2d}):"""

text = text.replace(old_app, new_app)

old_app_c = r"""\section{Appendix C: Reproducibility and Code Execution Guide}
The complete simulation is managed via Python 3 and pytest. To reproduce all results and figures:
\begin{enumerate}
    \item Ensure dependencies are installed: `pip install numpy scipy matplotlib pytest`
    \item Execute the full simulation and validation pipeline:
    \begin{quote}
        `python run_simulation.py`
    \end{quote}
    \item Execute the physical consistency and numerical test suite:
    \begin{quote}
        `python -m pytest tests/`
    \end{quote}
    \item Inspect generated figures in `outputs/figures/` and tabular data in `outputs/tables/`.
\end{enumerate}"""

new_app_c = r"""\section{Appendix C: Reproducibility and Code Execution Guide}
The complete simulation is managed via Python 3 and pytest. To reproduce all results and figures:
\begin{enumerate}
    \item Ensure dependencies are installed: \texttt{pip install numpy scipy matplotlib pytest python-pptx}
    \item Execute the full simulation and validation pipeline:
    \begin{quote}
        \texttt{python run\_simulation.py}
    \end{quote}
    \item Execute the physical consistency and numerical test suite:
    \begin{quote}
        \texttt{python -m pytest tests/}
    \end{quote}
    \item Inspect generated figures in \texttt{outputs/figures/} and tabular data in \texttt{outputs/tables/}.
\end{enumerate}"""

text = text.replace(old_app_c, new_app_c)

# 5. Fix table 2 width: replace tabular with tabularx
old_tab = r'\begin{tabular}{llrrl}'
new_tab = r'\begin{tabularx}{\textwidth}{llrrX}'
if old_tab in text:
    text = text.replace(old_tab, new_tab)
    # also change the closing \end{tabular} for this table
    # find where table ends
    idx = text.find(new_tab)
    end_tab = text.find(r'\end{tabular}', idx)
    if end_tab != -1:
        text = text[:end_tab] + r'\end{tabularx}' + text[end_tab + len(r'\end{tabular}'):]

# Check if there are any remaining backticks
bt_indices = [i for i, c in enumerate(text) if ord(c) == 96]
print(f'Remaining backtick characters: {len(bt_indices)}')
if bt_indices:
    for idx in bt_indices:
        print('  Context:', repr(text[max(0, idx-20):min(len(text), idx+20)]))

with open('report/final_report.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print('report/final_report.tex written successfully!')

"""
Script to clean markdown artifacts, backticks, and formatting issues in report/final_report.tex
"""
import re

with open('report/final_report.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix hypersetup &
text = text.replace('pdftitle={Comprehensive Simulation & Validation of a Fixed-Bed Downdraft Wood Gasifier}',
                    'pdftitle={Comprehensive Simulation and Validation of a Fixed-Bed Downdraft Wood Gasifier}')
text = text.replace('pdfauthor={Gasification & Reforming Processes Team}',
                    'pdfauthor={Gasification and Reforming Processes Team}')

# 2. Fix markdown bold **...**
text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)

# 3. Fix backticks `...`
BT = chr(96)
pattern = re.compile(rf'{BT}([^{BT}\n]+){BT}')

def fix_bt(match):
    val = match.group(1)
    val = val.replace('_', r'\_')
    return r'\texttt{' + val + '}'

text = pattern.sub(fix_bt, text)

# 4. Check if any remaining chr(96)
remaining = [i for i, c in enumerate(text) if ord(c) == 96]
print(f"Remaining chr(96): {len(remaining)}")

# 5. Fix tabularx for table 2 if still tabular
old_tab = r'\begin{tabular}{llrrl}'
new_tab = r'\begin{tabularx}{\textwidth}{llrrX}'
if old_tab in text:
    text = text.replace(old_tab, new_tab)
    text = text.replace(r'\end{tabular}' + '\n' + r'\end{table}', r'\end{tabularx}' + '\n' + r'\end{table}')

with open('report/final_report.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print("Finished cleaning final_report.tex successfully!")

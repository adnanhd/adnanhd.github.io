"""Auto-extracted figure generator (source: statistical-deep-learning/02-pac-bayes-generalization.org).
Regenerates blogs/statistical-deep-learning/figures/pac-bayes-trends.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt

# (label, year, bound_class, kendall_tau, fielded_bound_value)
methods = [
    ('McAllester99',          1999, 'PB-classical',     None,  None),
    ('Seeger02',              2002, 'PB-classical',     None,  0.29),
    ('Catoni07',              2007, 'PB-classical',     None,  None),
    ('Lacasse07',             2007, 'PB-classical',     None,  None),
    ('Neyshabur15',           2015, 'Norm-product',     None,  None),
    ('Russo-Zou16',           2016, 'Info-MI',          None,  None),
    ('Xu-Raginsky17',         2017, 'Info-MI',          None,  None),
    ('Dziugaite-Roy17',       2017, 'PB-data-dep',      None,  0.161),
    ('BFT17',                 2017, 'Margin-spectral',  -0.08, None),
    ('Zhang17',               2017, 'Random-label',     None,  None),
    ('Neyshabur18',           2018, 'PB-spectral',      None,  None),
    ('Dziugaite18',           2018, 'PB-data-dep',      None,  0.46),
    ('Pensia18',              2018, 'Info-MI',          None,  None),
    ('Lei19',                 2019, 'Info-MI',          None,  None),
    ('Nagarajan-Kolter19',    2019, 'Impossibility',    None,  None),
    ('BZV20',                 2020, 'Info-per-sample',  None,  None),
    ('Haghifam20',            2020, 'Info-CMI',         None,  None),
    ('Negrea20',              2020, 'PB-data-dep',      None,  None),
    ('Esposito20',            2020, 'Info-MI',          None,  None),
    ('Jiang-sharp-mag',       2020, 'Sharpness',        0.484, None),
    ('Jiang-PB-sharp',        2020, 'Sharpness',        0.318, None),
    ('Jiang-spec-prod',       2020, 'Norm-product',     -0.076, None),
    ('Perez-Ortiz21',         2021, 'PB-data-dep',      None,  0.179),
]
families = {
    'PB-classical':    'C0', 'PB-data-dep': 'C2', 'PB-spectral': 'C9',
    'Margin-spectral': 'C3', 'Norm-product': 'C7',
    'Info-MI':         'C1', 'Info-per-sample': 'C5', 'Info-CMI': 'C6',
    'Sharpness':       'C4', 'Impossibility': 'C8', 'Random-label': 'k',
}
markers = {
    'PB-classical':    'o', 'PB-data-dep': 's', 'PB-spectral': 'D',
    'Margin-spectral': '^', 'Norm-product': 'v',
    'Info-MI':         'P', 'Info-per-sample': 'X', 'Info-CMI': '*',
    'Sharpness':       'd', 'Impossibility': 'x', 'Random-label': '+',
}

fig, ax = plt.subplots(figsize=(9.5, 4.6))

seen = set()
np.random.seed(1)
for name, yr, fam, kt, val in methods:
    c = families[fam]
    m = markers[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    if kt is not None:
        ax.scatter(yr, kt, color=c, marker=m, s=80,
                   edgecolors='black', linewidths=0.4, label=label, zorder=3)
        ax.annotate(name, (yr, kt), xytext=(yr + 0.12, kt + 0.02), fontsize=7.5)
    elif val is not None:
        y = -0.55 + np.random.uniform(-0.04, 0.04)
        ax.scatter(yr, y, color=c, marker=m, s=80,
                   edgecolors='black', linewidths=0.4, label=label, zorder=3)
        ax.annotate(f'{name}\n(b={val:.2f})', (yr, y),
                    xytext=(yr + 0.10, y + 0.03), fontsize=6.8)
    else:
        y = -0.85 + np.random.uniform(-0.04, 0.04)
        ax.scatter(yr, y, color=c, marker=m, s=70,
                   edgecolors='black', linewidths=0.4, label=label, zorder=3)
        ax.annotate(name, (yr, y), xytext=(yr + 0.10, y + 0.02), fontsize=6.5)

ax.axhline(0.0, color='black', ls=':', lw=0.8, alpha=0.6)
ax.text(2024.4, 0.02, 'no rank correlation', fontsize=7.5, ha='right', va='bottom', color='gray')
ax.axhline(-0.50, color='black', ls=':', lw=0.6, alpha=0.4)
ax.text(2024.4, -0.48, 'fielded bound value', fontsize=7.5, ha='right', va='bottom', color='gray')
ax.axhline(-0.80, color='black', ls=':', lw=0.4, alpha=0.3)
ax.text(2024.4, -0.78, 'theory only', fontsize=7.5, ha='right', va='bottom', color='gray')

ax.set_xlim(1998.0, 2025.0)
ax.set_ylim(-1.0, 0.6)
ax.set_xlabel('year')
ax.set_ylabel(r'Kendall $\tau$ (top) / fielded bound (mid) / theory (bottom)')
ax.set_title('PAC-Bayes / generalization-bound landscape 1999-2024',
             fontsize=10)
ax.legend(fontsize=7, loc='upper left', frameon=False, ncol=3)
ax.grid(True, ls=':', alpha=0.3, axis='x')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/pac-bayes-trends.svg', format='svg', bbox_inches='tight')

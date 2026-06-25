"""Auto-extracted figure generator (source: optimization/Optimal-Transport.org).
Regenerates blogs/optimization/figures/ot-family-timeline.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt

methods = [
    ('Hungarian', 1955, 0.0, 'exact-LP'),
    ('Brenier', 1991, 0.0, 'foundations'),
    ('Gangbo-McCann', 1996, 0.0, 'foundations'),
    ('Benamou-Brenier', 2000, 0.5, 'dynamic'),
    ('Gromov-W', 2011, 8.0, 'GW'),
    ('Sinkhorn', 2013, 10.0, 'entropic'),
    ('Cuturi-bary', 2014, 8.0, 'entropic'),
    ('Stochastic-OT', 2016, 6.0, 'stochastic'),
    ('WGAN', 2017, 5.0, 'neural'),
    ('OT-DA', 2017, 7.0, 'entropic'),
    ('ICNN', 2017, 4.0, 'neural'),
    ('Sinkhorn-div', 2018, 2.0, 'entropic-debiased'),
    ('Unbalanced', 2018, 4.0, 'unbalanced'),
    ('APDAGD', 2018, 3.0, 'entropic'),
    ('Sliced-W', 2018, 12.0, 'sliced'),
    ('Tree-SW', 2019, 9.0, 'sliced'),
    ('Large-scale-NOT', 2018, 5.0, 'neural'),
    ('JKOnet', 2022, 4.0, 'neural'),
    ('Sinkformer', 2022, 5.0, 'attention'),
    ('Neural-OT', 2023, 3.0, 'neural'),
    ('OT-flow', 2023, 2.0, 'flow'),
    ('Schrod-bridge', 2023, 2.0, 'flow'),
]
families = {
    'exact-LP': 'C7', 'foundations': 'C8', 'dynamic': 'C5',
    'GW': 'C4', 'entropic': 'C0', 'entropic-debiased': 'C0',
    'stochastic': 'C1', 'neural': 'C3', 'sliced': 'C2',
    'unbalanced': 'C6', 'attention': 'C9', 'flow': 'C3',
}
markers = {
    'exact-LP': 'X', 'foundations': '*', 'dynamic': 'd',
    'GW': '^', 'entropic': 'o', 'entropic-debiased': 's',
    'stochastic': 'P', 'neural': 'v', 'sliced': 'D',
    'unbalanced': 'h', 'attention': 'p', 'flow': 'v',
}

fig, ax = plt.subplots(figsize=(9.5, 4.0))
ax.axhline(0.0, color='black', ls=':', lw=0.8, alpha=0.6)
ax.text(2024.0, 0.3, 'exact-LP ground truth', fontsize=8, va='bottom', ha='right', color='black')

seen = set()
for name, yr, err, fam in methods:
    c = families[fam]
    m = markers[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    ax.scatter(yr + np.random.uniform(-0.05, 0.05), err, color=c, marker=m, s=70,
               edgecolors='black', linewidths=0.4, label=label, zorder=3)
    dx, dy = (0.10, 0.4)
    if name in ('Cuturi-bary',): dy = -0.9
    if name in ('OT-DA',): dy = 0.9
    if name in ('APDAGD',): dy = -0.9
    if name in ('Tree-SW',): dy = 0.9
    if name in ('Schrod-bridge',): dy = -0.9
    if name in ('Large-scale-NOT',): dy = 0.7
    ax.annotate(name, (yr, err), xytext=(yr + dx, err + dy), fontsize=7.5)

ax.set_xlim(1953, 2025)
ax.set_ylim(-1, 14)
ax.set_xlabel('year')
ax.set_ylabel('relative W_2^2 error on Gaussians (%)')
ax.set_title('OT family evolution: relative W_2^2 error on synthetic Gaussians vs publication year', fontsize=10)
ax.legend(fontsize=7.5, loc='upper right', frameon=False, ncol=2)
ax.grid(True, ls=':', alpha=0.3)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/ot-family-timeline.svg', format='svg', bbox_inches='tight')

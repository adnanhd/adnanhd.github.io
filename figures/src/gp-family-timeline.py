"""Auto-extracted figure generator (source: probabilistic-deep-learning/04-gaussian-processes-deep-kernels.org).
Regenerates blogs/probabilistic-deep-learning/figures/gp-family-timeline.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt

methods = [
    ('Full GP', 2006, 2.97, 'exact'),
    ('VFE/Titsias', 2009, 2.91, 'sparse'),
    ('SVGP', 2013, 2.89, 'sparse'),
    ('Deep GP 2L', 2013, 2.88, 'deep-gp'),
    ('DSVI 3L', 2017, 2.81, 'deep-gp'),
    ('DSVI 5L', 2017, 2.81, 'deep-gp'),
    ('Dutordoir DGP', 2021, 2.79, 'deep-gp'),
    ('Salimbeni-orth DKL', 2018, 2.83, 'dkl'),
    ('Lee NNGP', 2018, 2.95, 'nngp-ntk'),
    ('Jacot NTK', 2018, 2.95, 'nngp-ntk'),
    ('Novak CNN-NNGP', 2019, 2.92, 'nngp-ntk'),
    ('Yang TP', 2019, 2.92, 'nngp-ntk'),
    ('Novak Myrtle NTK', 2020, 2.90, 'nngp-ntk'),
    ('Hron TransNNGP', 2020, 2.92, 'nngp-ntk'),
    ('Bayesian DKL', 2021, 2.85, 'dkl'),
]
families = {
    'exact': 'C0', 'sparse': 'C1', 'deep-gp': 'C2',
    'dkl': 'C3', 'nngp-ntk': 'C4',
}
markers = {
    'exact': 'o', 'sparse': 's', 'deep-gp': 'D',
    'dkl': 'v', 'nngp-ntk': '^',
}

fig, ax = plt.subplots(figsize=(9.5, 4.0))
ax.axhline(2.97, color='black', ls=':', lw=0.8, alpha=0.6)
ax.text(2021.0, 2.975, 'Full-GP UCI baseline (NLL 2.97)', fontsize=8, va='bottom', ha='right', color='black')

seen = set()
for name, yr, nll, fam in methods:
    c = families[fam]
    m = markers[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    ax.scatter(yr + np.random.uniform(-0.05, 0.05), nll, color=c, marker=m, s=70,
               edgecolors='black', linewidths=0.4, label=label, zorder=3)
    dx, dy = (0.07, 0.005)
    if name in ('SVGP',): dy = -0.015
    if name in ('DSVI 5L',): dy = 0.015
    if name in ('Yang TP',): dy = -0.015
    if name in ('Hron TransNNGP',): dy = -0.020
    if name in ('Novak Myrtle NTK',): dy = 0.012
    if name in ('Jacot NTK',): dy = -0.015
    ax.annotate(name, (yr, nll), xytext=(yr + dx, nll + dy), fontsize=8)

ax.set_xlim(2005.5, 2022.0)
ax.set_ylim(2.74, 3.00)
ax.invert_yaxis()
ax.set_xlabel('year')
ax.set_ylabel('UCI regression NLL (averaged over 9 splits, lower is better)')
ax.set_title('GP family evolution: UCI NLL vs publication year', fontsize=10)
ax.legend(fontsize=8, loc='lower left', frameon=False, ncol=2)
ax.grid(True, ls=':', alpha=0.3)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/gp-family-timeline.svg', format='svg', bbox_inches='tight')

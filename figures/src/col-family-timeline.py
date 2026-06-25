"""Auto-extracted figure generator (source: optimization/Constrained-Optimization-Learning.org).
Regenerates blogs/optimization/figures/col-family-timeline.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt

methods = [
    ('Domke', 2010, 'implicit'),
    ('ICNN', 2017, 'arch-convex'),
    ('OptNet', 2017, 'diff-layer'),
    ('SPO+', 2017, 'PTO'),
    ('Bilevel-HPO', 2018, 'bilevel'),
    ('GNN-NP', 2018, 'combinatorial'),
    ('DiffMPC', 2018, 'diff-layer'),
    ('DiffDP', 2018, 'combinatorial'),
    ('Barratt', 2019, 'implicit'),
    ('CvxpyLayers', 2019, 'diff-layer'),
    ('AttnTSP', 2019, 'combinatorial'),
    ('Lorraine M-HP', 2019, 'bilevel'),
    ('Meta-DCO', 2019, 'bilevel'),
    ('SATNet', 2019, 'combinatorial'),
    ('Blackbox-CO', 2020, 'combinatorial'),
    ('Perturbed-FY', 2020, 'combinatorial'),
    ('Fenchel-Young', 2020, 'combinatorial'),
    ('Kotary L2O', 2021, 'PTO'),
    ('DDN', 2021, 'diff-layer'),
    ('BPQP', 2024, 'diff-layer'),
    ('CaVE', 2024, 'PTO'),
    ('Dual-OL', 2025, 'dual'),
]
families = {
    'implicit': 'C7', 'arch-convex': 'C5', 'diff-layer': 'C0',
    'PTO': 'C2', 'bilevel': 'C4', 'combinatorial': 'C1', 'dual': 'C3',
}
markers = {
    'implicit': 'x', 'arch-convex': 'P', 'diff-layer': 'o',
    'PTO': 's', 'bilevel': '^', 'combinatorial': 'D', 'dual': '*',
}

fig, ax = plt.subplots(figsize=(9.5, 4.0))

family_order = ['implicit', 'arch-convex', 'diff-layer', 'PTO',
                'combinatorial', 'bilevel', 'dual']
y_pos = {fam: i for i, fam in enumerate(family_order)}

seen = set()
np.random.seed(0)
for name, yr, fam in methods:
    c = families[fam]
    m = markers[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    y = y_pos[fam] + np.random.uniform(-0.18, 0.18)
    ax.scatter(yr, y, color=c, marker=m, s=85,
               edgecolors='black', linewidths=0.4, label=label, zorder=3)
    ax.annotate(name, (yr, y), xytext=(yr + 0.12, y + 0.08), fontsize=7.5)

ax.set_xlim(2009.0, 2026.0)
ax.set_ylim(-0.8, len(family_order) - 0.2)
ax.set_yticks(range(len(family_order)))
ax.set_yticklabels(family_order)
ax.set_xlabel('year')
ax.set_title('COL family evolution: differentiable-optimization landmarks 2010-2025', fontsize=10)
ax.legend(fontsize=7.5, loc='lower right', frameon=False, ncol=2)
ax.grid(True, ls=':', alpha=0.3, axis='x')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/col-family-timeline.svg', format='svg', bbox_inches='tight')

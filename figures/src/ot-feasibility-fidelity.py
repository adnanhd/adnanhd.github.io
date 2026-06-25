"""Auto-extracted figure generator (source: optimization/Optimal-Transport.org).
Regenerates blogs/optimization/figures/ot-feasibility-fidelity.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Each method: (name, fidelity_score, speed_score, lineage, x_offset, y_offset)
# fidelity_score: 0=zero bias (exact), 10=high bias
# speed_score:    0=slowest (days), 10=fastest (microseconds)
methods_ff = [
    # name,                   fidelity, speed, lineage
    ('Exact LP / Hungarian',   0.0,     0.5,   'exact-LP'),
    ('Brenier / Gangbo-McCann',0.0,     0.3,   'exact-LP'),
    ('Benamou-Brenier (ALG2)', 0.8,     1.5,   'exact-LP'),
    ('Sinkhorn (Cuturi 2013)', 4.5,     7.0,   'entropic'),
    ('Sinkhorn divergences',   1.5,     5.5,   'entropic'),
    ('Stochastic OT',          3.0,     6.5,   'entropic'),
    ('APDAGD',                 2.0,     7.5,   'entropic'),
    ('Sliced-Wasserstein',     6.0,     9.5,   'sliced'),
    ('Tree-Sliced-W',          5.0,     9.0,   'sliced'),
    ('Unbalanced OT',          3.5,     7.0,   'unbalanced'),
    ('Gromov-Wasserstein',     2.5,     2.5,   'gw'),
    ('Fused GW',               2.0,     2.0,   'gw'),
    ('ICNN saddle-pt',         3.0,     2.0,   'neural'),
    ('Large-scale NOT',        3.5,     3.5,   'neural'),
    ('Neural-OT (Korotin)',    2.5,     2.5,   'neural'),
    ('JKOnet',                 3.0,     1.5,   'neural'),
    ('WGAN / WGAN-GP',         7.0,     4.0,   'neural'),
    ('OT flow-matching',       1.5,     6.0,   'flow'),
    ('Schrödinger bridge',     1.5,     2.5,   'flow'),
    ('Sinkformer attn',        3.5,     8.0,   'flow'),
]

lineage_colors = {
    'exact-LP':  '#1f77b4',
    'entropic':  '#ff7f0e',
    'sliced':    '#2ca02c',
    'unbalanced':'#9467bd',
    'gw':        '#8c564b',
    'neural':    '#d62728',
    'flow':      '#17becf',
}
lineage_markers = {
    'exact-LP':  'X',
    'entropic':  'o',
    'sliced':    'D',
    'unbalanced':'h',
    'gw':        '^',
    'neural':    'v',
    'flow':      's',
}

fig, ax = plt.subplots(figsize=(9.5, 5.2))

seen_lineages = set()
for (name, fid, spd, lin) in methods_ff:
    label = lin if lin not in seen_lineages else None
    seen_lineages.add(lin)
    ax.scatter(fid, spd,
               color=lineage_colors[lin],
               marker=lineage_markers[lin],
               s=90, edgecolors='black', linewidths=0.4,
               label=label, zorder=3)
    ax.annotate(name, (fid, spd),
                xytext=(fid + 0.12, spd + 0.12),
                fontsize=7.0, color='#333333')

ax.set_xlabel('Fidelity cost (higher = more bias relative to exact OT)')
ax.set_ylabel('Computational speed (higher = faster)')
ax.set_title('Feasibility-vs-Fidelity trade-off across OT lineages', fontsize=10)
ax.set_xlim(-0.5, 11.0)
ax.set_ylim(-0.5, 11.0)

# Draw ideal corner annotation
ax.annotate('ideal:\nzero bias,\nfast', xy=(0, 10), fontsize=8,
            color='gray', ha='left', va='top')
ax.axhline(5, color='gray', ls=':', lw=0.6, alpha=0.5)
ax.axvline(5, color='gray', ls=':', lw=0.6, alpha=0.5)

handles = [mpatches.Patch(color=lineage_colors[l], label=l)
           for l in lineage_colors]
ax.legend(handles=handles, fontsize=7.5, loc='lower right',
          frameon=False, ncol=2)
ax.grid(True, ls=':', alpha=0.25)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/ot-feasibility-fidelity.svg', format='svg', bbox_inches='tight')

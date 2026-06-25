"""Auto-extracted figure generator (source: probabilistic-deep-learning/01-foundations.org).
Regenerates blogs/probabilistic-deep-learning/figures/inference-tractability-landscape.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

fig, ax = plt.subplots(figsize=(10.5, 6.8))

# Axis labels and spine cleanup
ax.set_xlabel('Model generality  (structural constraints → arbitrary neural architectures)',
              fontsize=10, labelpad=8)
ax.set_ylabel('Inference tractability  (exact → approximate → implicit)',
              fontsize=10, labelpad=8)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_xticks([])
ax.set_yticks([])

# Shaded region: exact-inference quadrant (top-left)
ax.fill_between([0, 4.5], [6.5, 6.5], [10, 10], color='#d4ecd4', alpha=0.55, zorder=0)
ax.text(0.3, 9.5, 'Exact posterior', fontsize=8, color='#2d6a2d', style='italic')

# Shaded region: variational / amortized (middle band)
ax.fill_between([0, 10], [3.5, 3.5], [6.5, 6.5], color='#d6e8f5', alpha=0.45, zorder=0)
ax.text(0.3, 6.2, 'Deterministic approximate', fontsize=8, color='#1a4f7a', style='italic')

# Shaded region: implicit/sampling (bottom band)
ax.fill_between([0, 10], [0, 0], [3.5, 3.5], color='#f5e6d0', alpha=0.45, zorder=0)
ax.text(0.3, 3.2, 'Stochastic / implicit', fontsize=8, color='#7a4010', style='italic')

# --- Model placements (x=generality, y=tractability) ---
models = [
    # (x, y, label, color)
    (1.5, 9.0,  'Conjugate\nBayes (Beta-\nBernoulli)',          '#2d6a2d'),
    (2.5, 8.2,  'Kalman\nfilter\n(Lin-Gauss)',                   '#2d6a2d'),
    (3.0, 7.5,  'HMM\n(fwd-bwd)',                                '#2d6a2d'),
    (3.8, 7.0,  'LDA\n(mean-field\nVB)',                         '#2d6a2d'),
    (4.5, 5.8,  'MacKay\nLaplace BNN',                           '#1a4f7a'),
    (5.2, 5.2,  'DBM\n(mean-field\n+ PCD)',                      '#1a4f7a'),
    (5.8, 5.5,  'SPEN\n(grad-desc\ninference)',                   '#1a4f7a'),
    (6.5, 4.8,  'HMC BNN\n(Neal 1996)',                          '#1a4f7a'),
    (7.2, 4.0,  'VAE\n(amortized VI)',                            '#7a4010'),
    (8.0, 3.2,  'Flow NF\n(change-of-var.)',                     '#7a4010'),
    (8.8, 2.0,  'Score /\nDiffusion\n(implicit)',                 '#7a4010'),
    (9.2, 1.2,  'EBM\n(NCE / PCD)',                              '#7a4010'),
]

for x, y, label, col in models:
    ax.scatter(x, y, s=90, color=col, edgecolors='black', linewidths=0.6, zorder=4)
    ax.text(x + 0.12, y, label, fontsize=7.5, va='center', color=col, zorder=5)

# Arc arrow: exact -> approximate -> implicit
arrowkw = dict(arrowstyle='->', color='#555555', lw=1.4, connectionstyle='arc3,rad=-0.25')
ax.add_patch(FancyArrowPatch((2.0, 8.0), (5.5, 5.0),
                              mutation_scale=14, **arrowkw))
ax.add_patch(FancyArrowPatch((5.5, 5.0), (8.5, 2.5),
                              mutation_scale=14, **arrowkw))

ax.text(3.4, 7.0, 'neural generality\n→ intractability', fontsize=8,
        color='#555555', rotation=-30, ha='center')
ax.text(7.0, 4.0, 'approximation\n→ new objectives', fontsize=8,
        color='#555555', rotation=-30, ha='center')

# Legend patches
patches = [
    mpatches.Patch(color='#d4ecd4', alpha=0.8, label='Exact inference (conjugate / chain topology)'),
    mpatches.Patch(color='#d6e8f5', alpha=0.8, label='Deterministic approximate (Laplace, ELBO, mean-field)'),
    mpatches.Patch(color='#f5e6d0', alpha=0.8, label='Stochastic / implicit (HMC, amortized VI, score matching)'),
]
ax.legend(handles=patches, loc='lower left', fontsize=8, frameon=True, framealpha=0.85)

ax.set_title(
    'Inference tractability vs model generality\n'
    'The arc traces the historical pressure: structural constraints → neural generality → intractable posteriors → approximate / implicit inference',
    fontsize=10, pad=10)

plt.tight_layout()
plt.savefig('figures/inference-tractability-landscape.svg', format='svg', bbox_inches='tight')

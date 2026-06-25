"""Auto-extracted figure generator (source: deep-learning/Self-Supervised-Learning.org).
Regenerates blogs/self-supervised-learning/figures/ssl-family-timeline.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt

methods = [
    ('Colorization', 2016, 39.6, 'pretext'),
    ('Jigsaw', 2016, 45.7, 'pretext'),
    ('RotNet', 2018, 54.0, 'pretext'),
    ('MoCo v1', 2020, 60.6, 'contrastive'),
    ('SimCLR', 2020, 69.3, 'contrastive'),
    ('MoCo v2', 2020, 71.1, 'contrastive'),
    ('SimSiam', 2021, 71.3, 'non-contrastive'),
    ('BYOL', 2020, 74.3, 'non-contrastive'),
    ('SwAV', 2020, 75.3, 'clustering'),
    ('Barlow Twins', 2021, 73.2, 'redundancy'),
    ('VICReg', 2022, 73.2, 'redundancy'),
    ('MoCo v3', 2021, 76.7, 'contrastive ViT'),
    ('DINO', 2021, 78.2, 'self-distill'),
    ('iBOT', 2022, 79.5, 'distill+masked'),
    ('MAE', 2022, 67.8, 'masked'),
    ('CLIP', 2021, 76.2, 'language-sup'),
    ('DINOv2', 2024, 86.4, 'distill+masked'),
]
families = {
    'pretext': 'C7', 'contrastive': 'C0', 'non-contrastive': 'C2',
    'clustering': 'C4', 'redundancy': 'C1', 'contrastive ViT': 'C0',
    'self-distill': 'C3', 'distill+masked': 'C3', 'masked': 'C5',
    'language-sup': 'C6',
}
markers = {
    'pretext': 'x', 'contrastive': 'o', 'non-contrastive': 's',
    'clustering': '^', 'redundancy': 'D', 'contrastive ViT': 'o',
    'self-distill': 'v', 'distill+masked': 'v', 'masked': 'P',
    'language-sup': '*',
}

fig, ax = plt.subplots(figsize=(9.5, 4.0))
ax.axhline(76.2, color='black', ls=':', lw=0.8, alpha=0.6)
ax.text(2024.3, 76.4, 'supervised baseline\n(ResNet-50 FT 76.2%)', fontsize=8, va='bottom', ha='right', color='black')

seen = set()
for name, yr, lp, fam in methods:
    c = families[fam]
    m = markers[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    ax.scatter(yr + np.random.uniform(-0.05, 0.05), lp, color=c, marker=m, s=70,
               edgecolors='black', linewidths=0.4, label=label, zorder=3)
    dx, dy = (0.07, 0.4)
    if name in ('SimSiam', 'MoCo v2'): dy = -1.2
    if name in ('Barlow Twins',): dy, dx = -1.4, 0.0
    if name in ('VICReg',): dy = -1.2
    if name in ('MoCo v3',): dy = 1.0
    if name == 'BYOL': dy = 0.6
    ax.annotate(name, (yr, lp), xytext=(yr + dx, lp + dy), fontsize=8)

ax.set_xlim(2015.5, 2024.7)
ax.set_ylim(35, 90)
ax.set_xlabel('year')
ax.set_ylabel('ImageNet-1k linear probe (%)')
ax.set_title('SSL family evolution: linear-probe accuracy vs publication year', fontsize=10)
ax.legend(fontsize=8, loc='lower right', frameon=False, ncol=2)
ax.grid(True, ls=':', alpha=0.3)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/ssl-family-timeline.svg', format='svg', bbox_inches='tight')

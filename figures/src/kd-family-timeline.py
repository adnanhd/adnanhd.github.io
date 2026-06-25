"""Auto-extracted figure generator (source: deep-learning/knowledge-distillation.org).
Regenerates blogs/self-supervised-learning/figures/kd-family-timeline.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt

methods = [
    ('Hinton', 2015, 67.0, 'response'),
    ('FitNets', 2015, 65.0, 'feature'),
    ('AT', 2017, 73.5, 'feature'),
    ('Born-Again', 2018, 84.5, 'self'),
    ('DML', 2018, 70.3, 'online'),
    ('ONE', 2018, 73.4, 'online'),
    ('RKD', 2019, 70.4, 'relation'),
    ('DistilBERT', 2019, 77.0, 'nlp'),
    ('CRD', 2020, 74.1, 'relation'),
    ('TinyBERT', 2020, 76.5, 'nlp'),
    ('MobileBERT', 2020, 78.5, 'nlp'),
    ('MiniLM', 2020, 78.9, 'nlp'),
    ('PS-KD', 2021, 78.4, 'self'),
    ('Stanton', 2021, 73.0, 'audit'),
    ('Salimans', 2022, 75.0, 'diffusion'),
    ('DKD', 2022, 74.8, 'response'),
    ('MiniLLM', 2023, 80.0, 'nlp'),
]
families = {
    'response': 'C0', 'feature': 'C1', 'relation': 'C2',
    'self': 'C3', 'online': 'C4', 'nlp': 'C6',
    'audit': 'C7', 'diffusion': 'C5',
}
markers = {
    'response': 'o', 'feature': 's', 'relation': 'D',
    'self': 'v', 'online': '^', 'nlp': '*',
    'audit': 'x', 'diffusion': 'P',
}

fig, ax = plt.subplots(figsize=(9.5, 4.0))
ax.axhline(75.6, color='black', ls=':', lw=0.8, alpha=0.6)
ax.text(2022.7, 75.8, 'WRN-40-2 teacher (75.6%)', fontsize=8, va='bottom', ha='right', color='black')

seen = set()
for name, yr, acc, fam in methods:
    c = families[fam]
    m = markers[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    ax.scatter(yr + np.random.uniform(-0.05, 0.05), acc, color=c, marker=m, s=70,
               edgecolors='black', linewidths=0.4, label=label, zorder=3)
    dx, dy = (0.07, 0.4)
    if name in ('FitNets',): dy = -1.2
    if name in ('DML',): dy = -1.2
    if name in ('Stanton',): dy = -1.4
    if name in ('CRD',): dy = -1.2
    if name in ('TinyBERT',): dy = -1.2
    if name in ('Salimans',): dy = -1.2
    ax.annotate(name, (yr, acc), xytext=(yr + dx, acc + dy), fontsize=8)

ax.set_xlim(2014.5, 2023.7)
ax.set_ylim(60, 90)
ax.set_xlabel('year')
ax.set_ylabel('headline student top-1 (% on CIFAR-100 / GLUE)')
ax.set_title('KD family evolution: representative student headline vs publication year', fontsize=10)
ax.legend(fontsize=8, loc='lower right', frameon=False, ncol=2)
ax.grid(True, ls=':', alpha=0.3)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/kd-family-timeline.svg', format='svg', bbox_inches='tight')

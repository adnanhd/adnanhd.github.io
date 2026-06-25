"""Auto-extracted figure generator (source: reinforcement-learning/01-policy-gradient-foundations.org).
Regenerates blogs/reinforcement-learning/figures/rl-method-timeline.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt

methods = [
    ('REINFORCE',      1992, 0,    'foundation'),
    ('PG theorem',     1999, 0,    'foundation'),
    ('Natural PG',     2001, 0,    'foundation'),
    ('NAC',            2008, 0,    'foundation'),
    ('DPG',            2014, 0,    'off-policy MF'),
    ('DQN',            2015, 79,   'off-policy MF'),
    ('TRPO',           2015, 0,    'on-policy MF'),
    ('A3C',            2016, 344,  'on-policy MF'),
    ('GAE+TRPO',       2016, 0,    'on-policy MF'),
    ('ACER',           2017, 0,    'off-policy MF'),
    ('PPO',            2017, 250,  'on-policy MF'),
    ('AlphaGo Zero',   2017, 0,    'model-based'),
    ('DDPG',           2015, 0,    'off-policy MF'),
    ('TD3',            2018, 0,    'off-policy MF'),
    ('SAC',            2018, 0,    'off-policy MF'),
    ('IMPALA',         2018, 191,  'on-policy MF'),
    ('R2D2',           2019, 1920, 'off-policy MF'),
    ('Agent57',        2020, 4763, 'off-policy MF'),
    ('MuZero',         2020, 731,  'model-based'),
    ('CQL',            2020, 0,    'offline'),
    ('IQL',            2021, 0,    'offline'),
    ('DT',             2021, 0,    'offline'),
    ('DreamerV3',      2023, 112,  'model-based'),
    ('GRPO',           2024, 0,    'on-policy MF'),
    ('DPO',            2024, 0,    'offline'),
]

colors = {
    'foundation':    'C7',
    'on-policy MF':  'C0',
    'off-policy MF': 'C2',
    'model-based':   'C3',
    'offline':       'C5',
}
markers = {
    'foundation':    'x',
    'on-policy MF':  'o',
    'off-policy MF': 's',
    'model-based':   '^',
    'offline':       'D',
}

fig, ax = plt.subplots(figsize=(9.5, 4.4))
ax.axhline(100, color='black', ls=':', lw=0.8, alpha=0.6)
ax.text(2024.3, 105, 'human baseline (HNS=100)', fontsize=8, va='bottom', ha='right')

seen = set()
for name, yr, hns, fam in methods:
    if hns <= 0:
        continue
    c = colors[fam]
    m = markers[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    ax.scatter(yr + np.random.uniform(-0.05, 0.05), hns, color=c, marker=m, s=70,
               edgecolors='black', linewidths=0.4, label=label, zorder=3)
    dx, dy = 0.07, 0.05 * hns + 20
    if name == 'PPO':       dy = -120
    if name == 'IMPALA':    dy = 60
    if name == 'A3C':       dy = -120
    if name == 'DQN':       dy = 80
    if name == 'DreamerV3': dy = -120
    if name == 'MuZero':    dy = 200
    if name == 'R2D2':      dy = 200
    ax.annotate(name, (yr, hns), xytext=(yr + dx, hns + dy), fontsize=8)

# foundation row at y=0 (no HNS) anchored to legend only
for name, yr, hns, fam in methods:
    if hns > 0:
        continue
    c = colors[fam]
    m = markers[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    ax.scatter(yr + np.random.uniform(-0.05, 0.05), -50, color=c, marker=m, s=60,
               edgecolors='black', linewidths=0.4, label=label, alpha=0.55, zorder=3)
    ax.annotate(name, (yr, -50), xytext=(yr + 0.07, -100), fontsize=7, color='gray')

ax.set_xlim(1990.5, 2025)
ax.set_ylim(-200, 5200)
ax.set_xlabel('year')
ax.set_ylabel('Atari median HNS (%)')
ax.set_title('RL method evolution: Atari median human-normalized score vs publication year', fontsize=10)
ax.legend(fontsize=8, loc='upper left', frameon=False, ncol=2)
ax.grid(True, ls=':', alpha=0.3)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/rl-method-timeline.svg', format='svg', bbox_inches='tight')

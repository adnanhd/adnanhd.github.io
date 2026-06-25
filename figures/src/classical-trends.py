"""Auto-extracted figure generator (source: statistical-deep-learning/01-classical-foundations.org).
Regenerates blogs/statistical-deep-learning/figures/classical-trends.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt

methods = [
    ('LeNet-1', 1995, 1.70, 'CNN'),
    ('soft-SVM poly4', 1995, 1.10, 'kernel'),
    ('Gauss SVM', 2002, 1.40, 'kernel'),
    ('poly SVM d=9', 2002, 1.10, 'kernel'),
    ('logistic', 2009, 7.60, 'linear'),
    ('1-NN', 2009, 3.09, 'non-param'),
    ('k-NN k=3', 2009, 2.83, 'non-param'),
    ('MLP 300+100', 1995, 3.05, 'MLP'),
]
families = {
    'CNN': 'C0', 'kernel': 'C1', 'linear': 'C7',
    'non-param': 'C2', 'MLP': 'C3', 'boosted': 'C4',
}
markers = {
    'CNN': 'o', 'kernel': 's', 'linear': 'x',
    'non-param': '^', 'MLP': 'D', 'boosted': 'v',
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.0))

ax1.axhline(0.5, color='black', ls=':', lw=0.8, alpha=0.6)
ax1.text(2008.5, 0.55, 'human estimate (~0.5%)', fontsize=8, va='bottom', ha='right', color='black')

seen = set()
for name, yr, err, fam in methods:
    c = families[fam]
    m = markers[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    ax1.scatter(yr + np.random.uniform(-0.05, 0.05), err, color=c, marker=m, s=70,
                edgecolors='black', linewidths=0.4, label=label, zorder=3)
    dx, dy = (0.15, 0.18)
    if name in ('soft-SVM poly4',): dy = -0.45
    if name in ('poly SVM d=9',): dy = 0.35; dx = -0.1
    if name in ('1-NN',): dy = -0.45
    ax1.annotate(name, (yr, err), xytext=(yr + dx, err + dy), fontsize=8)

ax1.set_xlim(1994, 2011)
ax1.set_ylim(0, 9)
ax1.set_xlabel('year')
ax1.set_ylabel('MNIST test error (%)')
ax1.set_title('MNIST: classical-method trend by family', fontsize=10)
ax1.legend(fontsize=8, loc='upper right', frameon=False, ncol=2)
ax1.grid(True, ls=':', alpha=0.3)
ax1.spines['top'].set_visible(False); ax1.spines['right'].set_visible(False)

# Right panel: AdaBoost margin-vs-rounds (Letter)
rounds = np.array([5, 10, 50, 100, 500, 1000])
train_err = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
test_err_stumps = np.array([20.0, 13.0, 9.0, 6.6, 5.5, 5.0])
test_err_c45 = np.array([10.5, 7.5, 5.0, 3.5, 3.2, 3.10])

ax2.plot(rounds, test_err_stumps, marker='v', color='C4', linestyle='-', label='AdaBoost stumps test')
ax2.plot(rounds, test_err_c45, marker='^', color='C5', linestyle='-', label='AdaBoost C4.5 test')
ax2.plot(rounds, train_err, marker='o', color='black', linestyle=':', label='train err (both)')
ax2.set_xscale('log')
ax2.set_xlabel('AdaBoost rounds T')
ax2.set_ylabel('UCI Letter error (%)')
ax2.set_title('Boosting: test error keeps falling after train hits 0', fontsize=10)
ax2.legend(fontsize=8, loc='upper right', frameon=False)
ax2.grid(True, ls=':', alpha=0.3)
ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/classical-trends.svg', format='svg', bbox_inches='tight')

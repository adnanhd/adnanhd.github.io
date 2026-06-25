"""Auto-extracted figure generator (source: quantization-aware-training/Quantization-Aware-Training.org).
Regenerates blogs/quantization-aware-training/figures/qat-family-timeline.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt

methods = [
    ('Vanhoucke', 2011, 8.0, 'prod-INT8'),
    ('BNN', 2016, 1.0, 'binary-ternary'),
    ('XNOR-Net', 2016, 1.0, 'binary-ternary'),
    ('DoReFa', 2016, 1.0, 'learnable-scale'),
    ('TWN', 2016, 2.0, 'binary-ternary'),
    ('HWGQ', 2017, 1.0, 'binary-ternary'),
    ('TTQ', 2017, 2.0, 'binary-ternary'),
    ('PACT', 2018, 4.0, 'learnable-scale'),
    ('Jacob', 2018, 8.0, 'prod-INT8'),
    ('Krishnamoorthi', 2018, 8.0, 'prod-INT8'),
    ('LQ-Nets', 2018, 2.0, 'learnable-scale'),
    ('DFQ', 2019, 8.0, 'prod-INT8'),
    ('HAWQ', 2019, 6.0, 'mixed-prec'),
    ('HAQ', 2019, 3.8, 'mixed-prec'),
    ('Q8BERT', 2019, 8.0, 'transformer'),
    ('LSQ W4A4', 2020, 4.0, 'learnable-scale'),
    ('LSQ W3A3', 2020, 3.0, 'learnable-scale'),
    ('LSQ+', 2020, 3.0, 'learnable-scale'),
    ('AdaRound', 2020, 4.0, 'prod-INT8'),
    ('TernaryBERT', 2020, 2.0, 'transformer'),
    ('I-BERT', 2021, 8.0, 'transformer'),
    ('HAWQ-V3', 2021, 4.5, 'mixed-prec'),
    ('FracBits', 2021, 4.0, 'mixed-prec'),
    ('FP8', 2022, 8.0, 'llm-ptq'),
    ('LLM.int8()', 2022, 8.0, 'llm-ptq'),
    ('GPTQ', 2023, 4.0, 'llm-ptq'),
    ('GPTQ W3', 2023, 3.0, 'llm-ptq'),
    ('AWQ', 2023, 4.0, 'llm-ptq'),
    ('SmoothQuant', 2023, 8.0, 'llm-ptq'),
    ('QLoRA', 2023, 4.0, 'llm-ptq'),
    ('SpQR', 2023, 3.0, 'llm-ptq'),
    ('OmniQuant W4A4', 2024, 4.0, 'llm-ptq'),
]
families = {
    'prod-INT8': 'C0', 'binary-ternary': 'C7', 'learnable-scale': 'C2',
    'mixed-prec': 'C1', 'transformer': 'C3', 'llm-ptq': 'C4',
}
markers = {
    'prod-INT8': 'o', 'binary-ternary': 'x', 'learnable-scale': 's',
    'mixed-prec': 'D', 'transformer': '^', 'llm-ptq': 'P',
}

fig, ax = plt.subplots(figsize=(9.5, 4.0))
ax.axhline(8.0, color='black', ls=':', lw=0.8, alpha=0.4)
ax.text(2024.3, 8.15, 'INT8 (TFLite default)', fontsize=8, va='bottom', ha='right', color='black')
ax.axhline(4.0, color='black', ls=':', lw=0.8, alpha=0.4)
ax.text(2024.3, 4.15, 'INT4 (LLM weight-only)', fontsize=8, va='bottom', ha='right', color='black')

seen = set()
for name, yr, bits, fam in methods:
    c = families[fam]
    m = markers[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    ax.scatter(yr + np.random.uniform(-0.08, 0.08), bits + np.random.uniform(-0.05, 0.05),
               color=c, marker=m, s=70, edgecolors='black', linewidths=0.4,
               label=label, zorder=3)
    dx, dy = (0.08, 0.18)
    if name in ('XNOR-Net', 'DoReFa'):
        dy = -0.45
    if name in ('LSQ W3A3',):
        dy = -0.45
    if name in ('Krishnamoorthi',):
        dy = -0.45
    if name in ('AWQ',):
        dy = -0.45
    if name == 'GPTQ W3':
        dy = -0.45
    ax.annotate(name, (yr, bits), xytext=(yr + dx, bits + dy), fontsize=7)

ax.set_xlim(2010.5, 2024.7)
ax.set_ylim(0.3, 9.2)
ax.set_xlabel('year')
ax.set_ylabel('headline weight bit-width')
ax.set_title('QAT/PTQ family evolution: weight-precision frontier vs publication year', fontsize=10)
ax.legend(fontsize=8, loc='lower left', frameon=False, ncol=3)
ax.grid(True, ls=':', alpha=0.3)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/qat-family-timeline.svg', format='svg', bbox_inches='tight')

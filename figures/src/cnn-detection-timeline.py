"""Auto-extracted figure generator (source: computer-vision/CNN-Object-Detection.org).
Regenerates blogs/computer-vision/figures/cnn-detection-timeline.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt

methods = [
    ('Fast R-CNN', 2015, 19.7, 'two-stage'),
    ('Faster R-CNN', 2015, 21.9, 'two-stage'),
    ('YOLO v1', 2016, 21.6, 'one-stage'),
    ('SSD-512', 2016, 28.8, 'one-stage'),
    ('FPN', 2017, 36.2, 'two-stage'),
    ('Mask R-CNN', 2017, 39.8, 'two-stage'),
    ('RetinaNet', 2017, 39.1, 'one-stage'),
    ('YOLO v3', 2018, 33.0, 'one-stage'),
    ('Cascade R-CNN', 2018, 42.8, 'two-stage'),
    ('PANet', 2018, 47.4, 'two-stage'),
    ('CornerNet', 2019, 42.1, 'anchor-free'),
    ('FCOS', 2019, 41.5, 'anchor-free'),
    ('CenterNet', 2019, 42.1, 'anchor-free'),
    ('EfficientDet-D7', 2020, 53.7, 'one-stage'),
    ('YOLO v4', 2020, 43.5, 'one-stage'),
    ('DETR', 2020, 44.9, 'transformer'),
    ('Deformable DETR', 2021, 46.2, 'transformer'),
    ('DINO-DETR', 2022, 58.5, 'transformer'),
    ('Co-DETR', 2023, 66.0, 'transformer'),
]

families = {
    'two-stage': ('C0', 'o'),
    'one-stage': ('C1', 's'),
    'anchor-free': ('C2', '^'),
    'transformer': ('C3', 'D'),
}

fig, ax = plt.subplots(figsize=(9.5, 4.2))

seen = set()
for name, yr, ap, fam in methods:
    color, marker = families[fam]
    label = fam if fam not in seen else None
    seen.add(fam)
    ax.scatter(yr + np.random.uniform(-0.06, 0.06), ap, color=color, marker=marker,
               s=70, edgecolors='black', linewidths=0.4, label=label, zorder=3)
    dx, dy = 0.08, 0.5
    if name in ('Faster R-CNN', 'YOLO v1', 'CenterNet'): dy = -1.4
    if name in ('YOLO v3',): dy = -1.6
    if name in ('FCOS',): dy = -1.6
    if name in ('Mask R-CNN',): dy = 0.7
    if name in ('Deformable DETR',): dy = -1.6
    ax.annotate(name, (yr, ap), xytext=(yr + dx, ap + dy), fontsize=8)

ax.set_xlim(2014.5, 2023.7)
ax.set_ylim(15, 70)
ax.set_xlabel('year')
ax.set_ylabel('COCO val/test-dev AP (%)')
ax.set_title('CNN detection family evolution: COCO AP vs publication year', fontsize=10)
ax.legend(fontsize=8, loc='upper left', frameon=False, ncol=2)
ax.grid(True, ls=':', alpha=0.3)
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('figures/cnn-detection-timeline.svg', format='svg', bbox_inches='tight')

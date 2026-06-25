"""Auto-extracted figure generator (source: generative-models/Autoregressive-Models.org).
Regenerates blogs/generative-models/figures/ar-causal-masking.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.6), gridspec_kw={'width_ratios': [1.0, 1.0, 1.1]})

# Panel 1: raster-AR causal mask on a 4x4 grid
ax = axes[0]
n = 4
ax.set_xlim(-0.5, n - 0.5); ax.set_ylim(-0.5, n - 0.5)
ax.set_aspect('equal'); ax.invert_yaxis()
ax.set_xticks([]); ax.set_yticks([])

# fill cells with raster index
for r in range(n):
    for c in range(n):
        idx = r * n + c
        # current pixel position (red), past (light blue), future (gray)
        if r == 2 and c == 1:
            color = '#ff7878'
        elif idx < 2 * n + 1:
            color = '#9ec5ff'
        else:
            color = '#dcdcdc'
        ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1, fc=color, ec='black', lw=0.8))
        ax.text(c, r, str(idx), ha='center', va='center', fontsize=8)

ax.set_title('Raster-scan AR mask\n(red = current, blue = past, gray = future)', fontsize=10)
ax.set_xlabel(r'token $i$ attends to tokens $j < i$ in raster order', fontsize=8)

# Panel 2: VAR block-causal scale mask
ax = axes[1]
scales = [1, 2, 4]
sizes = [s * s for s in scales]
total = sum(sizes)
M = np.zeros((total, total))
offsets = [0]
for s in sizes[:-1]:
    offsets.append(offsets[-1] + s)
for si, s in enumerate(sizes):
    block_start = offsets[si]
    block_end = block_start + s
    # within scale: bidirectional (1)
    M[block_start:block_end, block_start:block_end] = 1.0
    # earlier scales visible (1)
    M[block_start:block_end, :block_start] = 1.0
ax.imshow(M, cmap='Blues', vmin=0, vmax=1.5, aspect='equal')
ax.set_xticks([]); ax.set_yticks([])

# Draw scale block boundaries
for off in offsets[1:]:
    ax.axhline(off - 0.5, color='black', lw=1.2)
    ax.axvline(off - 0.5, color='black', lw=1.2)
# Annotate scales on the diagonal
labels = [r'scale 1 ($1^2$)', r'scale 2 ($2^2$)', r'scale 3 ($4^2$)']
for si, (off, sz) in enumerate(zip(offsets, sizes)):
    ax.text(off + sz / 2 - 0.5, off + sz / 2 - 0.5, labels[si],
            ha='center', va='center', fontsize=8, weight='bold')
ax.set_title('VAR block-causal scale mask\n(parallel within scale, causal across)', fontsize=10)
ax.set_xlabel('keys (earlier scales)', fontsize=8)
ax.set_ylabel('queries', fontsize=8)

# Panel 3: MaskGIT iterative parallel decoding cosine schedule
ax = axes[2]
T_steps = 8
t = np.arange(T_steps + 1)
gamma = np.cos(np.pi * t / (2 * T_steps))
masked = np.round(256 * gamma).astype(int)
unmasked = 256 - masked
ax.bar(t, unmasked, color='#7fb8e8', edgecolor='black', lw=0.6, label='unmasked tokens')
ax.bar(t, masked, bottom=unmasked, color='#dcdcdc', edgecolor='black', lw=0.6, label='[MASK]')

ax.set_xticks(t)
ax.set_xlabel('iteration $t$', fontsize=9)
ax.set_ylabel('tokens (out of 256)', fontsize=9)
ax.set_title(r'MaskGIT cosine schedule $\gamma(t)=\cos(\pi t / 2T)$', fontsize=10)
ax.legend(loc='upper left', fontsize=8)
ax.set_ylim(0, 280)

# annotate selected steps
for ti in [0, 4, T_steps]:
    ax.text(ti, masked[ti] + unmasked[ti] + 8, f'{unmasked[ti]} kept',
            ha='center', fontsize=7)

plt.tight_layout()
plt.savefig('figures/ar-causal-masking.svg', format='svg', bbox_inches='tight')

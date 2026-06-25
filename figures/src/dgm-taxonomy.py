"""Auto-extracted figure generator (source: generative-models/Deep-Generative-Models.org).
Regenerates blogs/generative-models/figures/dgm-taxonomy.svg. Run via figures/build.py.
"""
import matplotlib
matplotlib.use("Agg")
import numpy as np
np.random.seed(0)  # deterministic jitter so re-runs don't churn

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(13.5, 5.6))
ax.set_xlim(0, 18); ax.set_ylim(0, 9); ax.axis('off')

paradigms = [
    {'name': 'VAE', 'x': 1.3, 'color': '#cfe5ff', 'border': '#1f77b4',
     'objective': r'maximise ELBO',
     'eq': r'$\log p(x) \geq \mathbb{E}_q[\log p(x|z)] - D_{\rm KL}(q\|p)$',
     'sample': r'$z \sim q$;  $x \sim p(\cdot|z)$',
     'props': ['exact ELBO', 'amortised inference', 'blurry samples', 'posterior collapse risk'],
     'examples': r'$\beta$-VAE, NVAE, VQ-VAE'},
    {'name': 'GAN', 'x': 4.7, 'color': '#ffd6d6', 'border': '#d62728',
     'objective': r'minimax adversarial',
     'eq': r'$\min_G \max_D V(D,G)$',
     'sample': r'$z \sim p_z$;  $x = G(z)$',
     'props': ['no likelihood', 'sharp samples', 'mode collapse', 'unstable training'],
     'examples': r'DCGAN, WGAN, StyleGAN, BigGAN'},
    {'name': 'Flow', 'x': 8.1, 'color': '#bfe0bf', 'border': '#2ca02c',
     'objective': r'exact log-likelihood',
     'eq': r'$\log p(x) = \log p_z(f^{-1}(x)) + \log|\det J|$',
     'sample': r'$z \sim p_z$;  $x = f(z)$ (bijective)',
     'props': ['exact density', 'invertible $f$', 'limited expressiveness', '$\\dim z = \\dim x$'],
     'examples': 'Real NVP, Glow, NSF, FFJORD'},
    {'name': 'Diffusion', 'x': 11.5, 'color': '#fff1c2', 'border': '#9467bd',
     'objective': r'denoising score matching',
     'eq': r'$\mathcal{L} = \mathbb{E}_{t,\epsilon}[\|\epsilon_\theta(x_t,t)-\epsilon\|^2]$',
     'sample': r'$x_T \sim \mathcal{N}(0,I)$, iter denoise',
     'props': ['exact NLL bound', 'sharp + diverse', '50--1000 NFE', 'mode-covering'],
     'examples': 'DDPM, Score SDE, EDM, LDM'},
    {'name': 'AR', 'x': 14.9, 'color': '#f0c870', 'border': '#ff7f0e',
     'objective': r'next-token prediction',
     'eq': r'$\log p(x) = \sum_i \log p(x_i \mid x_{<i})$',
     'sample': r'sequential, $x_i \sim p(\cdot|x_{<i})$',
     'props': ['exact likelihood', 'sequential decode', 'discrete tokens', 'KV cache amortised'],
     'examples': 'PixelCNN, DALL-E, Parti, VAR'},
]

for p in paradigms:
    # title box
    ax.add_patch(FancyBboxPatch((p['x'] - 1.2, 7.6), 2.7, 1.0, boxstyle='round,pad=0.04',
                                ec=p['border'], fc=p['color'], lw=2.0))
    ax.text(p['x'] + 0.15, 8.1, p['name'], ha='center', va='center', fontsize=14, weight='bold')
    # objective
    ax.text(p['x'] + 0.15, 7.0, p['objective'], ha='center', va='center', fontsize=8, style='italic')
    # equation
    ax.text(p['x'] + 0.15, 6.3, p['eq'], ha='center', va='center', fontsize=7)
    # sampling
    ax.text(p['x'] + 0.15, 5.5, 'sample: ' + p['sample'], ha='center', va='center', fontsize=7)
    # props
    for i, prop in enumerate(p['props']):
        bullet = '+' if i < 2 else '-'
        col = '#155715' if i < 2 else '#7a1414'
        ax.text(p['x'] + 0.15, 4.7 - i * 0.55, f'{bullet} {prop}', ha='center', va='center',
                fontsize=7, color=col)
    # examples
    ax.text(p['x'] + 0.15, 1.7, p['examples'], ha='center', va='center', fontsize=7,
            color='#444', style='italic')
    # sample-quality axis tick
    ax.text(p['x'] + 0.15, 1.0, '', ha='center')

# Convergence ribbon at top
ax.text(9, 8.7, 'Five paradigms; common transport-map framework (Score SDE / Flow Matching / Schrodinger Bridge)',
        ha='center', va='center', fontsize=10, weight='bold', color='#333')

# axis at bottom
ax.annotate('', xy=(17.2, 0.5), xytext=(0.5, 0.5),
            arrowprops=dict(arrowstyle='->', lw=1.0, color='#666'))
ax.text(0.5, 0.2, 'fast sampling', fontsize=8, ha='left', color='#666')
ax.text(17.2, 0.2, 'slow sampling', fontsize=8, ha='right', color='#666')

# Sample-quality bar (illustrative ranking)
quality = {'VAE': 4, 'GAN': 8, 'Flow': 5, 'Diffusion': 9, 'AR': 9}
for p in paradigms:
    q = quality[p['name']]
    h = q * 0.06
    ax.add_patch(plt.Rectangle((p['x'] - 0.2, 0.7), 0.7, h, color=p['border'], alpha=0.7))
    ax.text(p['x'] + 0.15, 0.7 + h + 0.05, f'q={q}', ha='center', fontsize=7, color=p['border'])

plt.tight_layout()
plt.savefig('figures/dgm-taxonomy.svg', format='svg', bbox_inches='tight')

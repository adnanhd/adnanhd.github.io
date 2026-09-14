"""Generate blog HTML pages from org-roam notes via pandoc.

Run:  python -m builder.build_blogs

Blogs are PRE-GENERATED and committed; the main site build (`python -m builder`)
does not read the org sources, which live outside the repo under ~/org/roam2.

Each BlogSpec lists one or more org files; the `Related Work` section of each is
extracted, footnote labels are namespaced per-file (to avoid collisions when
combining), and the sections are concatenated under per-file H2 subheadings.
Pandoc renders org -> HTML5 with native MathML (no JS) and citeproc-resolved
citations from the folder's shared .bib.
"""

import re
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

import yaml

from .build_config import BASE_DIR

ORG_ROOT = Path.home() / "org" / "roam2" / "informatics"
SITE_URL = "https://adnanhd.github.io"
AUTHOR = "Adnan Harun Dogan"
FALLBACK_OG_IMAGE = "assets/img/profile.jpeg"


def _blog_dates():
    """Map slug -> ISO datePublished from data/blogs.yaml (best effort)."""
    out = {}
    try:
        data = yaml.safe_load((BASE_DIR / "data" / "blogs.yaml").read_text()) or {}
        for blog in data.get("blogs", []):
            path = blog.get("path", "")
            parts = path.split("/")
            if len(parts) >= 2 and parts[0] == "blogs" and blog.get("date"):
                iso = str(blog["date"]).strip().replace(" ", "T")
                out[parts[1]] = iso
    except (OSError, yaml.YAMLError):
        pass
    return out


def _make_og_image(html, out_dir, slug):
    """Rasterize the post's first figure to og-image.png (1200px, white bg) for
    social previews, since SVGs don't render as OG images. Returns the image
    path relative to the site root; falls back to the profile photo."""
    m = re.search(r'src="(figures/[^"]+\.svg)"', html)
    if m and shutil.which("rsvg-convert"):
        src = out_dir / m.group(1)
        dst = out_dir / "og-image.png"
        if src.exists():
            try:
                subprocess.run(
                    ["rsvg-convert", "-w", "1200", "-b", "white",
                     str(src), "-o", str(dst)],
                    check=True, capture_output=True,
                )
                return f"blogs/{slug}/og-image.png"
            except (OSError, subprocess.CalledProcessError):
                pass
    return FALLBACK_OG_IMAGE


@dataclass
class BlogSpec:
    slug: str
    title: str
    meta: str
    description: str
    sources: list[Path]                # org files whose Related Work is combined
    bib: Path | None = None
    section_prefix: str = "Related Work"   # heading prefix to extract


# --- org preprocessing ------------------------------------------------------

def _extract_section(text, prefix):
    """Body of the first heading (any level) whose title starts with `prefix`.

    Captures until the next heading of the same or higher level, so nested
    subsections (e.g. a `*** SoTA Leaderboard` under a `** Related Work`) are
    kept. Handles both top-level `* Related Work` and nested `** Related Work`.
    """
    out, level = [], None
    for line in text.splitlines():
        m = re.match(r"^(\*+)\s+(.*)", line)
        if m:
            stars, title = len(m.group(1)), m.group(2).strip()
            if level is None:
                if title.startswith(prefix):
                    level = stars
                continue
            if stars <= level:
                break          # next sibling/parent heading ends the section
            out.append(line)   # deeper heading: part of the section
            continue
        if level is not None:
            out.append(line)
    return "\n".join(out).strip()


def _strip_noise(org_text):
    """Drop babel src blocks and property drawers - not wanted in prose blogs."""
    org_text = re.sub(r"^#\+begin_src.*?^#\+end_src\s*$", "", org_text,
                      flags=re.S | re.M | re.I)
    org_text = re.sub(r"^\s*:PROPERTIES:.*?^\s*:END:\s*$", "", org_text,
                      flags=re.S | re.M | re.I)
    return org_text


def _title_of(text):
    m = re.search(r"^#\+TITLE:\s*(.+)$", text, flags=re.M)
    return m.group(1).strip() if m else ""


def _namespace_footnotes(text, prefix):
    """Prefix named footnote labels so combined files don't collide."""
    return re.sub(r"\[fn:([\w-]+)", rf"[fn:{prefix}-\1", text)


def _assemble(spec):
    """Concatenate the Related Work sections of all sources into one org doc."""
    multi = len(spec.sources) > 1
    parts = []
    for i, src in enumerate(spec.sources):
        raw = src.read_text()
        section = _strip_noise(_extract_section(raw, spec.section_prefix))
        if not section:
            continue
        section = _namespace_footnotes(section, f"s{i}")
        if multi:
            # demote the file's inner headings one level so they nest under its H2
            section = re.sub(r"^(\*+)(\s)", r"*\1\2", section, flags=re.M)
            parts.append(f"** {_title_of(raw)}\n\n{section}")
        else:
            parts.append(section)
    return "\n\n".join(parts)


# --- pandoc + HTML postprocessing ------------------------------------------

def _pandoc(org_text, bib):
    cmd = ["pandoc", "-f", "org", "-t", "html5", "--mathml", "--no-highlight"]
    if bib and bib.exists():
        cmd += ["--citeproc", "--bibliography", str(bib)]
    return subprocess.run(cmd, input=org_text, capture_output=True, text=True,
                          check=True).stdout


def _postprocess(html, org_dir, out_dir):
    """Neutralize internal org links and copy referenced figures locally."""
    # [[id:...]] cross-note links -> plain text. pandoc wraps output, so <a and
    # href may be separated by a newline.
    html = re.sub(r'<a\s+href="id:[^"]*"[^>]*>(.*?)</a>', r"\1", html, flags=re.S)

    # Copy only figures not already present locally: figures are owned by
    # figures/build.py (in-repo generators), so we don't clobber them here --
    # we only fill in anything missing from the org source.
    figs = set(re.findall(r'src="(figures/[^"]+)"', html))
    if figs:
        (out_dir / "figures").mkdir(parents=True, exist_ok=True)
        for rel in figs:
            src = org_dir / rel
            dst = out_dir / rel
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)

    html = re.sub(r"<table\b", '<div class="blog-table"><table', html)
    html = html.replace("</table>", "</table></div>")
    html = html.replace('<div id="refs"',
                        '<h2 class="blog-refs-title">References</h2>\n<div id="refs"')
    return html


def _normalize_punctuation(text):
    """Normalize AI-tell unicode punctuation to plain ASCII.

    em/en dashes -> hyphens (numeric ranges close up; parenthetical dashes become
    a spaced hyphen), smart quotes -> straight, ellipsis -> three dots. Operates on
    the rendered page; MathML uses U+2212 minus (untouched) so equations are safe.
    """
    text = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1-\2", text)  # 10–20 -> 10-20
    text = re.sub(r"\s*[–—]\s*", " - ", text)            # a — b / a–b -> a - b
    text = (text.replace("“", '"').replace("”", '"')      # “ ” -> "
                .replace("‘", "'").replace("’", "'")      # ‘ ’ -> '
                .replace("…", "..."))                          # … -> ...
    text = (text.replace("&mdash;", " - ").replace("&ndash;", "-")
                .replace("&hellip;", "...")
                .replace("&ldquo;", '"').replace("&rdquo;", '"')
                .replace("&lsquo;", "'").replace("&rsquo;", "'"))
    return text


BLOG_SHELL = """<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="description" content="{description_attr}" />
        <title>{title_attr} - Adnan Harun Dogan</title>
        <link rel="canonical" href="{url}" />
        <meta property="og:type" content="article" />
        <meta property="og:site_name" content="Adnan Harun Dogan" />
        <meta property="og:title" content="{title_attr}" />
        <meta property="og:description" content="{description_attr}" />
        <meta property="og:url" content="{url}" />
        <meta property="og:image" content="{og_image}" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="{title_attr}" />
        <meta name="twitter:description" content="{description_attr}" />
        <meta name="twitter:image" content="{og_image}" />
        <script type="application/ld+json">
{json_ld}
        </script>
        <link rel="stylesheet" href="../../assets/css/vendor.css" />
        <link rel="stylesheet" href="../../assets/css/style.css" />
        <link rel="icon" type="image/jpeg" href="../../assets/img/profile-sm.jpeg" />
    </head>
    <body>
        <div class="blog-page">
            <a href="../../index.html?tab=blogs" class="blog-back">&larr; Back to blogs</a>
            <h1>{title}</h1>
            <div class="blog-meta">{meta}</div>
            <article class="blog-body">
{body}
            </article>
        </div>
        <script>
            const saved = localStorage.getItem("theme");
            if (saved) document.documentElement.setAttribute("data-theme", saved);
            else if (window.matchMedia("(prefers-color-scheme: dark)").matches)
                document.documentElement.setAttribute("data-theme", "dark");
        </script>
    </body>
</html>
"""


def build_blog(spec):
    org_text = _assemble(spec)
    if not org_text.strip():
        print(f"Warning: no Related Work found for {spec.slug}, skipping", file=sys.stderr)
        return
    body = _pandoc(org_text, spec.bib)

    out_dir = BASE_DIR / "blogs" / spec.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    body = _postprocess(body, spec.sources[0].parent, out_dir)

    url = f"{SITE_URL}/blogs/{spec.slug}/"
    og_image = f"{SITE_URL}/{_make_og_image(body, out_dir, spec.slug)}"
    ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": spec.title,
        "description": spec.description,
        "url": url,
        "image": og_image,
        "author": {"@type": "Person", "name": AUTHOR, "url": SITE_URL + "/"},
        "publisher": {"@type": "Person", "name": AUTHOR},
        "mainEntityOfPage": url,
    }
    date_iso = _blog_dates().get(spec.slug)
    if date_iso:
        ld["datePublished"] = date_iso
    json_ld = json.dumps(ld, indent=2, ensure_ascii=False)

    page = BLOG_SHELL.format(
        title=spec.title, title_attr=escape(spec.title),
        description_attr=escape(spec.description), meta=spec.meta, body=body,
        url=url, og_image=og_image, json_ld=json_ld,
    )
    page = _normalize_punctuation(page)
    (out_dir / "index.html").write_text(page)
    print(f"Built blogs/{spec.slug}/index.html ({len(page):,} bytes)")


# --- registry of blogs to generate -----------------------------------------

def _folder_sources(folder):
    """All topic .org files in a folder, sorted, excluding index/sitemap."""
    skip = {"index", "sitemap"}
    return sorted(p for p in folder.glob("*.org") if p.stem not in skip)


def _spec(slug, title, meta, description, folder):
    f = ORG_ROOT / folder
    return BlogSpec(slug=slug, title=title, meta=meta, description=description,
                    sources=_folder_sources(f), bib=f / f"{folder}.bib")


def _spec1(slug, folder, filename, title, meta, description):
    """A single-file post: one org chapter, the folder's bibliography."""
    f = ORG_ROOT / folder
    return BlogSpec(slug=slug, title=title, meta=meta, description=description,
                    sources=[f / filename], bib=f / f"{folder}.bib")


BLOGS = [
    # One post per chapter file: short, densely-scoped posts instead of
    # one giant survey per field. Sources stay the org notes verbatim.
    BlogSpec(
        slug="policy-gradient-foundations",
        title="Policy Gradients: REINFORCE, Baselines, and Generalized Advantage Estimation",
        meta="Policy gradient theorem, REINFORCE, variance reduction, GAE",
        description="The policy gradient theorem, REINFORCE, baseline subtraction "
                    "and advantage functions, and generalized advantage estimation.",
        sources=[ORG_ROOT / "reinforcement-learning" / "01-policy-gradient-foundations.org"],
        bib=ORG_ROOT / "reinforcement-learning" / "reinforcement-learning.bib",
    ),
    BlogSpec(
        slug="trust-region-methods",
        title="Trust-Region Policy Methods: TRPO, PPO, and GRPO",
        meta="Trust-region and proximal policy optimization",
        description="Trust region policy optimization, proximal policy optimization, "
                    "group relative policy optimization, and why implementation details matter.",
        sources=[ORG_ROOT / "reinforcement-learning" / "02-trust-region-methods.org"],
        bib=ORG_ROOT / "reinforcement-learning" / "reinforcement-learning.bib",
    ),
    BlogSpec(
        slug="actor-critic-distributed",
        title="Actor-Critic and Distributed RL: DDPG, TD3, SAC, and Beyond",
        meta="Deterministic and soft actor-critic methods, distributed training",
        description="Deep deterministic policy gradients, twin delayed DDPG, "
                    "soft actor-critic, and distributed reinforcement learning.",
        sources=[ORG_ROOT / "reinforcement-learning" / "03-actor-critic-distributed.org"],
        bib=ORG_ROOT / "reinforcement-learning" / "reinforcement-learning.bib",
    ),
    BlogSpec(
        slug="offline-model-based-rl",
        title="Offline and Model-Based RL: CQL, Decision Transformer, DPO, and World Models",
        meta="Offline RL, sequence models, preference optimization, world models",
        description="Conservative Q-learning, the decision transformer, direct "
                    "preference optimization, and world-model agents.",
        sources=[ORG_ROOT / "reinforcement-learning" / "04-offline-model-based.org"],
        bib=ORG_ROOT / "reinforcement-learning" / "reinforcement-learning.bib",
    ),
    _spec1("cnn-object-detection", "computer-vision", "CNN-Object-Detection.org",
           "CNN Object Detection: From LeNet and AlexNet to Modern Detector Backbones",
           "Convolutional backbones and CNN-based object detection",
           "LeNet, AlexNet, VGG, ResNet, Inception, and the CNN object detection lineage built on them."),
    _spec1("vision-transformers", "computer-vision", "Vision-Transformers.org",
           "Vision Transformers: ViT, Self-Attention, and the CNN Comparison",
           "The ViT architecture and its trade-offs against CNNs",
           "The ViT architecture, multi-head self-attention, position encodings, and how vision transformers compare with CNNs."),
    _spec1("detection-segmentation-transformers", "computer-vision", "Detection-Segmentation-Transformers.org",
           "Detection and Segmentation Transformers: DETR and Its Descendants",
           "Set prediction, bipartite matching, deformable attention",
           "End-to-end detection with DETR, bipartite matching and the set prediction loss, deformable attention, and segmentation transformers."),
    _spec1("self-supervised-learning", "deep-learning", "Self-Supervised-Learning.org",
           "Self-Supervised Representation Learning: Instance Discrimination and InfoNCE",
           "Contrastive pretraining of visual representations",
           "Instance discrimination, the InfoNCE loss, alignment and uniformity, and the augmentation pipeline behind contrastive pretraining."),
    _spec1("knowledge-distillation", "deep-learning", "knowledge-distillation.org",
           "Knowledge Distillation: Soft Labels, Temperature, and Dark Knowledge",
           "Teacher-student training with temperature-scaled softmax",
           "Hard versus soft labels, temperature-scaled softmax, the distillation objective, and what dark knowledge actually transfers."),
    _spec1("deep-generative-models", "generative-models", "Deep-Generative-Models.org",
           "Variational Autoencoders: The ELBO and the Reparameterization Trick",
           "The VAE framework and its training objective",
           "The VAE framework, the evidence lower bound, the reparameterization trick, and importance weighted autoencoders."),
    _spec1("autoregressive-models", "generative-models", "Autoregressive-Models.org",
           "Autoregressive Image Generation: PixelRNN, PixelCNN, and VQ-VAE",
           "Pixel-level autoregression and discrete latent codes",
           "PixelRNN, masked convolutions in PixelCNN, conditional generation, and vector-quantized latent spaces."),
    _spec1("diffusion-transformers", "generative-models", "Diffusion-Transformers.org",
           "Diffusion Models and DiT: Noise Schedules, DDIM, and Scalable Transformers",
           "Denoising diffusion and transformer backbones for generation",
           "Forward and reverse diffusion, noise schedules, DDIM sampling, the score-based view, and scalable diffusion transformers."),
    _spec1("vision-language-models", "generative-models", "Vision-Language-Models.org",
           "Vision-Language Models: CLIP, ALIGN, and SigLIP",
           "Contrastive image-text pretraining and zero-shot transfer",
           "Contrastive language-image pretraining, zero-shot transfer, scaling with noisy pairs, and sigmoid-loss variants."),
    _spec1("optimal-transport", "optimization", "Optimal-Transport.org",
           "Optimal Transport: From Exact Linear Programs to Sinkhorn and Neural Potentials",
           "Four generations of OT solvers",
           "Exact LP formulations, entropic regularization and Sinkhorn, sliced OT, and unbalanced / Gromov-Wasserstein extensions."),
    _spec1("bayesian-optimization", "optimization", "Bayesian-Optimization.org",
           "Bayesian Optimization with Gaussian Process Surrogates",
           "GP posteriors, covariance functions, acquisition strategies",
           "Gaussian process surrogates, posterior inference, covariance functions, and hyperparameter learning for black-box optimization."),
    _spec1("constrained-optimization-learning", "optimization", "Constrained-Optimization-Learning.org",
           "Differentiating Through Constrained Optimization: Implicit Layers and Convex Programs",
           "Implicit differentiation and optimization layers in deep networks",
           "Implicit differentiation of optimality conditions, perturbation methods, differentiable convex layers, and input convex networks."),
    _spec1("probabilistic-dl-foundations", "probabilistic-deep-learning", "01-foundations.org",
           "Probabilistic Deep Learning Foundations: Tractability versus Generality",
           "Exact inference, intractability, and approximation",
           "Exact inference under structural constraints, why neural generality breeds intractability, and approximation as a necessity."),
    _spec1("bayesian-neural-networks", "probabilistic-deep-learning", "02-bayesian-neural-networks.org",
           "Bayesian Neural Networks: Evidence, HMC, and Function-Space Bayes",
           "The Bayesian program for deep networks",
           "The Bayesian program for neural networks, evidence and Occam factors, HMC, the NNGP limit, and mode-averaging ensembles."),
    _spec1("posterior-approximation", "probabilistic-deep-learning", "03-posterior-approximation.org",
           "Posterior Approximation: Variational Inference from Mean-Field to Cold Posteriors",
           "The ELBO, SVI, and the limits of Gaussian mean-field",
           "Variational inference and the ELBO, stochastic VI, mean-field Gaussian BNNs, tight bounds, and the cold posterior effect."),
    _spec1("gaussian-processes-deep-kernels", "probabilistic-deep-learning", "04-gaussian-processes-deep-kernels.org",
           "Gaussian Processes and Deep Kernel Learning",
           "GP regression, marginal likelihood, scalable approximations",
           "The GP prior, posterior mean and variance, marginal likelihood, computational costs, and deep kernel learning."),
    _spec1("uncertainty-quantification", "probabilistic-deep-learning", "05-uncertainty-quantification.org",
           "Uncertainty Quantification: Predictive Variance, MC Dropout, and Deep Ensembles",
           "Aleatoric and epistemic uncertainty in deep models",
           "The predictive variance decomposition, heteroscedastic heads with MC dropout, prior networks, and deep ensembles."),
    _spec1("statistical-learning-foundations", "statistical-deep-learning", "01-classical-foundations.org",
           "Classical Statistical Learning: ERM, Capacity Control, and Uniform Convergence",
           "The classical generalization theory deep learning inherited",
           "Empirical risk minimization, maximum likelihood as M-estimation, capacity control, and the classical uniform-convergence toolkit."),
    _spec1("pac-bayes-generalization", "statistical-deep-learning", "02-pac-bayes-generalization.org",
           "PAC-Bayes Generalization Bounds: From McAllester to Nonvacuous Bounds",
           "PAC-Bayes bounds and their deep-learning revival",
           "The McAllester bound, deterministic versus stochastic classifiers, refinements, and nonvacuous bounds for deep networks."),
    _spec1("ntk-infinite-width", "statistical-deep-learning", "03-ntk-infinite-width.org",
           "The Neural Tangent Kernel and Infinite-Width Networks",
           "Gradient-flow ODEs, the NTK theorem, and its limits",
           "The NTK definition and parameterization, the gradient-flow ODE, the convergence theorem, and where the kernel picture breaks."),
    _spec1("benign-overfitting-double-descent", "statistical-deep-learning", "04-benign-overfitting-double-descent.org",
           "Benign Overfitting and Double Descent",
           "Interpolation without catastrophe and the double-descent curve",
           "The double-descent curve, deep double descent, experimental protocol nuances, and the dynamical picture of benign overfitting."),
    _spec1("scaling-laws", "statistical-deep-learning", "05-scaling-information.org",
           "Neural Scaling Laws: Kaplan, Chinchilla, and Compute-Optimal Training",
           "Empirical scaling laws and compute-optimal model sizing",
           "Kaplan scaling laws, Chinchilla compute-optimal training, and the earlier empirical scaling literature."),
    _spec1("quantization-aware-training", "quantization-aware-training", "Quantization-Aware-Training.org",
           "Quantization-Aware Training: Scales, Granularity, and Calibration",
           "Low-precision training and inference for deep networks",
           "Uniform affine quantization, symmetric versus asymmetric schemes, per-tensor versus per-channel granularity, and calibration."),
    _spec1("inertial-motion-capture", "inertial-motion-capture", "Inertial-Motion-Capture.org",
           "Sparse Inertial Motion Capture: IMU Models, Orientation, and Sensor Fusion",
           "IMU-based pose estimation from sparse sensors",
           "IMU measurement models, orientation estimation, sparse sensor configurations, and coordinate-frame handling."),
]



def main():
    if not ORG_ROOT.exists():
        print(f"Error: org root not found: {ORG_ROOT}", file=sys.stderr)
        sys.exit(1)
    if not shutil.which("pandoc"):
        print("Error: pandoc not found", file=sys.stderr)
        sys.exit(1)
    for spec in BLOGS:
        existing = [s for s in spec.sources if s.exists()]
        if not existing:
            print(f"Warning: no sources for {spec.slug}, skipping", file=sys.stderr)
            continue
        spec.sources = existing
        build_blog(spec)


if __name__ == "__main__":
    main()

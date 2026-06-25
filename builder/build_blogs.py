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
        <link rel="stylesheet" href="../../assets/css/style.css" />
        <link rel="icon" type="image/jpeg" href="../../assets/img/profile-sm.jpeg" />
    </head>
    <body>
        <div class="blog-page">
            <a href="../../index.html" class="blog-back">&larr; Back to home</a>
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


BLOGS = [
    # RL stays as the single comprehensive cross-chapter survey already published.
    BlogSpec(
        slug="reinforcement-learning",
        title="Reinforcement Learning",
        meta="A survey of 30+ RL models - from REINFORCE to MuZero and DPO",
        description="A survey of reinforcement learning models: policy gradients, "
                    "trust-region and actor-critic methods, distributed training, "
                    "model-based RL, and offline / preference-based learning.",
        sources=[ORG_ROOT / "reinforcement-learning" / "01-policy-gradient-foundations.org"],
        bib=ORG_ROOT / "reinforcement-learning" / "reinforcement-learning.bib",
    ),
    _spec("computer-vision", "Computer Vision",
          "CNN detectors, vision transformers, and detection/segmentation transformers",
          "A survey of computer-vision models: CNN-based object detection, vision "
          "transformers, and detection & segmentation transformers.",
          "computer-vision"),
    _spec("self-supervised-learning", "Self-Supervised Representation Learning",
          "Self-supervised pretraining and knowledge distillation",
          "A survey of self-supervised visual representation learning and knowledge "
          "distillation.",
          "deep-learning"),
    _spec("generative-models", "Generative Models",
          "Deep generative models, autoregressive generation, diffusion, and VLMs",
          "A survey of generative models: deep generative models, autoregressive "
          "visual generation, diffusion transformers, and vision-language models.",
          "generative-models"),
    _spec("optimization", "Optimization for Machine Learning",
          "Optimal transport, Bayesian optimization, and constrained learning",
          "A survey of optimization in machine learning: optimal transport, Bayesian "
          "optimization, and constrained optimization.",
          "optimization"),
    _spec("probabilistic-deep-learning", "Probabilistic Deep Learning",
          "Bayesian neural networks, posterior approximation, GPs, and uncertainty",
          "A survey of probabilistic deep learning: Bayesian neural networks, "
          "posterior approximation, Gaussian processes, and uncertainty quantification.",
          "probabilistic-deep-learning"),
    _spec("statistical-deep-learning", "Statistical Deep Learning",
          "PAC-Bayes, NTK, benign overfitting / double descent, and scaling laws",
          "A survey of statistical deep learning: PAC-Bayes generalization, the neural "
          "tangent kernel, benign overfitting / double descent, and scaling laws.",
          "statistical-deep-learning"),
    _spec("quantization-aware-training", "Quantization-Aware Training",
          "Low-precision deep network training and inference",
          "A survey of quantization-aware training for low-precision deep networks.",
          "quantization-aware-training"),
    _spec("inertial-motion-capture", "Sparse Inertial Motion Capture",
          "IMU-based pose estimation and sensor fusion",
          "A survey of sparse inertial motion capture: IMU-based pose estimation and "
          "sensor fusion.",
          "inertial-motion-capture"),
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

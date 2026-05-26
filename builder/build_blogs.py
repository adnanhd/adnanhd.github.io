"""Generate blog HTML pages from org-roam notes via pandoc.

Run:  python -m builder.build_blogs

Blogs are PRE-GENERATED and committed; the main site build (`python -m builder`)
does not read the org sources, which live outside the repo under ~/org/roam2.
Each blog is defined by a BlogSpec: an org file, the section to extract, and
output metadata. Pandoc renders org -> HTML5 with native MathML (no JS) and
citeproc-resolved citations from the note's .bib.
"""

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .build_config import BASE_DIR

ORG_ROOT = Path.home() / "org" / "roam2" / "informatics"


@dataclass
class BlogSpec:
    slug: str                      # output dir under blogs/
    title: str
    meta: str                      # date / byline line
    description: str
    org_file: Path                 # source .org
    section: str = "Related Work"  # top-level heading to extract ("" = whole file)
    bib: Path | None = None        # bibliography for citeproc


# --- org preprocessing ------------------------------------------------------

def _extract_section(text, heading):
    """Return the body of the top-level `* heading` section (heading line dropped)."""
    if not heading:
        return text
    out, capture = [], False
    for line in text.splitlines():
        if re.match(r"^\*\s", line):
            capture = line.strip() == f"* {heading}"
            continue
        if capture:
            out.append(line)
    return "\n".join(out).strip()


def _strip_noise(org_text):
    """Drop babel src blocks and property drawers — not wanted in prose blogs."""
    org_text = re.sub(r"^#\+begin_src.*?^#\+end_src\s*$", "", org_text,
                      flags=re.S | re.M | re.I)
    org_text = re.sub(r"^\s*:PROPERTIES:.*?^\s*:END:\s*$", "", org_text,
                      flags=re.S | re.M | re.I)
    return org_text


# --- pandoc + HTML postprocessing ------------------------------------------

def _pandoc(org_text, bib):
    cmd = ["pandoc", "-f", "org", "-t", "html5", "--mathml", "--no-highlight"]
    if bib and bib.exists():
        cmd += ["--citeproc", "--bibliography", str(bib)]
    return subprocess.run(cmd, input=org_text, capture_output=True, text=True,
                          check=True).stdout


def _postprocess(html, org_dir, out_dir):
    """Neutralize internal org links and copy referenced figures locally."""
    # [[id:...]] cross-note links -> plain text (targets aren't on the site).
    # pandoc wraps output, so <a and href may be separated by a newline.
    html = re.sub(r'<a\s+href="id:[^"]*"[^>]*>(.*?)</a>', r"\1", html, flags=re.S)

    # copy referenced figures next to the blog, keep relative src
    figs = set(re.findall(r'src="(figures/[^"]+)"', html))
    if figs:
        (out_dir / "figures").mkdir(parents=True, exist_ok=True)
        for rel in figs:
            src = org_dir / rel
            if src.exists():
                shutil.copy2(src, out_dir / rel)

    # wrap tables (which carry attributes) for horizontal scroll on mobile
    html = re.sub(r"<table\b", '<div class="blog-table"><table', html)
    html = html.replace("</table>", "</table></div>")

    # citeproc emits the bibliography without a heading — add one
    html = html.replace('<div id="refs"',
                        '<h2 class="blog-refs-title">References</h2>\n<div id="refs"')
    return html


BLOG_SHELL = """<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="description" content="{description}" />
        <title>{title} - Adnan Harun Dogan</title>
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
    org_text = spec.org_file.read_text()
    section = _strip_noise(_extract_section(org_text, spec.section))
    body = _pandoc(section, spec.bib)

    out_dir = BASE_DIR / "blogs" / spec.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    body = _postprocess(body, spec.org_file.parent, out_dir)

    page = BLOG_SHELL.format(
        title=spec.title, meta=spec.meta, description=spec.description, body=body,
    )
    (out_dir / "index.html").write_text(page)
    print(f"Built blogs/{spec.slug}/index.html ({len(page):,} bytes)")


# --- registry of blogs to generate -----------------------------------------

RL_DIR = ORG_ROOT / "reinforcement-learning"

BLOGS = [
    BlogSpec(
        slug="reinforcement-learning",
        title="Reinforcement Learning",
        meta="A survey of 30+ RL models — from REINFORCE to MuZero and DPO",
        description="A survey of reinforcement learning models: policy gradients, "
                    "trust-region and actor-critic methods, distributed training, "
                    "model-based RL, and offline / preference-based learning.",
        org_file=RL_DIR / "01-policy-gradient-foundations.org",
        section="Related Work",
        bib=RL_DIR / "reinforcement-learning.bib",
    ),
]


def main():
    if not ORG_ROOT.exists():
        print(f"Error: org root not found: {ORG_ROOT}", file=sys.stderr)
        sys.exit(1)
    if not shutil.which("pandoc"):
        print("Error: pandoc not found", file=sys.stderr)
        sys.exit(1)
    for spec in BLOGS:
        if not spec.org_file.exists():
            print(f"Warning: missing {spec.org_file}, skipping {spec.slug}", file=sys.stderr)
            continue
        build_blog(spec)


if __name__ == "__main__":
    main()

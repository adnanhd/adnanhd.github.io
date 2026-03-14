"""
LaTeX resume generation using Jake's Resume template.

Reads YAML data and fills resume_template.tex, then compiles to PDF via pdflatex.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from build_config import (
    AUTHOR_NAME,
    AUTHOR_NAME_ALT,
    BASE_DIR,
    RESUME_OUTPUT_PATH,
    RESUME_TEMPLATE_PATH,
)


# ---------------------------------------------------------------------------
# LaTeX escaping
# ---------------------------------------------------------------------------

_TEX_SPECIAL = {
    '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
    '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\^{}',
}


def tex_escape(text):
    """Escape special LaTeX characters."""
    if not text:
        return ""
    s = str(text)
    for char, repl in _TEX_SPECIAL.items():
        s = s.replace(char, repl)
    return s


AUTHOR_NAME_APA = "Dogan, A. H."


def tex_bold_author(text):
    """Bold the author's name in an already-escaped LaTeX string, converting to APA format."""
    for name in (AUTHOR_NAME, AUTHOR_NAME_ALT):
        escaped = tex_escape(name)
        if escaped in text:
            text = text.replace(escaped, r'\textbf{' + tex_escape(AUTHOR_NAME_APA) + '}')
    return text


def _logo_path(item):
    """Return the logo filename if the logo file exists, else empty string."""
    logo = item.get("logo", "")
    if logo and (BASE_DIR / logo).exists():
        return logo
    return ""


# ---------------------------------------------------------------------------
# Section renderers (each returns a LaTeX string)
# ---------------------------------------------------------------------------

def render_education(data):
    items = (data.get("education") or {}).get("education", [])
    parts = []
    for edu in items:
        logo = _logo_path(edu)
        parts.append(
            f"    \\resumeSubheading"
            f"{{{tex_escape(edu.get('degree', ''))}}}"
            f"{{{tex_escape(str(edu.get('start_date', '')))} -- {tex_escape(str(edu.get('end_date', '')))}}}"
            f"{{{tex_escape(edu.get('institution', ''))}}}"
            f"{{{tex_escape(edu.get('location', ''))}}}"
            f"{{{logo}}}"
        )
    return "\n".join(parts)


def render_experience(data):
    items = (data.get("experience") or {}).get("experience", [])
    parts = []
    for exp in items:
        logo = _logo_path(exp)
        parts.append(
            f"    \\resumeSubheading"
            f"{{{tex_escape(exp.get('position', ''))}}}"
            f"{{{tex_escape(str(exp.get('start_date', '')))} -- {tex_escape(str(exp.get('end_date', '')))}}}"
            f"{{{tex_escape(exp.get('company', ''))}}}"
            f"{{{tex_escape(exp.get('location', ''))}}}"
            f"{{{logo}}}"
        )
        bullets = exp.get("bullets", [])
        description = exp.get("description", "")
        if not bullets and description:
            bullets = [description]
        if bullets:
            parts.append("      \\resumeItemListStart")
            for b in bullets:
                parts.append(f"        \\resumeItem{{{tex_escape(b)}}}")
            parts.append("      \\resumeItemListEnd")
    return "\n".join(parts)


def render_publications(data):
    pubs = [p for p in (data.get("publications") or {}).get("papers", []) if p.get("resume")]
    parts = []
    for paper in pubs:
        authors = tex_bold_author(tex_escape(paper.get("authors", "")))
        title = tex_escape(paper.get("title", ""))
        venue = tex_escape(paper.get("venue_short") or paper.get("venue", ""))
        year = tex_escape(str(paper.get("date", "")))
        # APA format: Author, A. B. (Year). Title. *Venue*.
        ref = f"{authors} ({year}). {title}. \\textbf{{\\emph{{{venue}}}}}."
        parts.append(f"    \\resumeItem{{{ref}}}")
    return "\n".join(parts)


def render_honors(data):
    items = (data.get("extracurricular") or {}).get("honors", [])
    parts = []
    for h in items:
        logo = _logo_path(h)
        parts.append(
            f"    \\resumeSubheading"
            f"{{{tex_escape(h.get('title', ''))}}}"
            f"{{{tex_escape(str(h.get('date', '')))}}}"
            f"{{{tex_escape(h.get('organization', ''))}}}"
            f"{{}}"
            f"{{{logo}}}"
        )
    return "\n".join(parts)


def render_skills(data):
    skills = (data.get("extracurricular") or {}).get("skills", [])
    if not skills:
        return ""
    return f"\\textbf{{Skills}}{{: {', '.join(tex_escape(s) for s in skills)}}}"


# ---------------------------------------------------------------------------
# Logo collection
# ---------------------------------------------------------------------------

def _collect_logos(data):
    """Return set of all logo paths referenced in data."""
    logos = set()
    for section in ("education", "experience", "research", "teaching"):
        items = (data.get(section) or {}).get(section, [])
        for item in items:
            if item.get("logo"):
                logos.add(item["logo"])
    for h in (data.get("extracurricular") or {}).get("honors", []):
        if h.get("logo"):
            logos.add(h["logo"])
    return logos


# ---------------------------------------------------------------------------
# PDF compilation
# ---------------------------------------------------------------------------

def build_resume_pdf(data):
    """Generate resume.pdf from the LaTeX template and YAML data."""
    if not RESUME_TEMPLATE_PATH.exists():
        print("Warning: resume_template.tex not found, skipping PDF", file=sys.stderr)
        return

    if not shutil.which("pdflatex"):
        print("Warning: pdflatex not found, skipping PDF", file=sys.stderr)
        return

    bio = data["bio"]
    social = bio.get("social") or {}

    template = RESUME_TEMPLATE_PATH.read_text()
    replacements = {
        "{{NAME}}": tex_escape(bio["name"]),
        "{{PHONE}}": "",
        "{{EMAIL}}": tex_escape(social.get("email", "")),
        "{{LINKEDIN}}": tex_escape(social.get("linkedin", "")),
        "{{GITHUB}}": tex_escape(social.get("github", "")),
        "{{SCHOLAR}}": tex_escape(social.get("google_scholar", "")),
        "{{EDUCATION}}": render_education(data),
        "{{EXPERIENCE}}": render_experience(data),
        "{{PUBLICATIONS}}": render_publications(data),
        "{{HONORS}}": render_honors(data),
        "{{SKILLS}}": render_skills(data),
    }

    output = template
    for placeholder, tex in replacements.items():
        output = output.replace(placeholder, tex)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "resume.tex"
        tex_path.write_text(output)

        # Copy logo images into the build directory
        for logo in _collect_logos(data):
            src = BASE_DIR / logo
            if src.exists():
                dst = Path(tmpdir) / logo
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "resume.tex"],
            cwd=tmpdir, capture_output=True, text=True, timeout=30,
        )

        pdf_path = Path(tmpdir) / "resume.pdf"
        if pdf_path.exists():
            shutil.copy2(pdf_path, RESUME_OUTPUT_PATH)
            print(f"Built {RESUME_OUTPUT_PATH}")
        else:
            print("Error: pdflatex failed to produce resume.pdf", file=sys.stderr)
            if result.stdout:
                print(result.stdout[-500:], file=sys.stderr)
            if result.stderr:
                print(result.stderr[-500:], file=sys.stderr)

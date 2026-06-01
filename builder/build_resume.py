"""
LaTeX resume generation using Jake's Resume template.

Reads YAML data and fills resume_template.tex, then compiles to PDF via pdflatex.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .build_config import (
    AUTHOR_NAME,
    AUTHOR_NAME_ALT,
    BASE_DIR,
    RESUME_OUTPUT_PATH,
    RESUME_TEMPLATE_PATH,
)
from .build_utils import format_date, parse_date


def _short_date(value):
    """Resume dates: 3-letter month + year, no day ('Sep 2022')."""
    return format_date(value, short=True, day=False)


_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _tex_with_links(text):
    """Escape a bullet for LaTeX, converting inline markdown links
    [phrase](url) into colored hyperlinks on that phrase. The URL is
    passed through unescaped so hyperref handles it."""
    out, last = [], 0
    for m in _MD_LINK.finditer(text):
        out.append(tex_escape(text[last:m.start()]))
        out.append(f"\\href{{{m.group(2)}}}{{\\textcolor{{linkblue}}{{{tex_escape(m.group(1))}}}}}")
        last = m.end()
    out.append(tex_escape(text[last:]))
    return "".join(out)


# Skill name (lowercased) -> Simple Icons slug for a brand glyph prefix.
# Items not listed (incl. research interests) render as plain text.
_SKILL_ICONS = {
    "python/pytorch": "pytorch",
    "c/c++": "cplusplus",
    "c++": "cplusplus",
    "ros2": "ros",
    "ros": "ros",
    "rust": "rust",
    "github": "github",
    "git": "github",
    "docker": "docker",
}


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


# Canonical display label for known publication-link synonyms. Anything
# not recognised keeps its given name and sorts after the known ones.
_LINK_LABELS = {
    "doi": "DOI",
    "arxiv": "arXiv",
    "paper": "PDF",
    "pdf": "PDF",
    "ecva": "PDF",
    "github": "Code",
    "gitlab": "Code",
    "code": "Code",
    "kaggle": "Data",
    "dataset": "Data",
    "data": "Data",
}
_LINK_ORDER = ["DOI", "arXiv", "PDF", "Code", "Data"]

# Display text for a paper's `status` field (in-progress / unpublished work).
_STATUS_LABELS = {
    "under-review": "Under Review",
    "in-progress": "In Progress",
}


def _status_label(status):
    """Badge text for a paper's status, or '' when unset."""
    if not status:
        return ""
    return _STATUS_LABELS.get(str(status).strip().lower(), str(status).strip())


def _ordered_links(links):
    """Normalize link labels to a canonical vocabulary, drop duplicate
    labels (first URL wins), and sort by a fixed priority so every
    publication shows its links in the same order."""
    seen = {}
    for l in links:
        url = l.get("url")
        if not url:
            continue
        name = (l.get("name") or "").strip()
        label = _LINK_LABELS.get(name.lower(), name)
        if label and label not in seen:
            seen[label] = url

    def sort_key(label):
        rank = _LINK_ORDER.index(label) if label in _LINK_ORDER else len(_LINK_ORDER)
        return (rank, label.lower())

    return [(label, seen[label]) for label in sorted(seen, key=sort_key)]


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
            f"{{{tex_escape(_short_date(edu.get('start_date', '')))} -- {tex_escape(_short_date(edu.get('end_date', '')))}}}"
            f"{{{_tex_with_links(edu.get('institution', ''))}}}"
            f"{{{tex_escape(edu.get('location', ''))}}}"
            f"{{{logo}}}"
        )
        # Thesis (linked) and advisor as compact sub-items.
        sub = []
        thesis = edu.get("thesis") or {}
        if thesis.get("title"):
            t = tex_escape(thesis["title"])
            if thesis.get("link"):
                t = f"\\href{{{thesis['link']}}}{{\\textcolor{{linkblue}}{{{t}}}}}"
            sub.append(f"\\textbf{{Thesis:}} {t}")
        if edu.get("advisor"):
            sub.append(f"\\textbf{{Advisor:}} {_tex_with_links(edu['advisor'])}")
        if sub:
            parts.append("      \\resumeItemListStart")
            for s in sub:
                parts.append(f"        \\resumeItem{{{s}}}")
            parts.append("      \\resumeItemListEnd")
    return "\n".join(parts)


def render_experience(data):
    items = (data.get("experience") or {}).get("experience", [])
    parts = []
    for exp in items:
        logo = _logo_path(exp)
        # Supervisor sits beside the position title in normal (non-bold)
        # small type; names carry inline Scholar links.
        position = tex_escape(exp.get("position", ""))
        if exp.get("advisor"):
            position += f"\\quad\\textmd{{\\footnotesize (Supervisor: {_tex_with_links(exp['advisor'])})}}"
        parts.append(
            f"    \\resumeSubheading"
            f"{{{position}}}"
            f"{{{tex_escape(_short_date(exp.get('start_date', '')))} -- {tex_escape(_short_date(exp.get('end_date', '')))}}}"
            f"{{{_tex_with_links(exp.get('company', ''))}}}"
            f"{{{tex_escape(exp.get('location', ''))}}}"
            f"{{{logo}}}"
        )
        bullets = exp.get("bullets", [])
        description = exp.get("description", "")
        if not bullets and description:
            bullets = [description]
        item_tex = [_tex_with_links(b) for b in bullets]
        if item_tex:
            parts.append("      \\resumeItemListStart")
            for it in item_tex:
                parts.append(f"        \\resumeItem{{{it}}}")
            parts.append("      \\resumeItemListEnd")
    return "\n".join(parts)


def render_publications(data):
    pubs = [p for p in (data.get("publications") or {}).get("papers", []) if p.get("resume")]
    # In-progress / under-review papers float to the top of the list.
    pubs.sort(key=lambda p: 0 if p.get("status") else 1)
    parts = []
    for paper in pubs:
        authors = tex_bold_author(tex_escape(paper.get("authors", "")))
        title = tex_escape(paper.get("title", ""))
        venue = tex_escape(paper.get("venue_short") or paper.get("venue", ""))
        year = tex_escape(_short_date(paper.get("date", "")))
        # Format: Author, A. B. (Year). *Title*. Venue. [Award] [links]
        # The title is italic; the venue is plain text. Links stay inline
        # and are colored; a bare "|" renders as an em-dash in text mode,
        # so the separator is "$|$".
        ref = f"{authors} ({year}). \\emph{{{title}}}."
        status = _status_label(paper.get("status"))
        # Under-review work keeps its venue in the data but doesn't show
        # it yet -- only the status badge. Venue is plain, bold-
        # highlighted only for `selected: true` papers.
        if venue and not status:
            venue_tex = f"\\textbf{{{venue}}}" if paper.get("selected") else venue
            ref += f" {venue_tex}."
        if status:
            ref += f" \\textcolor{{statusamber}}{{[{tex_escape(status)}]}}"
        for a in (paper.get("awards") or []):
            if a.get("name"):
                ref += f" \\textcolor{{awardcolor}}{{\\faAward\\ {tex_escape(a['name'])}}}"
        links = _ordered_links(paper.get("links", []))
        if links:
            link_strs = [
                f"\\href{{{url}}}{{\\textcolor{{linkblue}}{{{tex_escape(label)}}}}}"
                for label, url in links
            ]
            ref += "\\hspace{0.5em}" + "\\,\\textperiodcentered\\,".join(link_strs)
        parts.append(f"    \\resumeItem{{{ref}}}")
    return "\n".join(parts)


def _aggregate_honors(data):
    """Every award attached to a publication / degree / experience /
    research entry, plus the standalone honors listed in
    extracurricular.yaml. Mirrors the HTML Honors section so the CV
    surfaces e.g. a paper's Best Paper award. Sorted newest first."""
    items = []
    for h in (data.get("extracurricular") or {}).get("honors", []):
        if not h.get("title") or h.get("resume") is False:
            continue
        items.append({
            "title": h.get("title", ""),
            "organization": h.get("organization", ""),
            "date": h.get("date"),
            "logo": h.get("logo"),
        })
    # Publication awards are shown as inline badges on the paper itself
    # (see render_publications), so they are intentionally excluded here.
    sources = [
        ("education", "education", "institution", "start_date"),
        ("experience", "experience", "company", "start_date"),
        ("research", "research", "company", "start_date"),
    ]
    for src_key, list_key, sub_field, date_field in sources:
        for entry in (data.get(src_key) or {}).get(list_key, []):
            for a in (entry.get("awards") or []):
                if not a.get("name") or a.get("resume") is False:
                    continue
                items.append({
                    "title": a["name"],
                    "organization": a.get("organization") or entry.get(sub_field, ""),
                    "date": a.get("date") or entry.get(date_field),
                    "logo": a.get("logo") or entry.get("logo"),
                })
    items.sort(key=lambda h: parse_date(h.get("date")), reverse=True)
    return items


def render_honors(data):
    # One line per honor: bold title (organization folded in), date on
    # the right. Keeps the score/award list compact.
    parts = []
    for h in _aggregate_honors(data):
        title = tex_escape(h.get("title", ""))
        org = tex_escape(h.get("organization", ""))
        date = tex_escape(_short_date(h.get("date", "")))
        left = f"\\textbf{{{title}}}"
        if org:
            left += f", {org}"
        parts.append(f"    \\resumeProjectHeading{{{left}}}{{{date}}}")
    return "\n".join(parts)


def render_skills(data):
    skills = (data.get("extracurricular") or {}).get("skills")
    if not skills:
        return ""
    # Grouped form: a mapping of category -> [items] renders one bold-
    # labelled line per category. A flat list (legacy) renders a single
    # "Skills: ..." line.
    def _fmt(item):
        icon = _SKILL_ICONS.get(str(item).strip().lower())
        label = tex_escape(item)
        return f"\\simpleicon{{{icon}}}~{label}" if icon else label

    def _joined(items):
        return ", ".join(_fmt(s) for s in items)

    if isinstance(skills, dict):
        lines = []
        for category, items in skills.items():
            if not items:
                continue
            lines.append(f"\\textbf{{{tex_escape(category)}}}{{: {_joined(items)}}}")
        return " \\\\\n     ".join(lines)
    return f"\\textbf{{Skills}}{{: {_joined(skills)}}}"


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
    # Honors aggregates nested award logos (e.g. a paper's Best Paper
    # award), which the loop above never reaches -- collect them too so
    # the files get copied into the build dir.
    for h in _aggregate_honors(data):
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
        "{{WEBSITE}}": tex_escape(bio.get("site_url", "")),
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

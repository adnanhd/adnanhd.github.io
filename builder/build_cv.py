"""
Long-form curriculum vitae (cv.pdf) from the same YAML data as the resume.

Unlike resume.pdf, nothing is filtered by the `resume` flag: every
publication, research project, teaching assignment and award is listed.
"""

import datetime
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .build_config import BASE_DIR, CV_OUTPUT_PATH, CV_TEMPLATE_PATH
from .build_resume import (
    _logo_path,
    _ordered_links,
    _status_label,
    _tex_with_links,
    is_standalone,
    tex_bold_author,
    tex_escape,
    tex_url,
)
from .build_utils import format_date, parse_date


def _year(value):
    """'2023-02' -> '2023'; 'Present' / 'Spring 2019' pass through."""
    if not value:
        return ""
    s = str(value)
    m = re.match(r"^(\d{4})", s)
    return m.group(1) if m else s


def _year_range(start, end):
    a, b = _year(start), _year(end)
    if a and b and a != b:
        return f"{a}--{b}"
    return a or b


def _month(value):
    return format_date(value, short=True, day=False)


def _month_range(start, end):
    a, b = _month(start), _month(end)
    if a and b:
        return f"{a}--{b}"
    return a or b


def _entry(item, date, body):
    logo = _logo_path(item)
    opt = f"[{logo}]" if logo else ""
    return f"\\cventry{opt}{{{date}}}{{{body}}}"


def _href(url, text):
    return f"\\href{{{tex_url(url)}}}{{\\textcolor{{linkblue}}{{{text}}}}}"


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def render_personal(data):
    bio = data["bio"]
    social = bio.get("social") or {}
    rows = []
    aff = (bio.get("affiliations") or [{}])[0]
    addr = ", ".join(x for x in [aff.get("name"), aff.get("detail"), bio.get("location")] if x)
    if addr:
        rows.append(("Address", tex_escape(addr)))
    if social.get("email"):
        rows.append(("Email", _href(f"mailto:{social['email']}", tex_escape(social["email"]))))
    if bio.get("site_url"):
        site = bio["site_url"]
        rows.append(("Personal Website", _href(site, tex_escape(re.sub(r"^https?://", "", site)))))
    if social.get("google_scholar"):
        url = f"https://scholar.google.com/citations?user={social['google_scholar']}"
        rows.append(("Google Scholar", _href(url, tex_escape(re.sub(r"^https?://", "", url)))))
    if social.get("github"):
        rows.append(("GitHub", _href(f"https://github.com/{social['github']}", tex_escape(f"github.com/{social['github']}"))))
    if social.get("orcid"):
        rows.append(("ORCID", _href(f"https://orcid.org/{social['orcid']}", tex_escape(social["orcid"]))))
    return "\n".join(f"\\cvfield{{{k}}}{{{v}}}" for k, v in rows)


def render_employment(data):
    items = (data.get("experience") or {}).get("experience", [])
    parts = []
    for exp in items:
        body = f"\\textbf{{{tex_escape(exp.get('position', ''))}}}, {_tex_with_links(exp.get('company', ''))}"
        # Supervisor on the left, location pushed to the right margin.
        loc = f"\\hfill\\emph{{{tex_escape(exp['location'])}}}" if exp.get("location") else ""
        if exp.get("advisor"):
            body += f"\\\\ Supervisor: {_tex_with_links(exp['advisor'])}{loc}"
        elif loc:
            body += f"\\\\ {loc}"
        parts.append(_entry(exp, _month_range(exp.get('start_date'), exp.get('end_date')), body))
    return "\n".join(parts)


def render_education(data):
    items = (data.get("education") or {}).get("education", [])
    parts = []
    for edu in items:
        body = f"\\textbf{{{tex_escape(edu.get('degree', ''))}}}, {_tex_with_links(edu.get('institution', ''))}"
        loc = f"\\hfill\\emph{{{tex_escape(edu['location'])}}}" if edu.get("location") else ""
        if edu.get("advisor"):
            body += f"\\\\ Advisor: {_tex_with_links(edu['advisor'])}{loc}"
        elif loc:
            body += f"\\\\ {loc}"
        thesis = edu.get("thesis") or {}
        if thesis.get("title"):
            t = tex_escape(thesis["title"])
            if thesis.get("link"):
                t = _href(thesis["link"], t)
            body += f"\\\\ Thesis: {t}"
        parts.append(_entry(edu, _year_range(edu.get('start_date'), edu.get('end_date')), body))
    return "\n".join(parts)


def render_interests(data):
    bio = data["bio"]
    return tex_escape(bio.get("research_interests") or bio.get("short_bio") or "")


def _all_awards(data):
    """Every award anywhere in the data (publication, degree, experience,
    research, standalone honors). The `resume` flag is ignored: the CV
    is the complete record."""
    items = []
    for h in (data.get("extracurricular") or {}).get("honors", []):
        if h.get("title"):
            items.append({"title": h["title"], "organization": h.get("organization", ""), "date": h.get("date")})
    sources = [
        ("education", "education", "institution", "start_date"),
        ("experience", "experience", "company", "start_date"),
        ("research", "research", "company", "start_date"),
    ]
    for src_key, list_key, sub_field, date_field in sources:
        for entry in (data.get(src_key) or {}).get(list_key, []):
            for a in (entry.get("awards") or []):
                if a.get("name"):
                    items.append({
                        "title": a["name"],
                        "organization": a.get("organization") or entry.get(sub_field, ""),
                        "date": a.get("date") or entry.get(date_field),
                    })
    for p in (data.get("publications") or {}).get("papers", []):
        for a in (p.get("awards") or []):
            if a.get("name"):
                items.append({
                    "title": a["name"],
                    "organization": p.get("venue_short") or p.get("venue", ""),
                    "date": a.get("date") or p.get("date"),
                })
    items.sort(key=lambda h: parse_date(h.get("date")), reverse=True)
    return items


def render_awards(data):
    parts = []
    for h in _all_awards(data):
        date = str(h.get("date") or "")
        date = date.replace("-", "--") if re.match(r"^\d{4}-\d{4}$", date) else _year(date)
        text = tex_escape(h["title"])
        if h.get("organization"):
            text += f" by {tex_escape(h['organization'])}"
        parts.append(f"\\cvaward{{{tex_escape(date)}}}{{{text}}}")
    return "\n".join(parts)


def _pub_group(paper):
    if paper.get("status"):
        return "review"
    venue = str(paper.get("venue") or paper.get("venue_short") or "").lower()
    if "thesis" in venue or "dissertation" in venue:
        return "thesis"
    if not venue or venue.startswith("arxiv"):
        return "preprint"
    return "peer"


_PUB_GROUPS = [
    ("peer", "Peer-reviewed publications"),
    ("preprint", "Preprints"),
    ("review", "Manuscripts under review"),
    ("thesis", "Theses"),
]


def _render_pub_item(paper, number):
    authors = tex_bold_author(tex_escape(paper.get("authors", "")))
    title = tex_escape(paper.get("title_apa") or paper.get("title", ""))
    venue = tex_escape(paper.get("venue", "") or paper.get("venue_short", ""))
    year = tex_escape(_year(paper.get("date", "")))
    # APA: Authors (Year). Title. *Venue*. -- except standalone works
    # (thesis, preprint, manuscript under review): *Title*. Venue.
    standalone = is_standalone(paper)
    title_tex = f"\\emph{{{title}}}" if standalone else title
    ref = f"{authors} ({year}). {title_tex}."
    status = _status_label(paper.get("status"))
    if status:
        ref += f" \\textcolor{{statusamber}}{{{tex_escape(status)}"
        if venue:
            ref += f" at {venue}"
        ref += "}."
    elif venue:
        venue_tex = venue if standalone else f"\\emph{{{venue}}}"
        if paper.get("venue_link"):
            venue_tex = _href(paper["venue_link"], f"\\textbf{{{venue_tex}}}")
        ref += f" {venue_tex}."
    links = _ordered_links(paper.get("links", []))
    if links:
        ref += " (" + ", ".join(_href(url, tex_escape(label)) for label, url in links) + ")"
    item = f"  \\item[{number}.] {ref}"
    awards = [a["name"] for a in (paper.get("awards") or []) if a.get("name")]
    if awards:
        item += "\n  \\begin{cvsublist}\n"
        item += "\n".join(f"    \\item \\textcolor{{awardcolor}}{{\\faAward\\ {tex_escape(a)}}}" for a in awards)
        item += "\n  \\end{cvsublist}"
    return item


def render_publications(data):
    """Publications grouped by kind (peer-reviewed / preprints / under
    review / theses), each group newest first and numbered in reverse
    within itself."""
    pubs = list((data.get("publications") or {}).get("papers", []))
    pubs.sort(key=lambda p: -parse_date(p.get("date")).toordinal())
    parts = []
    for key, heading in _PUB_GROUPS:
        group = [p for p in pubs if _pub_group(p) == key]
        if not group:
            continue
        parts.append(f"\\subsection*{{{heading}}}")
        parts.append("\\begin{cvlist}")
        n = len(group)
        for i, paper in enumerate(group):
            parts.append(_render_pub_item(paper, n - i))
        parts.append("\\end{cvlist}")
    return "\n".join(parts)


def render_research(data):
    items = list((data.get("research") or {}).get("research", []))
    items.sort(key=lambda r: parse_date(r.get("start_date")), reverse=True)
    parts = []
    for r in items:
        body = f"\\textbf{{{_tex_with_links(r.get('company', ''))}}}"
        body += f"\\\\ \\emph{{{tex_escape(r.get('position', ''))}}}"
        if r.get("description"):
            body += f"\\\\ {_tex_with_links(r['description'])}"
        # Advisor on the left, location pushed to the right margin.
        loc = f"\\hfill\\emph{{{tex_escape(r['location'])}}}" if r.get("location") else ""
        if r.get("advisor"):
            body += f"\\\\ Advisor: {_tex_with_links(r['advisor'])}{loc}"
        elif loc:
            body += f"\\\\ {loc}"
        parts.append(_entry(r, _month_range(r.get('start_date'), r.get('end_date')), body))
    return "\n".join(parts)


def render_teaching(data):
    """One subsection per appointment (role + department), courses
    listed beneath it -- mirrors the grouped publication list instead of
    repeating the role under every course."""
    parts = []
    for t in (data.get("teaching") or {}).get("teaching", []):
        head = f"{tex_escape(t.get('position', ''))}, {_tex_with_links(t.get('company', ''))}"
        dates = _month_range(t.get("start_date"), t.get("end_date"))
        if dates:
            head += f" \\hfill {{\\normalfont\\small {tex_escape(dates)}}}"
        parts.append(f"\\subsection*{{{head}}}")
        courses = t.get("bullets") or []
        if courses:
            parts.append("\\begin{cvlist}")
            n = len(courses)
            for i, course in enumerate(courses):
                parts.append(f"  \\item[{n - i}.] {tex_escape(course)}")
            parts.append("\\end{cvlist}")
    return "\n".join(parts)


def render_skills(data):
    skills = (data.get("extracurricular") or {}).get("skills") or {}
    if isinstance(skills, dict):
        return "\n".join(
            f"\\cvfield{{{tex_escape(cat)}}}{{{tex_escape(', '.join(items))}}}"
            for cat, items in skills.items() if items
        )
    return tex_escape(", ".join(skills))


def render_languages(data):
    langs = (data.get("extracurricular") or {}).get("languages") or []
    return "\n".join(
        f"\\cvfield{{{tex_escape(l.get('name', ''))}}}{{{tex_escape(l.get('level', ''))}}}"
        for l in langs if l.get("name")
    )


# ---------------------------------------------------------------------------
# Logo preparation
# ---------------------------------------------------------------------------

def _prepare_logo(logo, tmpdir):
    """Copy a logo into the build dir, normalised so every entry's logo
    sits in the same visual box: a sibling .svg is rasterised at high
    resolution (crisp), and surrounding whitespace / transparent padding
    is trimmed so logos with built-in margins don't look smaller than
    the rest. Falls back to a plain copy when the tools are missing."""
    src = BASE_DIR / logo
    dst = tmpdir / logo
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    svg = src.with_suffix(".svg")
    if svg.exists() and shutil.which("rsvg-convert"):
        raster = dst.with_suffix(".png")
        subprocess.run(["rsvg-convert", "-h", "600", "-o", str(raster), str(svg)],
                       check=False, capture_output=True)
        src = raster if raster.exists() else src
        dst = dst.with_suffix(".png")
    if shutil.which("magick"):
        r = subprocess.run(
            ["magick", str(src), "-trim", "+repage", "-background", "none",
             "-bordercolor", "none", "-border", "2%", str(dst)],
            check=False, capture_output=True)
        if r.returncode == 0 and dst.exists():
            return
    shutil.copy2(src, dst)


# ---------------------------------------------------------------------------
# PDF compilation
# ---------------------------------------------------------------------------

def build_cv_pdf(data):
    """Generate cv.pdf from cv_template.tex and the YAML data."""
    if not CV_TEMPLATE_PATH.exists():
        print("Warning: cv_template.tex not found, skipping CV", file=sys.stderr)
        return
    if not shutil.which("pdflatex"):
        print("Warning: pdflatex not found, skipping CV", file=sys.stderr)
        return

    replacements = {
        "{{NAME}}": tex_escape(data["bio"]["name"]),
        "{{PERSONAL}}": render_personal(data),
        "{{EMPLOYMENT}}": render_employment(data),
        "{{EDUCATION}}": render_education(data),
        "{{INTERESTS}}": render_interests(data),
        "{{AWARDS}}": render_awards(data),
        "{{PUBLICATIONS}}": render_publications(data),
        "{{RESEARCH}}": render_research(data),
        "{{TEACHING}}": render_teaching(data),
        "{{SKILLS}}": render_skills(data),
        "{{LANGUAGES}}": render_languages(data),
        "{{UPDATED}}": datetime.date.today().strftime("%B %Y"),
    }
    output = CV_TEMPLATE_PATH.read_text()
    for placeholder, tex in replacements.items():
        if not tex.strip() and placeholder not in ("{{NAME}}", "{{UPDATED}}"):
            # Empty section: drop its heading (and any wrapping list) too.
            output = re.sub(
                r"\\section\*\{[^}]*\}\n(?:\\begin\{cvlist\}\n)?" + re.escape(placeholder)
                + r"\n(?:\\end\{cvlist\}\n)?", "", output)
        output = output.replace(placeholder, tex)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "cv.tex"
        tex_path.write_text(output)
        for section in ("education", "experience", "research"):
            for item in (data.get(section) or {}).get(section, []):
                logo = _logo_path(item)
                if logo:
                    _prepare_logo(logo, Path(tmpdir))
        result = None
        for _ in range(2):  # second pass settles page numbers
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "cv.tex"],
                cwd=tmpdir, capture_output=True, text=True, timeout=60,
            )
        pdf_path = Path(tmpdir) / "cv.pdf"
        if pdf_path.exists():
            shutil.copy2(pdf_path, CV_OUTPUT_PATH)
            print(f"Built {CV_OUTPUT_PATH}")
        else:
            print("Error: pdflatex failed to produce cv.pdf", file=sys.stderr)
            if result and result.stdout:
                print(result.stdout[-800:], file=sys.stderr)

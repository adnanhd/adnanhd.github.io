"""
HTML rendering functions for the static site.

Each function takes data (dicts loaded from YAML) and returns an HTML string.
"""

import json
import re

from .build_config import (
    LINK_ICONS,
    LINK_NAMES,
    PRIMARY_LINKS,
    SECONDARY_CATEGORIES,
    URL_TEMPLATES,
)
from .build_utils import esc, format_date, highlight_author, highlight_author_span, parse_date, slugify


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _render_social_link(platform, uid):
    """Render a single social link element."""
    url = URL_TEMPLATES[platform].format(id=esc(uid))
    icon = LINK_ICONS.get(platform, "")
    label = LINK_NAMES.get(platform, platform)
    target = "" if platform == "email" else ' target="_blank" rel="noopener noreferrer"'
    return (
        f'<a href="{url}" class="social-link" title="{esc(label)}" '
        f'aria-label="{esc(label)}"{target}>'
        f'<i class="{icon}"></i>'
        f'<span class="social-label">{esc(label)}</span></a>'
    )


def render_sidebar(bio):
    """Render the left sidebar: profile image, name, title, links."""
    parts = []

    # Profile image
    parts.append(
        f'<div class="bio-image">'
        f'  <img src="{esc(bio["profile_image"])}" alt="{esc(bio["name"])}" '
        f'width="180" height="180" />'
        f'</div>'
    )

    # Identity
    parts.append(f'<h1 class="sidebar-name">{esc(bio["name"])}</h1>')
    parts.append(f'<p class="sidebar-title">{esc(bio.get("title", ""))}</p>')
    parts.append(f'<p class="sidebar-affiliation">{esc(bio.get("affiliation", ""))}</p>')

    if bio.get("short_bio"):
        parts.append(f'<p class="bio-short">{esc(bio["short_bio"])}</p>')

    # Links container
    parts.append('<div class="links">')
    social = bio.get("social") or {}

    # Primary links (always visible)
    for platform in PRIMARY_LINKS:
        uid = social.get(platform)
        if uid and str(uid).strip() and platform in URL_TEMPLATES:
            parts.append(_render_social_link(platform, uid))

    # Custom links (Resume PDF, etc.)
    for link in bio.get("custom_links") or []:
        target = ' target="_blank" rel="noopener noreferrer"' if link["url"].startswith("http") else ""
        parts.append(f'<a href="{esc(link["url"])}"{target}>{esc(link["name"])}</a>')

    # Collapsible secondary categories
    for category, platforms in SECONDARY_CATEGORIES.items():
        links = [
            _render_social_link(p, social[p])
            for p in platforms
            if social.get(p) and str(social[p]).strip() and p in URL_TEMPLATES
        ]
        if links:
            parts.append(
                f'<div class="links-category">'
                f'<button class="links-category-toggle" aria-expanded="false">'
                f'<span class="category-label">{esc(category)}</span>'
                f'<i class="fas fa-chevron-down category-chevron"></i></button>'
                f'<div class="links-category-items">'
            )
            parts.extend(links)
            parts.append("</div></div>")

    parts.append("</div>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Bio
# ---------------------------------------------------------------------------

def render_bio(bio):
    """Render About Me paragraphs. Bio text is trusted HTML (author-controlled)."""
    paragraphs = bio.get("bio", "").split("\n\n")
    return "\n".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())


# ---------------------------------------------------------------------------
# Publications
# ---------------------------------------------------------------------------

# venue token -> brand colour for the publication-venue-tag pill.
# Key is the first non-prefix token of `venue_short` uppercased
# (e.g. "IEEE/TVCG 2025" -> "TVCG", "Book Chapter 2024" -> "BOOK").
_VENUE_COLORS = {
    "ICRA":     "#00629b",   # IEEE robotics blue
    "TVCG":     "#7b3f8f",   # graphics purple
    "ECCV":     "#017a8e",   # ECCV teal
    "CVPR":     "#1b4f72",   # CVPR navy
    "ICCV":     "#7b1d36",   # ICCV maroon
    "NEURIPS":  "#6c71c4",
    "NIPS":     "#6c71c4",
    "ICML":     "#d36d2e",
    "ICLR":     "#cf2e2e",
    "AAAI":     "#0e4d92",
    "AINA":     "#5b7eb0",
    "BOOK":     "#8b5e34",
    "ITU":      "#7a1a35",
    "SRMC":     "#1e7a3d",
    "CINC":     "#c0392b",   # cardiology red
    "DAWAK":    "#6c71c4",
    "SIGGRAPH": "#cf2e7a",
    "ACL":      "#2e7d32",
    "EMNLP":    "#00695c",
    "ICASSP":   "#0a64a4",
}


def _venue_color(venue_short):
    """Pick a brand colour from `venue_short`; None falls back to --accent-color."""
    if not venue_short:
        return None
    s = re.sub(r"^(IEEE|ACM)/", "", str(venue_short).strip().upper())
    token = s.split()[0] if s else ""
    return _VENUE_COLORS.get(token)


def _render_pub_links(links):
    """Render publication link buttons (PAPER, CODE, DEMO, etc.)."""
    if not links:
        return ""
    items = "\n".join(
        f'<a href="{esc(l["url"])}" class="pub-link" target="_blank" '
        f'rel="noopener noreferrer">{esc(l["name"])}</a>'
        for l in links
    )
    return f'<div class="publication-links">\n{items}\n</div>'


def render_publication_card(paper):
    """Render a fancy publication card (About page - selected works)."""
    parts = ['<div class="publication-item">']

    # Left: venue tag + image
    parts.append('<div class="publication-left">')
    venue_text = paper.get("venue_short") or paper.get("venue", "Publication")
    color = _venue_color(venue_text)
    style = f' style="background-color: {color}"' if color else ""
    if paper.get("venue_link"):
        parts.append(
            f'<div class="publication-venue-tag"{style}>'
            f'<a href="{esc(paper["venue_link"])}" target="_blank" rel="noopener noreferrer">'
            f'{esc(venue_text)}</a></div>'
        )
    else:
        parts.append(f'<div class="publication-venue-tag"{style}>{esc(venue_text)}</div>')

    if paper.get("image"):
        parts.append(
            f'<div class="publication-image">'
            f'<img src="{esc(paper["image"])}" alt="{esc(paper["title"])}" loading="lazy" /></div>'
        )
    parts.append("</div>")

    # Right: title, authors, venue, links
    parts.append('<div class="publication-content">')
    slug = slugify(paper["title"])
    parts.append(
        f'<div class="publication-title">'
        f'<a href="projects/{slug}/index.html" class="project-link">{esc(paper["title"])}</a></div>'
    )
    parts.append(f'<div class="publication-authors">{highlight_author_span(esc(paper.get("authors", "")))}</div>')

    venue_full = paper.get("venue", "")
    if paper.get("date"):
        venue_full += f', {format_date(paper["date"])}'
    parts.append(f'<div class="publication-venue">{esc(venue_full)}</div>')
    parts.append(_render_pub_links(paper.get("links")))
    parts.append("</div></div>")
    return "\n".join(parts)


def render_compact_publication(paper):
    """Render a compact APA-style citation (CV page)."""
    parts = ['<div class="publication-item-compact">']

    authors_html = highlight_author(esc(paper.get("authors", "")))
    citation = authors_html
    if paper.get("date"):
        citation += f" ({esc(format_date(paper['date']))})."
    citation += f" {esc(paper['title'])}."
    if paper.get("venue_link") and paper.get("venue_short"):
        citation += (
            f' <em><a href="{esc(paper["venue_link"])}" target="_blank" rel="noopener noreferrer" '
            f'style="color: var(--accent-color); text-decoration: none;">'
            f'{esc(paper["venue_short"])}</a></em>.'
        )
    elif paper.get("venue"):
        citation += f" <em>{esc(paper['venue'])}</em>."

    parts.append(f'<div class="pub-compact-reference">{citation}</div>')

    if paper.get("links"):
        parts.append('<div class="publication-links">')
        for link in paper["links"]:
            parts.append(
                f'<a href="{esc(link["url"])}" class="pub-link" target="_blank" '
                f'rel="noopener noreferrer">{esc(link["name"])}</a>'
            )
        parts.append("</div>")

    parts.append("</div>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Resume sections (Education, Experience, Research, Teaching, Honors)
# ---------------------------------------------------------------------------

def _render_resume_item(title, subtitle, date, description="", logo=None,
                        links=None, logo_link=None, commitment=None,
                        advisor=None, bullets=None):
    """Render a single resume entry with logo, header, bullets, and links."""
    parts = ['<div class="resume-item">']

    if logo:
        parts.append('<div class="resume-logo">')
        img = f'<img src="{esc(logo)}" alt="{esc(subtitle)}" loading="lazy" width="40" height="40" />'
        if logo_link:
            parts.append(f'<a href="{esc(logo_link)}" target="_blank" rel="noopener noreferrer">{img}</a>')
        else:
            parts.append(img)
        parts.append("</div>")

    parts.append('<div class="resume-details">')
    parts.append(f'<div class="resume-header"><strong>{esc(title)}</strong>'
                 f'<span class="date">{esc(date)}</span></div>')

    parts.append(f'<div class="resume-subheader"><span>{esc(subtitle)}</span>')
    if commitment and str(commitment).strip():
        parts.append(f'<span class="resume-commitment">{esc(commitment)}</span>')
    parts.append("</div>")

    if advisor and str(advisor).strip():
        parts.append(f'<div class="resume-advisor"><strong>Advisor:</strong> {esc(advisor)}</div>')

    if description:
        parts.append(f"<p>{esc(description)}</p>")

    if bullets:
        parts.append('<ul class="resume-bullets">')
        for bullet in bullets:
            course = re.match(r"^(CENG \d+)\s*-\s*(.+)$", bullet)
            if course:
                code, name = course.group(1), course.group(2)
                num = code.replace("CENG ", "")
                url = f"https://catalog.metu.edu.tr/course.php?course_code=5710{num}"
                parts.append(
                    f'<li><a href="{url}" target="_blank" rel="noopener noreferrer" '
                    f'style="color: var(--accent-color); text-decoration: none;">'
                    f'{esc(code)}</a> - {esc(name)}</li>'
                )
            else:
                parts.append(f"<li>{esc(bullet)}</li>")
        parts.append("</ul>")

    parts.append(_render_pub_links(links))
    parts.append("</div></div>")
    return "\n".join(parts)


def _render_section(items, title_key, subtitle_key, date_fn):
    """Render a list of resume items."""
    return "\n".join(
        _render_resume_item(
            title=item.get(title_key, ""),
            subtitle=item.get(subtitle_key, ""),
            date=date_fn(item),
            description=item.get("description", ""),
            logo=item.get("logo"),
            links=item.get("links"),
            logo_link=item.get("logo_link"),
            commitment=item.get("commitment"),
            advisor=item.get("advisor"),
            bullets=item.get("bullets"),
        )
        for item in items
    )


def _date_range(item):
    start = format_date(item.get("start_date", ""))
    end = format_date(item.get("end_date", ""))
    if start and end:
        return f"{start} - {end}"
    return start or end


def render_education(data):
    items = (data.get("education") or {}).get("education", [])
    return _render_section(items, "degree", "institution", _date_range)


def render_experience(data):
    items = (data.get("experience") or {}).get("experience", [])
    return _render_section(items, "position", "company", _date_range)


def render_research(data):
    items = (data.get("research") or {}).get("research", [])
    return _render_section(items, "position", "company", _date_range)


def render_teaching(data):
    items = (data.get("teaching") or {}).get("teaching", [])
    return _render_section(items, "position", "company", _date_range)


def render_honors(data):
    items = (data.get("extracurricular") or {}).get("honors", [])
    return _render_section(items, "title", "organization", lambda e: format_date(e.get("date", "")))


# ---------------------------------------------------------------------------
# News - manually curated one-liners, each clickable through to Timeline
# ---------------------------------------------------------------------------

_NEWS_TAG_COLORS = {
    "publication": "#10b981",   # green
    "degree":      "#6c71c4",   # purple
    "internship":  "#2aa198",   # teal
    "award":       "#b58900",   # gold
    "life-event":  "#8b5cf6",   # purple
}


def _normalize_tags(raw):
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return list(raw)


def render_news(data):
    """One-line news entries with optional [link] and tag chips. The whole
    row hyperlinks to the matching Timeline anchor (timeline_ref slug)."""
    items = (data.get("news") or {}).get("items", [])
    if not items:
        return ""

    parts = []
    for item in items:
        tags = _normalize_tags(item.get("tags"))
        date_html = f'<span class="news-date">{esc(format_date(item["date"]))}</span>'

        body = esc(item["content"])
        if item.get("link"):
            body += (
                f' <a href="{esc(item["link"])}" class="news-link" '
                f'target="_blank" rel="noopener noreferrer">[link]</a>'
            )
        content_html = f'<span class="news-content">{body}</span>'

        chips = "".join(
            f'<span class="news-tag" style="background-color: '
            f'{_NEWS_TAG_COLORS.get(t, "var(--text-muted)")}">{esc(t)}</span>'
            for t in tags
        )
        tag_html = f'<span class="news-tags">{chips}</span>' if chips else ""

        ref = item.get("timeline_ref")
        if ref:
            inner = (
                f'<a class="news-row" href="#timeline:tl-{esc(ref)}">'
                f'{date_html}{content_html}{tag_html}</a>'
            )
        else:
            inner = f'<span class="news-row">{date_html}{content_html}{tag_html}</span>'

        parts.append(f'<li>{inner}</li>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Timeline - two-sided chronology, no nav entry (reached via News clicks)
# ---------------------------------------------------------------------------

# Type -> (side, dot/border colour). Paper-related events (publications +
# paper awards) go on the LEFT; institutional events (degree, experience,
# research positions) go on the RIGHT. The right side is intentionally
# given more width since those titles + org names run long.
_TIMELINE_TYPE_META = {
    "publication": ("left",  "#10b981"),
    "award":       ("left",  "#b58900"),
    "degree":      ("right", "#6c71c4"),
    "experience":  ("right", "#2aa198"),
    "research":    ("right", "#2aa198"),
}


def _timeline_exp_event(item, ev_type):
    """Build a timeline event from an education/experience/research record."""
    return {
        "date": item.get("start_date"), "end_date": item.get("end_date"),
        "type": ev_type,
        "title": item.get("degree") or item.get("position", ""),
        "subtitle": item.get("institution") or item.get("company", ""),
        "logo": item.get("logo"),
        "link": item.get("link"),
    }


def _event_year(e):
    """Extract the 4-digit year from an event's date string."""
    m = re.search(r"\d{4}", str(e.get("date") or ""))
    return int(m.group()) if m else 0


def _render_timeline_card(e):
    """Render a single timeline card (used inside a year row)."""
    side, color = _TIMELINE_TYPE_META.get(e["type"], ("right", "var(--accent-color)"))
    anchor = f"tl-{slugify(e['title'])}"

    date = esc(format_date(e["date"]))
    if e.get("end_date"):
        date += f' <span class="timeline-dash">-</span> {esc(format_date(e["end_date"]))}'

    logo = e.get("logo")
    logo_html = (
        f'<img class="timeline-logo" src="{esc(logo)}" alt="" loading="lazy" '
        f'width="22" height="22" />' if logo else ""
    )

    body = [
        f'<span class="timeline-date">{date}</span>',
        f'<h4 class="timeline-title">{logo_html}<span>{esc(e["title"])}</span></h4>',
    ]

    if e["type"] == "publication":
        body.append(
            f'<div class="timeline-authors">'
            f'{highlight_author(esc(e.get("authors", "")))}</div>'
        )
        if e.get("subtitle"):
            body.append(f'<div class="timeline-venue"><em>{esc(e["subtitle"])}</em></div>')
        links = [l for l in (e.get("links") or []) if l.get("url")]
        if links:
            link_html = "".join(
                f'<a href="{esc(l["url"])}" target="_blank" rel="noopener noreferrer" '
                f'class="timeline-link">{esc(l["name"])}</a>'
                for l in links
            )
            body.append(f'<div class="timeline-links">{link_html}</div>')
    else:
        if e.get("subtitle"):
            body.append(f'<div class="timeline-org">{esc(e["subtitle"])}</div>')
        if e.get("link"):
            body.append(
                f'<div class="timeline-links">'
                f'<a href="{esc(e["link"])}" target="_blank" '
                f'rel="noopener noreferrer" class="timeline-link">Link</a></div>'
            )

    return (
        f'<div id="{anchor}" class="timeline-item timeline-{e["type"]} timeline-{side}" '
        f'style="--dot-color: {color}">{"".join(body)}</div>'
    )


def render_timeline(data):
    """Cartesian timeline: years stack newest-first, each year is a labelled
    band on the central rail; publications go on the left, institutional /
    award entries on the right. Empty years keep their slot to preserve the
    chronological scale."""
    events = []

    for edu in (data.get("education") or {}).get("education", []):
        if edu.get("timelined"):
            events.append(_timeline_exp_event(edu, "degree"))
    for exp in (data.get("experience") or {}).get("experience", []):
        if exp.get("timelined"):
            events.append(_timeline_exp_event(exp, "experience"))
    for res in (data.get("research") or {}).get("research", []):
        if res.get("timelined"):
            events.append(_timeline_exp_event(res, "research"))

    # Publications are inherently chronological - include all of them.
    for paper in (data.get("publications") or {}).get("papers", []):
        events.append({
            "date": paper.get("date"), "type": "publication",
            "title": paper.get("title", ""),
            "authors": paper.get("authors", ""),
            "subtitle": paper.get("venue_short") or paper.get("venue", ""),
            "links": paper.get("links"),
        })

    for h in (data.get("extracurricular") or {}).get("honors", []):
        if not h.get("timelined"):
            continue
        events.append({
            "date": h.get("date"), "type": "award",
            "title": h.get("title", ""),
            "subtitle": h.get("organization", ""),
            "logo": h.get("logo"),
            "link": h.get("link"),
        })

    events = [e for e in events if e.get("date")]
    events.sort(key=lambda e: parse_date(e["date"]), reverse=True)
    if not events:
        return ""

    by_year = {}
    for e in events:
        by_year.setdefault(_event_year(e), []).append(e)

    years = [y for y in by_year.keys() if y]
    if not years:
        return ""
    max_year, min_year = max(years), min(years)

    parts = ['<div class="timeline">']
    for y in range(max_year, min_year - 1, -1):
        ev = by_year.get(y, [])
        left  = [e for e in ev if _TIMELINE_TYPE_META.get(e["type"], ("right",))[0] == "left"]
        right = [e for e in ev if _TIMELINE_TYPE_META.get(e["type"], ("right",))[0] == "right"]
        empty_cls = " timeline-year-empty" if not ev else ""

        parts.append(f'<div class="timeline-year{empty_cls}" data-year="{y}">')
        parts.append(f'<span class="timeline-year-label">{y}</span>')
        parts.append('<div class="timeline-year-row">')

        parts.append('<div class="timeline-year-side timeline-year-leftside">')
        parts.extend(_render_timeline_card(e) for e in left)
        parts.append('</div>')

        parts.append('<div class="timeline-year-side timeline-year-rightside">')
        parts.extend(_render_timeline_card(e) for e in right)
        parts.append('</div>')

        parts.append('</div></div>')
    parts.append('</div>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Blogs and Works
# ---------------------------------------------------------------------------

_TAG_ACRONYMS = {"rl": "RL", "ml": "ML", "ai": "AI", "cv": "CV", "nlp": "NLP", "llm": "LLM"}


def _pretty_tag(tag):
    """Human-readable label for a slug tag: 'model-based-rl' -> 'Model Based RL'."""
    return " ".join(_TAG_ACRONYMS.get(w, w.title()) for w in str(tag).split("-"))


def _tag_parent_map(tag_tree):
    """Invert a parent->children tree into child->{parents} for ancestor lookup."""
    parents = {}
    for parent, children in (tag_tree or {}).items():
        for child in children or []:
            parents.setdefault(child, set()).add(parent)
    return parents


def _effective_tags(tags, parent_map):
    """Expand tags with all inherited (ancestor) tags from the tag tree."""
    result, stack = set(), list(tags or [])
    while stack:
        tag = stack.pop()
        if tag in result:
            continue
        result.add(tag)
        stack.extend(parent_map.get(tag, ()))
    return result


def render_blog_controls(blogs_data):
    """Render the blog search box + tag filter chips (tag-inheritance aware)."""
    bd = blogs_data or {}
    blogs = bd.get("blogs", [])
    if not blogs:
        return ""
    parent_map = _tag_parent_map(bd.get("tag_tree"))
    all_tags = set()
    for blog in blogs:
        all_tags |= _effective_tags(blog.get("tags") or [], parent_map)

    chips = ['<button class="blog-filter active" data-tag="">All</button>']
    for tag in sorted(all_tags):
        chips.append(
            f'<button class="blog-filter" data-tag="{esc(tag)}">{esc(_pretty_tag(tag))}</button>'
        )
    filters = f'<div class="blog-filters">{"".join(chips)}</div>' if all_tags else ""
    return (
        '<div class="blog-controls">'
        '<input type="search" id="blog-search" class="blog-search" '
        'placeholder="Search posts..." aria-label="Search blog posts" />'
        f'{filters}'
        '</div>'
    )


def render_blogs(blogs_data, selected_only=False):
    """Render blog post listings with inherited tags + search/filter metadata."""
    bd = blogs_data or {}
    blogs = bd.get("blogs", [])
    parent_map = _tag_parent_map(bd.get("tag_tree"))
    if selected_only:
        blogs = [b for b in blogs if b.get("selected")]

    if not blogs:
        msg = "No selected blogs yet." if selected_only else "No blog posts yet. Check back soon!"
        return f'<p style="color: var(--text-secondary);">{msg}</p>'

    parts = []
    for blog in blogs:
        own_tags = sorted(blog.get("tags") or [])
        eff_tags = sorted(_effective_tags(own_tags, parent_map))
        data_tags = " ".join(eff_tags)
        search = " ".join([blog.get("title", ""), blog.get("description", "")] + eff_tags).lower()

        chips = "".join(
            f'<span class="blog-tag" data-tag="{esc(t)}">{esc(_pretty_tag(t))}</span>'
            for t in own_tags
        )
        chips_html = f'<div class="blog-tags">{chips}</div>' if chips else ""
        desc = f"<p>{esc(blog['description'])}</p>" if blog.get("description") else ""
        parts.append(
            f'<div class="blog-item" data-tags="{esc(data_tags)}" data-search="{esc(search)}">'
            f'<a href="{esc(blog["path"])}" class="blog-link">'
            f'<h3>{esc(blog["title"])}</h3>'
            f'<span class="blog-date">{esc(format_date(blog.get("date", "")))}</span>'
            f'{desc}</a>{chips_html}</div>'
        )
    return "\n".join(parts)


# tech tag -> (brand colour, Devicon class). Tags not listed render as plain chips.
_TECH_BADGES = {
    "python": ("#3776AB", "devicon-python-plain"),
    "pytorch": ("#EE4C2C", "devicon-pytorch-original"),
    "tensorflow": ("#FF6F00", "devicon-tensorflow-original"),
    "jax": ("#5E97F6", "devicon-python-plain"),
    "c++": ("#00599C", "devicon-cplusplus-plain"),
    "cuda": ("#76B900", "devicon-nvidia-plain"),
    "docker": ("#2496ED", "devicon-docker-plain"),
    "apptainer": ("#0F4C81", "fas fa-cubes"),   # no Devicon glyph -> Font Awesome
    "singularity": ("#0F4C81", "fas fa-cubes"),
    "numpy": ("#013243", "devicon-numpy-original"),
}


def render_tags(tags):
    """Render tags: brand-coloured Devicon badges for known tech, chips otherwise."""
    if not tags:
        return ""
    out = []
    for tag in tags:
        badge = _TECH_BADGES.get(str(tag).lower())
        if badge:
            color, icon = badge
            out.append(
                f'<span class="tech-badge" style="background:{color}">'
                f'<i class="{icon}" aria-hidden="true"></i>{esc(tag)}</span>'
            )
        else:
            out.append(f'<span class="work-tag">{esc(tag)}</span>')
    return f'<div class="work-tags">{"".join(out)}</div>'


def _repo_path(url):
    """Return 'owner/repo' from a GitHub URL, else ''."""
    m = re.match(r"https?://github\.com/([^/]+/[^/?#]+)", url or "")
    return m.group(1) if m else ""


def render_works(works_data):
    """Render open source projects as GitHub cards."""
    works = (works_data or {}).get("works", [])
    if not works:
        return '<p style="color: var(--text-secondary);">No selected works yet.</p>'

    parts = []
    for work in works:
        repo = _repo_path(work.get("url", ""))
        repo_html = f'<span class="work-repo">{esc(repo)}</span>' if repo else ""
        desc = f"<p>{esc(work['description'])}</p>" if work.get("description") else ""
        tags = render_tags(work.get("tags"))

        slug = slugify(work["title"])
        links = _render_pub_links([{"name": "GitHub", "url": work["url"]}]) if work.get("url") else ""
        parts.append(
            f'<div class="work-item">'
            f'<div class="work-head">'
            f'<i class="fab fa-github work-icon" aria-hidden="true"></i>'
            f'<span class="work-titles">'
            f'<a href="projects/{slug}/index.html" class="work-name">{esc(work["title"])}</a>'
            f'{repo_html}</span></div>'
            f'{desc}{tags}{links}</div>'
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# SEO: JSON-LD and Sitemap
# ---------------------------------------------------------------------------

def render_json_ld(bio):
    """Render JSON-LD structured data for the Person schema."""
    same_as = [
        URL_TEMPLATES[p].format(id=str(uid))
        for p, uid in (bio.get("social") or {}).items()
        if uid and str(uid).strip() and p in URL_TEMPLATES and p != "email"
    ]
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": bio["name"],
        "description": bio.get("meta_description", ""),
        "url": bio.get("site_url", "") + "/",
        "image": bio.get("site_url", "") + "/" + bio.get("profile_image", ""),
        "jobTitle": bio.get("title", ""),
        "worksFor": {"@type": "Organization", "name": bio.get("affiliation", "")},
        "sameAs": same_as,
    }
    return json.dumps(person, indent=2, ensure_ascii=False)


def generate_sitemap(bio, blogs_data):
    """Generate sitemap.xml content."""
    from datetime import datetime
    site_url = bio.get("site_url", "https://adnanhd.github.io")
    today = datetime.now().strftime("%Y-%m-%d")

    urls = [
        (f"{site_url}/", today, "1.0"),
        (f"{site_url}/#cv", today, "0.9"),
        (f"{site_url}/#blogs", today, "0.8"),
    ]
    for blog in (blogs_data or {}).get("blogs", []):
        if blog.get("path"):
            urls.append((f"{site_url}/{blog['path']}", today, "0.6"))

    entries = "\n".join(
        f"  <url>\n    <loc>{esc(loc)}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n    <priority>{prio}</priority>\n  </url>"
        for loc, lastmod, prio in urls
    )
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>'

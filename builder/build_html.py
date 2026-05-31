"""
HTML rendering functions for the static site.

Each function takes data (dicts loaded from YAML) and returns an HTML string.
"""

import json
import re
import sys

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


def _render_awards(awards):
    """Render an attached-awards line. Subtle: small trophy glyph +
    plain text name, optionally a thin organization tail. One line per
    award. Returns "" when there are no awards so callers can drop it
    in unconditionally."""
    awards = [a for a in (awards or []) if a and a.get("name")]
    if not awards:
        return ""
    rows = []
    for a in awards:
        name = esc(a["name"])
        org = a.get("organization")
        link = a.get("link")
        org_html = f' <span class="award-org">- {esc(org)}</span>' if org else ""
        body = (
            f'<i class="fa-solid fa-award" aria-hidden="true"></i> '
            f'<span class="award-name">{name}</span>{org_html}'
        )
        if link:
            body = (
                f'<a href="{esc(link)}" target="_blank" rel="noopener noreferrer">'
                f'{body}</a>'
            )
        rows.append(f'<div class="entry-award">{body}</div>')
    return f'<div class="entry-awards">{"".join(rows)}</div>'


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
    parts.append(_render_awards(paper.get("awards")))
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

    parts.append('<div class="pub-compact-body">')
    parts.append(f'<div class="pub-compact-reference">{citation}</div>')
    parts.append(_render_awards(paper.get("awards")))
    parts.append('</div>')

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
                        advisor=None, bullets=None, awards=None):
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

    parts.append(_render_awards(awards))
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
            awards=item.get("awards"),
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
    """Honors aggregates every award attached to a publication / degree /
    research / experience entry, plus standalone honors listed in
    extracurricular.yaml (scholarships, fellowships with no single
    parent). Sorted newest first."""
    items = list((data.get("extracurricular") or {}).get("honors", []))
    sources = [
        ("publications", "papers", "title", "venue_short", "date"),
        ("education",    "education", "degree", "institution", "start_date"),
        ("experience",   "experience", "position", "company", "start_date"),
        ("research",     "research", "position", "company", "start_date"),
    ]
    for src_key, list_key, title_field, sub_field, date_field in sources:
        for entry in (data.get(src_key) or {}).get(list_key, []):
            for a in (entry.get("awards") or []):
                if not a.get("name"):
                    continue
                parent_title = entry.get(title_field, "")
                # The award's own description is canonical for the Honors
                # section. Fall back to "For <parent>" so an award without
                # a description still has SOME body text identifying its
                # source.
                desc = a.get("description")
                if not desc and parent_title:
                    desc = f'For "{parent_title}".'
                items.append({
                    "title": a["name"],
                    "organization": a.get("organization") or entry.get(sub_field, ""),
                    "date": a.get("date") or entry.get(date_field),
                    "link": a.get("link"),
                    "logo": a.get("logo") or entry.get("logo"),
                    "description": desc or "",
                })
    items.sort(key=lambda h: parse_date(h.get("date")), reverse=True)
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


_NEWS_MAX_ITEMS = 15  # cap on About; rest live on Timeline ("see all news ->")


def render_news(data):
    """One-line news entries with optional [link] and tag chips.
    Row is a <div data-href=...> (not <a>) because the content already
    contains an external <a class=news-link>[link]</a>, and nested <a>
    is invalid HTML - the browser silently closes the outer anchor and
    the row loses its grid layout. JS handles row-clicks instead.
    """
    items = (data.get("news") or {}).get("items", [])
    if not items:
        return ""

    items = sorted(items, key=lambda i: parse_date(i.get("date", "")), reverse=True)
    items = items[:_NEWS_MAX_ITEMS]

    parts = []
    for item in items:
        tags = _normalize_tags(item.get("tags"))
        date_html = f'<span class="news-date">{esc(format_date(item["date"], short=True))}</span>'

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
        attrs = f' data-href="#timeline:tl-{esc(ref)}" role="link" tabindex="0"' if ref else ""
        parts.append(
            f'<li><div class="news-row"{attrs}>'
            f'{date_html}{content_html}{tag_html}</div></li>'
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Timeline - two-sided chronology, no nav entry (reached via News clicks)
# ---------------------------------------------------------------------------

# Type -> (side, dot/border colour). Paper-related events (publications +
# paper awards) go on the LEFT; institutional events (degree, experience,
# research positions) go on the RIGHT. The right side is intentionally
# given more width since those titles + org names run long.
_TIMELINE_TYPE_META = {
    "publication": ("left",  "#10b981"),  # only when a pub has no `source:`
    "award":       ("left",  "#b58900"),  # orphan honors (no parent entry)
    "degree":      ("right", "#6c71c4"),  # formal credentials -> right side
    "experience":  ("left",  "#2aa198"),  # internships / positions -> left
    "research":    ("left",  "#2aa198"),  # research projects -> left
}


def _timeline_exp_event(item, ev_type):
    """Build a timeline event from an education/experience/research record.
    The `id` field is the slug used to match a publication's `source:`
    field, so a paper can be embedded inside the position card it came
    out of. The id is `item.id` if explicitly set in YAML, otherwise
    `slugify(title)` -- explicit ids are needed when several entries
    share the same position title (e.g. multiple 'Undergraduate Research
    Project' rows in research.yaml)."""
    title = item.get("degree") or item.get("position", "")
    item_id = item.get("id") or slugify(title)
    return {
        "date": item.get("start_date"), "end_date": item.get("end_date"),
        "type": ev_type,
        "title": title,
        "id": item_id,
        "subtitle": item.get("institution") or item.get("company", ""),
        "logo": item.get("logo"),
        "link": item.get("link"),
        "awards": item.get("awards"),
    }


def _render_nested_pub(paper):
    """Two-line chip inside the parent card:
      line 1 -> [venue] title
      line 2 -> short authors (highlighted self)
    Awards (Best Paper etc) and external links sit just under, with the
    same coloured left border picking up the parent's dot colour."""
    title = esc(paper.get("title", ""))
    authors = highlight_author(esc(paper.get("authors", "")))
    venue = esc(paper.get("venue_short") or paper.get("venue", ""))
    date = esc(format_date(paper.get("date"), short=True))
    venue_tag = (
        f'<span class="nested-pub-venue-tag">{venue}</span>' if venue else ""
    )
    links = [l for l in (paper.get("links") or []) if l.get("url")]
    links_html = ""
    if links:
        items = "".join(
            f'<a href="{esc(l["url"])}" target="_blank" rel="noopener noreferrer" '
            f'class="timeline-link">{esc(l["name"])}</a>'
            for l in links
        )
        links_html = f'<div class="timeline-links">{items}</div>'
    return (
        f'<div class="nested-pub" title="{title}">'
        f'<div class="nested-pub-line-1">'
        f'{venue_tag}'
        f'<span class="nested-pub-title">{title}</span>'
        f'<span class="nested-pub-date">{date}</span>'
        f'</div>'
        f'<div class="nested-pub-line-2">{authors}</div>'
        f'{_render_awards(paper.get("awards"))}'
        f'{links_html}'
        f'</div>'
    )


# Pixels per year of timeline height (true-cartesian: B.Sc. spanning
# 2018->2022 becomes ~4 x this tall). Used as the minimum date->Y
# mapping; cards may push subsequent siblings further apart when their
# rendered content exceeds the natural year-derived spacing.
_TIMELINE_YEAR_PX = 120
_TIMELINE_GAP_PX = 24  # min vertical gap between consecutive cards


def _estimate_card_height(e, slim=False):
    """Rough px-height of a rendered timeline card. Used to push later
    cards down when their natural date position would collide. Tuned to
    over-estimate slightly (better to have a bit of breathing room than
    to clip)."""
    if slim:
        pad = 14            # 7px * 2 vertical padding
        date_h = 17
        title_lh = 19
        text_lh = 17
        links_h = 22
        title_cpl = 30      # chars per line; conservative for ~280px width
        text_cpl = 40
    else:
        pad = 30
        date_h = 21
        title_lh = 24
        text_lh = 22
        links_h = 28
        # Multi-lane left side -> a 3-lane layout gives each card ~250px
        # of width, ~225px of inner text width. Bold 1em title fits ~22
        # chars per line; 0.9em text fits ~28. Anything bigger here
        # undercounts wraps and the per-lane post-pass leaves siblings
        # overlapping.
        title_cpl = 22
        text_cpl = 28
    h = pad + date_h + 4
    title = e.get("title", "") or ""
    h += max(1, -(-len(title) // title_cpl)) * title_lh
    if e["type"] == "publication" and e.get("authors"):
        h += max(1, -(-len(e["authors"]) // text_cpl)) * text_lh
    if e.get("subtitle"):
        h += max(1, -(-len(e["subtitle"]) // text_cpl)) * text_lh
    has_links = (e.get("links") and any(l.get("url") for l in e["links"])) or e.get("link")
    if has_links:
        h += links_h
    # Entry's own attached awards (TUBITAK badge on CONTSEC, Best Paper
    # on the IDS pub, ...). Each award badge takes one line + a tiny
    # margin.
    for _ in e.get("awards") or []:
        h += 26
    # Nested publications attached to this entry (via pub.source ==
    # entry.id). Tuned to match the rendered 2-line chip:
    #   ~6 px top margin + 10 px padding + 18 px line-1 (font 0.86em
    #   line-h 1.25 + venue-tag border) + 14 px line-2 = ~48 px base.
    # Round up a touch (50) so the layout estimator leans toward "a
    # little too much space" instead of "a little overlap".
    for child in e.get("child_pubs") or []:
        child_h = 50
        if child.get("links"):
            child_h += 18
        if child.get("awards"):
            child_h += 22
        h += child_h
    return h


def _date_frac(date_str):
    """Date string to fractional year. 2024 -> 2024.0, 2024-08 -> 2024.583."""
    if not date_str:
        return None
    s = str(date_str).strip()
    if s.lower() == "present":
        from datetime import datetime
        now = datetime.now()
        return now.year + (now.month - 1) / 12
    m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$", s)
    if m:
        y = int(m.group(1))
        mo = int(m.group(2) or 1)
        d = int(m.group(3) or 1)
        return y + (mo - 1) / 12 + (d - 1) / 365.0
    m = re.match(r"^([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        from .build_utils import MONTHS
        mo = MONTHS.get(m.group(1), 1)
        return int(m.group(2)) + (mo - 1) / 12
    m = re.match(r"^(\d{4})-(\d{4})$", s)
    if m:
        return int(m.group(2))  # range -> end year
    return None


def _render_timeline_card(e, top_px, height_px=None, lane=0, lanes=1, slim=False):
    """Render a single timeline card with absolute positioning + lane info."""
    side, color = _TIMELINE_TYPE_META.get(e["type"], ("right", "var(--accent-color)"))
    anchor = f"tl-{slugify(e['title'])}"
    slim_cls = " timeline-slim" if slim else ""

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
        body.append(_render_awards(e.get("awards")))
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
        body.append(_render_awards(e.get("awards")))
        if e.get("link"):
            body.append(
                f'<div class="timeline-links">'
                f'<a href="{esc(e["link"])}" target="_blank" '
                f'rel="noopener noreferrer" class="timeline-link">Link</a></div>'
            )
        for child_pub in e.get("child_pubs") or []:
            body.append(_render_nested_pub(child_pub))

    # Card positioning still uses var(--right-side-w) / var(--left-side-w),
    # but ONLY for `left:` / `right:` / `width:` on the card itself - those
    # properties resolve percentages against .timeline (the card's
    # positioned ancestor), which is correct.
    lane_recip = 1.0 / max(1, lanes)
    style = (
        f"top: {top_px:.1f}px; --dot-color: {color}; "
        f"--lane: {lane}; --lanes: {lanes}; --lane-recip: {lane_recip:.6f};"
    )
    if height_px is not None:
        style += f" min-height: {height_px:.1f}px;"
    card_html = (
        f'<div id="{anchor}" class="timeline-item timeline-{e["type"]} timeline-{side}{slim_cls}" '
        f'style="{style}">{"".join(body)}</div>'
    )

    # The dot+arm are rendered as a SIBLING of the card (direct child of
    # .timeline), not as the card's pseudo-element. This is essential
    # because pseudo-element percentages resolve against the host (the
    # narrow card), not the timeline - so `var(--right-side-w)` inside
    # the card's ::before is wrong. As a sibling of the card, the
    # rail-marker's containing block is .timeline, percentages resolve
    # correctly, and the arm extends precisely to the rail for every
    # lane.
    lane_ratio = lane / max(1, lanes)
    rail_marker = (
        f'<div class="rail-marker rail-marker-{side}" aria-hidden="true" '
        f'style="top: {top_px:.1f}px; --lane-ratio: {lane_ratio:.6f}; '
        f'--dot-color: {color};"></div>'
    )
    # rail-marker is placed AFTER the card so the `.timeline-item:hover +
    # .rail-marker` sibling combinator can light up the right dot.
    return card_html + rail_marker


def render_timeline(data):
    """Cartesian timeline: vertical axis is time, absolute Y per event.
    Range entries (B.Sc., M.Sc., experience positions) get min-height
    proportional to their duration so they visibly span their years.
    """
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

    # Index parents by id so each publication's `source:` field can
    # look up its parent card directly.
    parent_index = {e["id"]: e for e in events if e.get("id")}

    for paper in (data.get("publications") or {}).get("papers", []):
        source = paper.get("source")
        if source:
            parent = parent_index.get(source)
            if parent is None:
                # Data-integrity warning: surface at build time so
                # typos / renamed positions don't silently drop a paper.
                print(
                    f"Warning: publication '{paper.get('title','')[:60]}' "
                    f"has source='{source}' but no timelined position "
                    f"with that slug exists. Available: "
                    f"{sorted(parent_index)}",
                    file=sys.stderr,
                )
            else:
                parent.setdefault("child_pubs", []).append(paper)
                continue  # don't render as a standalone event
        events.append({
            "date": paper.get("date"), "type": "publication",
            "title": paper.get("title", ""),
            "authors": paper.get("authors", ""),
            "subtitle": paper.get("venue_short") or paper.get("venue", ""),
            "links": paper.get("links"),
            "awards": paper.get("awards"),
        })

    # Standalone (orphan) honors. Awards that belong to a specific paper
    # or degree live as nested `awards` on that parent entry instead and
    # are surfaced inline by _render_awards; only honors with no natural
    # parent (scholarships, fellowships) opt in here via `timelined: true`.
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

    # Annotate with fractional year positions; drop events with no date.
    for e in events:
        e["_start"] = _date_frac(e.get("date"))
        e["_end"] = _date_frac(e.get("end_date")) if e.get("end_date") else e["_start"]
    events = [e for e in events if e["_start"] is not None]
    if not events:
        return ""

    fracs = [e["_end"] for e in events] + [e["_start"] for e in events]
    top_year = int(max(fracs)) + 1
    bot_year = int(min(fracs))

    # Split events by side
    left, right = [], []
    for e in events:
        side, _ = _TIMELINE_TYPE_META.get(e["type"], ("right", ""))
        (left if side == "left" else right).append(e)

    # ---- Lane assignment for both sides (greedy interval colouring).
    # Range events that overlap in time get parallel lanes so they don't
    # collide horizontally. Point events get a tiny `pad` so even
    # same-date pubs don't share a lane.
    def assign_lanes(group, pad=0.1):
        sorted_g = sorted(group, key=lambda e: e["_start"])
        lane_ends = []
        for e in sorted_g:
            s, en = e["_start"], max(e["_end"], e["_start"] + pad)
            for i in range(len(lane_ends)):
                if lane_ends[i] <= s:
                    lane_ends[i] = en
                    e["_lane"] = i
                    break
            else:
                e["_lane"] = len(lane_ends)
                lane_ends.append(en)
        return max(len(lane_ends), 1)

    n_left = assign_lanes(left)
    n_right = assign_lanes(right)

    # ---- VARIABLE-BAND LAYOUT: every year gets its own band whose
    # height is just enough to hold the densest column's content for
    # that year. All columns share these band positions, so a 2024
    # paper on the left and a 2024 internship on the right land in the
    # same vertical region as the 2024 year label. Years with no events
    # collapse to a small minimum band; years with three concurrent
    # papers grow accordingly. This is the "auto-fit" the user asked
    # for: no wasted whitespace, year labels stay locked to their events.
    from collections import defaultdict as _dd
    GAP = _TIMELINE_GAP_PX
    # MIN_BAND = baseline year-band height. Years with no events still
    # take a visible slice of rail at this size.
    # BAND_CAP  = ceiling per year. A short-span dense card (e.g. SIPLab:
    # 2 pubs in 3 months -> would demand ~1100 px / year if uncapped)
    # would otherwise blow the canvas up. Past the cap, the extra
    # content is absorbed by per-lane stacking instead of by year
    # inflation: the card extends downward, the post-pass bumps its
    # in-lane neighbour clear of the bottom.
    MIN_BAND = 90
    BAND_CAP = 300
    MIN_GAP_BELOW_YEAR = 8

    # Group both sides by lane. Each lane within a side acts as an
    # independent column for the variable-band content-fit calc.
    left_lane_groups = _dd(list)
    for e in left:
        left_lane_groups[e.get("_lane", 0)].append(e)
    right_lane_groups = _dd(list)
    for e in right:
        right_lane_groups[e.get("_lane", 0)].append(e)

    # `slim` flag controls the typography/padding of point cards. Range
    # cards never use slim. Only standalone publications (rare now that
    # most pubs nest into a parent via `source:`) get slim treatment.
    def _is_slim(e):
        return e["type"] == "publication"

    columns = (
        [(g, False) for g in left_lane_groups.values()]
        + [(g, False) for g in right_lane_groups.values()]
    )

    # Step 1: required band height per year from point events.
    # band[y] is the px height of the band representing year y (i.e. the
    # vertical slab between the year (y+1) label at top and year y label
    # at bottom). Point events with int(end) == y sit in this band.
    band = {y: MIN_BAND for y in range(bot_year, top_year + 1)}
    for col, _ in columns:
        per_year_points = _dd(list)
        for e in col:
            is_range = e.get("end_date") and e["_end"] - e["_start"] > 0.05
            if is_range:
                continue
            per_year_points[int(e["_end"])].append(e)
        for y, evs in per_year_points.items():
            h = sum(_estimate_card_height(e, slim=_is_slim(e)) for e in evs)
            h += GAP * max(0, len(evs) - 1)
            h += MIN_GAP_BELOW_YEAR
            band[y] = max(band.get(y, MIN_BAND), h)

    # Step 2: range events. Grow each year band so the range card's
    # content fits within its date span - i.e. "make the rail longer
    # for that year". A short-span card with lots of nested content
    # (CONTSEC: 3 pubs in 9 months, SIPLab: 2 pubs in 3 months) demands
    # a tall band on the year(s) it spans; sparse years collapse to
    # MIN_BAND. Year labels then end up exactly at the natural date
    # positions of every event - no drift, no overlap.
    range_events = [
        e for e in events
        if e.get("end_date") and e["_end"] - e["_start"] > 0.05
    ]

    def _band_weights(e):
        s, en = e["_start"], e["_end"]
        s_y, e_y = int(s), int(en)
        s_frac, e_frac = s - s_y, en - e_y
        weights = {}
        if s_y == e_y:
            weights[s_y] = max(0.05, e_frac - s_frac)
        else:
            weights[s_y] = max(0.05, 1 - s_frac)
            for y in range(s_y + 1, e_y):
                weights[y] = 1.0
            weights[e_y] = max(0.05, e_frac)
        return weights

    for _ in range(30):
        changed = False
        for e in range_events:
            need = _estimate_card_height(e, slim=False) + MIN_GAP_BELOW_YEAR
            weights = _band_weights(e)
            actual = sum(band.get(y, MIN_BAND) * w for y, w in weights.items())
            if actual + 0.5 < need:
                deficit = need - actual
                total_w = sum(weights.values())
                if total_w > 1e-6:
                    grow = deficit / total_w
                    any_grew = False
                    for y in weights:
                        new_val = min(BAND_CAP, band.get(y, MIN_BAND) + grow)
                        if new_val > band.get(y, MIN_BAND) + 0.5:
                            band[y] = new_val
                            any_grew = True
                        else:
                            band[y] = new_val
                    if any_grew:
                        changed = True
        if not changed:
            break

    # Step 3: year-label positions (cumulative bands from top).
    year_label_y = {top_year: 0.0}
    cum = 0.0
    for y in range(top_year - 1, bot_year - 1, -1):
        cum += band[y]
        year_label_y[y] = cum
    total_h = int(cum + 40)

    def _y_at_date(d):
        """Map a fractional date to its y-position on the shared axis."""
        y_int = int(d)
        frac = d - y_int            # 0 (Jan 1, y_int) .. 1 (Jan 1, y_int+1)
        top_y = year_label_y.get(y_int + 1, 0.0)
        bot_y = year_label_y.get(y_int, total_h)
        return top_y + (1 - frac) * (bot_y - top_y)

    # Step 4: place cards.
    # Range cards: top = y at end date; height = max(span_h, content_h).
    # Point cards: stack within their year band, newest first.
    # Then a per-lane post-pass walks the lane top-down (newest first)
    # and pushes each card down whenever the previous newer card's
    # bottom would overlap. This is what guarantees no within-lane
    # vertical collision when a short-span range card has more nested
    # content than its date span can hold.
    for col, _ in columns:
        col.sort(key=lambda e: e["_end"], reverse=True)
        col_cursor = {}
        for e in col:
            is_range = e.get("end_date") and e["_end"] - e["_start"] > 0.05
            if is_range:
                top_px = _y_at_date(e["_end"])
                bot_px = _y_at_date(e["_start"])
                content_h = _estimate_card_height(e, slim=False)
                e["_top_px"] = top_px
                e["_est_h"] = max(bot_px - top_px, content_h)
                continue
            y = int(e["_end"])
            band_top = year_label_y.get(y + 1, 0.0)
            cursor = col_cursor.get(y, band_top + MIN_GAP_BELOW_YEAR)
            h = _estimate_card_height(e, slim=_is_slim(e))
            e["_top_px"] = cursor
            e["_est_h"] = h
            col_cursor[y] = cursor + h + GAP

        # Per-lane vertical collision fix: walk newest-first and push
        # each card down so its top is at least prev_bot + GAP.
        prev_bot = -1e9
        for e in col:
            if e["_top_px"] < prev_bot + GAP:
                e["_top_px"] = prev_bot + GAP
            prev_bot = e["_top_px"] + e["_est_h"]

    # Recompute total height: cards may have been pushed past the
    # natural canvas bottom by the per-lane shift.
    if events:
        canvas_max = max(e["_top_px"] + e["_est_h"] for e in events if "_top_px" in e)
        total_h = max(total_h, int(canvas_max + 40))

    # Render newest end first so DOM order matches visual stacking
    events.sort(key=lambda e: e["_end"] or 0, reverse=True)

    # Emit the per-build lane counts so the CSS computes one uniform
    # --lane-w across all sub-columns (no left-vs-right width asymmetry).
    n_total = n_left + n_right
    total_recip = 1.0 / max(1, n_total)
    timeline_style = (
        f"height: {total_h:.0f}px; "
        f"--n-left: {n_left}; --n-right: {n_right}; "
        f"--n-total: {n_total}; --total-recip: {total_recip:.6f};"
    )
    parts = [f'<div class="timeline" style="{timeline_style}">']
    # Month ticks on the rail (small dashes between consecutive year
    # labels). The band per year is variable, so each tick is placed at
    # the m/12 fraction of its year's band height.
    for y in range(top_year - 1, bot_year - 1, -1):
        band_top = year_label_y.get(y + 1, 0.0)
        band_h = band.get(y, 0)
        if band_h <= 0:
            continue
        for m in range(1, 12):
            tick_y = band_top + (m / 12.0) * band_h
            parts.append(
                f'<div class="timeline-month-tick" style="top: {tick_y:.1f}px"></div>'
            )
    for y, y_pos in year_label_y.items():
        parts.append(
            f'<div class="timeline-year-label" style="top: {y_pos:.1f}px">{y}</div>'
        )

    for e in events:
        side, _ = _TIMELINE_TYPE_META.get(e["type"], ("right", ""))
        top_px = e["_top_px"]
        n_lanes = n_left if side == "left" else n_right
        slim = _is_slim(e)
        # Always enforce the packed est_h as min-height: it's what the
        # per-lane post-pass used to space siblings, and if the actual
        # rendered content turns out larger than the estimate, the card
        # still grows past min-height - but never SHRINKS below it, so
        # the next-in-lane card never collides.
        est_h = e.get("_est_h", 0)
        height_px = est_h if est_h > 1 else None
        parts.append(_render_timeline_card(
            e, top_px, height_px, lane=e.get("_lane", 0), lanes=n_lanes,
            slim=slim,
        ))

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
    """Render open source projects as cards. On About > Open Source:
      - the title links to the GitHub repo,
      - the rest of the card surface links to the project page.
    The standalone GitHub tag-box is intentionally dropped here; it's
    still rendered by build_projects on the project page itself."""
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
        project_href = f"projects/{slug}/index.html"
        github_url = work.get("url", "")

        title_html = (
            f'<a href="{esc(github_url)}" class="work-name" '
            f'target="_blank" rel="noopener noreferrer">{esc(work["title"])}</a>'
            if github_url else
            f'<span class="work-name">{esc(work["title"])}</span>'
        )

        parts.append(
            f'<div class="work-item" data-href="{esc(project_href)}" '
            f'role="link" tabindex="0">'
            f'<div class="work-head">'
            f'<i class="fab fa-github work-icon" aria-hidden="true"></i>'
            f'<span class="work-titles">{title_html}{repo_html}</span></div>'
            f'{desc}{tags}</div>'
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

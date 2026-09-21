"""
HTML rendering functions for the static site.

Each function takes data (dicts loaded from YAML) and returns an HTML string.
"""

import json
import re
import sys

from .build_config import (
    BASE_DIR,
    LINK_ICONS,
    LINK_NAMES,
    PRIMARY_LINKS,
    SECONDARY_CATEGORIES,
    URL_TEMPLATES,
)
from .build_utils import esc, format_date, highlight_author, highlight_author_span, linkify_names_html, parse_date, slugify


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def primary_affiliation(bio):
    """First affiliation name, for meta/JSON-LD. Falls back to the legacy
    singular `affiliation` field if the list isn't present."""
    affs = bio.get("affiliations") or []
    if affs:
        return affs[0].get("name", "")
    return bio.get("affiliation", "")


def _render_social_link(platform, uid, metrics_html="", label=None):
    """Render a single social link element. metrics_html (if any) sits on the
    same row, right-aligned. label overrides the visible text (the full name
    stays in the title/aria-label)."""
    url = URL_TEMPLATES[platform].format(id=esc(uid))
    icon = LINK_ICONS.get(platform, "")
    full = LINK_NAMES.get(platform, platform)
    shown = label or full
    target = "" if platform == "email" else ' target="_blank" rel="noopener noreferrer"'
    return (
        f'<a href="{url}" class="social-link" title="{esc(full)}" '
        f'aria-label="{esc(full)}"{target}>'
        f'<i class="{icon}"></i>'
        f'<span class="social-label">{esc(shown)}</span>'
        f'{metrics_html}</a>'
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

    # Identity: name, then the descriptive bio (replaces the old title line).
    parts.append(f'<h1 class="sidebar-name">{esc(bio["name"])}</h1>')

    if bio.get("short_bio"):
        parts.append(f'<p class="bio-short">{esc(bio["short_bio"])}</p>')

    # Contact group: location + live local clock + the booking link.
    meta_bits = []
    if bio.get("location"):
        meta_bits.append(
            f'<span class="sidebar-location">'
            f'<i class="fas fa-location-dot"></i> {esc(bio["location"])}</span>'
        )
    if bio.get("timezone"):
        meta_bits.append(
            f'<span class="sidebar-localtime"><i class="fas fa-clock"></i> '
            f'<span class="local-time" data-tz="{esc(bio["timezone"])}">--:--</span> '
            f'<span class="lt-label">local time</span></span>'
        )
    schedule = render_appointment_calendar(bio)
    if schedule:
        meta_bits.append(schedule)
    if meta_bits:
        parts.append(f'<div class="sidebar-meta">{"".join(meta_bits)}</div>')

    # Affiliations are rendered LAST (after the links) as footer-style contact
    # details; build the HTML here, append it at the very bottom.
    aff_items = []
    for aff in bio.get("affiliations") or []:
        name = esc(aff.get("name", ""))
        if not name:
            continue
        if aff.get("url"):
            name = (f'<a href="{esc(aff["url"])}" target="_blank" '
                    f'rel="noopener noreferrer">{name}</a>')
        detail = esc(aff.get("detail", ""))
        if detail and aff.get("map"):
            detail = (f'<a href="{esc(aff["map"])}" target="_blank" '
                      f'rel="noopener noreferrer">{detail}</a>')
        detail_html = f'<span class="affiliation-detail">{detail}</span>' if detail else ""
        phone_html = ""
        if aff.get("phone"):
            phone = str(aff["phone"]).strip()
            tel = "tel:" + re.sub(r"[^\d+]", "", phone)
            phone_html = (
                f'<span class="affiliation-phone">'
                f'<a href="{esc(tel)}">{esc(phone)}</a></span>'
            )
        contact = detail_html + phone_html
        if contact:
            contact = f'<span class="affiliation-contact">{contact}</span>'
        aff_items.append(
            f'<li class="affiliation">'
            f'<span class="affiliation-name">{name}</span>{contact}</li>'
        )
    affiliations_html = (
        f'<ul class="sidebar-affiliations">{"".join(aff_items)}</ul>'
        if aff_items else ""
    )

    # Links container. Metric badges (citations / stars / PRs) are optional:
    # set `show_metrics: true` in bio.yaml to enable them. When off, no badges
    # render and the data-github/data-scholar hooks (which drive the live
    # refresh in initStats) are omitted too.
    social = bio.get("social") or {}
    show_metrics = bool(bio.get("show_metrics"))
    if show_metrics:
        gh = esc((social.get("github") or "").strip())
        gs = esc((social.get("google_scholar") or "").strip())
        parts.append(f'<div class="links" data-github="{gh}" data-scholar="{gs}">')
        metrics = bio.get("metrics") or {}
    else:
        parts.append('<div class="links">')
        metrics = {}
    # Shorter visible labels for links that carry metric badges, so the badges
    # fit on the same row in the narrow sidebar (full name stays in the title).
    SIDEBAR_LABELS = {"google_scholar": "Scholar"}

    # Primary links (always visible), each with its metric badges inline.
    for platform in PRIMARY_LINKS:
        uid = social.get(platform)
        if uid and str(uid).strip() and platform in URL_TEMPLATES:
            parts.append(_render_social_link(
                platform, uid,
                _link_metrics_html(platform, metrics),
                label=SIDEBAR_LABELS.get(platform),
            ))

    # Custom links (Resume PDF, etc.). PDF targets get a file-pdf icon and
    # render in the same icon+label style as the GitHub/Scholar links.
    for link in bio.get("custom_links") or []:
        url = link["url"]
        name = esc(link["name"])
        if url.lower().endswith(".pdf"):
            parts.append(
                f'<a class="social-link" href="{esc(url)}" title="{name}" '
                f'aria-label="{name}" target="_blank" rel="noopener noreferrer">'
                f'<i class="fas fa-file-pdf"></i>'
                f'<span class="social-label">{name}</span></a>'
            )
        else:
            target = ' target="_blank" rel="noopener noreferrer"' if url.startswith("http") else ""
            parts.append(f'<a href="{esc(url)}"{target}>{name}</a>')

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

    # Affiliations (institution / office / phone) at the very bottom.
    parts.append(affiliations_html)

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Bio
# ---------------------------------------------------------------------------

def render_bio(bio):
    """Render About Me paragraphs. Bio text is trusted HTML (author-controlled)."""
    paragraphs = bio.get("bio", "").split("\n\n")
    return "\n".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())


# Metric badges shown beneath the relevant sidebar link. Values are baked
# from bio.yaml `metrics:` so the badges always show real numbers; GitHub's
# stars/PRs are then refreshed live on top by initStats() in data.js.
# (key, label, metrics-subdict, value-key-in-yaml)
_LINK_METRICS = {
    "github": [
        ("stars", "stars", "github", "stars"),
        ("prs", "PRs", "github", "prs"),
    ],
    "google_scholar": [
        ("citations", "cited", "scholar", "citations"),
        ("hindex", "h", "scholar", "h_index"),
        ("i10", "i10", "scholar", "i10"),
    ],
}


def _fmt_count(n):
    """Compact number: 1234 -> '1,234', 12000 -> '12k'."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return None
    if n >= 1000:
        return f"{n/1000:.1f}".rstrip("0").rstrip(".") + "k"
    return f"{n:,}"


def _link_metrics_html(platform, metrics):
    spec = _LINK_METRICS.get(platform)
    if not spec:
        return ""
    chips = []
    for stat_key, label, group, yaml_key in spec:
        val = ((metrics or {}).get(group) or {}).get(yaml_key)
        shown = _fmt_count(val)
        if shown is None:
            continue
        chips.append(
            f'<span class="link-metric">'
            f'<span class="lm-value" data-stat="{stat_key}">{shown}</span> '
            f'<span class="lm-label">{esc(label)}</span></span>'
        )
    if not chips:
        return ""
    return f'<div class="link-metrics">{"".join(chips)}</div>'


def render_appointment_calendar(bio):
    """A plain "Schedule a meeting" link. initAppointment() in data.js opens the
    booking calendar in an in-page overlay (a dimmed backdrop + centered white
    dialog, same window -- the behavior of Google's own scheduling button).
    data-booking is the `?gv=true` embeddable view. The href is a no-JS
    fallback. Reads `appointment_url` from bio.yaml; '' when unset."""
    url = (bio.get("appointment_url") or "").strip()
    if not url:
        return ""
    sep = "&" if "?" in url else "?"
    embed = esc(url + sep + "gv=true")
    return (
        f'<a class="sidebar-schedule" href="{esc(url)}" data-booking="{embed}" '
        f'rel="noopener noreferrer">'
        f'<i class="fas fa-calendar-day"></i> Schedule a meeting</a>'
    )


# platform key -> (display label, icon class, brand color for the icon)
_POST_PLATFORM = {
    "linkedin": ("LinkedIn", "fa-brands fa-linkedin",  "#0a66c2"),
    "twitter":  ("X",        "fa-brands fa-x-twitter", "currentColor"),
    "x":        ("X",        "fa-brands fa-x-twitter", "currentColor"),
}


def render_social_posts(data):
    """"Recent Posts" section at the bottom of the Blogs tab. Each curated post
    in `posts:` (data/social_posts.yaml) renders as a link-preview card with
    the post's title, excerpt and optional thumbnail. Cards are used instead of
    live iframe/widget embeds because those render blank on mobile and for
    logged-out visitors. Returns '' when no posts are configured.
    Each entry: platform, url, title, [excerpt], [image]."""
    posts = (data.get("social_posts") or {}).get("posts") or []

    cards = []
    for p in posts:
        key = (p.get("platform") or "").lower()
        url = p.get("url")
        meta = _POST_PLATFORM.get(key)
        if not url or not meta:
            continue
        label, icon, color = meta
        img = p.get("image")
        media = (
            f'<div class="post-card-media">'
            f'<img src="{esc(img)}" alt="" loading="lazy" '
            f'onerror="this.closest(\'.post-card-media\').style.display=\'none\'" />'
            f'</div>' if img else ""
        )
        title = esc(p.get("title", "")) or f"Post on {esc(label)}"
        excerpt = esc(p.get("excerpt", ""))
        excerpt_html = f'<p class="post-card-excerpt">{excerpt}</p>' if excerpt else ""
        cards.append(
            f'<a class="social-card post-card post-card-{esc(key)}" '
            f'href="{esc(url)}" target="_blank" rel="noopener noreferrer">'
            f'{media}'
            f'<div class="post-card-body">'
            f'<span class="post-card-source">'
            f'<i class="{icon}" style="color:{color}"></i> {esc(label)}</span>'
            f'<span class="post-card-title">{title}</span>'
            f'{excerpt_html}'
            f'<span class="post-card-link">View on {esc(label)} '
            f'<i class="fa-solid fa-arrow-right"></i></span>'
            f'</div></a>'
        )
    if not cards:
        return ""
    return (
        '<div class="content-section" id="social-posts-section">'
        '<h2>Media Posts</h2>'
        f'<div id="recent-posts" class="social-grid">{"".join(cards)}</div>'
        '</div>'
    )


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
    "CNR":      "#8b5e34",   # CNR Edizioni book chapter
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
    token = re.sub(r"'\d+$", "", token)  # "ECCV'24" -> "ECCV"
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


def _render_awards(awards, compact=False):
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
        org_html = "" if compact else (
            f' <span class="award-org">- {esc(org)}</span>' if org else "")
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


_STATUS_LABELS = {
    "under-review": "Under Review",
    "in-progress": "In Progress",
}


def _status_badge(paper):
    """Render an in-progress / under-review badge, or '' when the paper
    has no status set."""
    status = paper.get("status")
    if not status:
        return ""
    text = _STATUS_LABELS.get(str(status).strip().lower(), str(status).strip())
    return f'<span class="pub-status">{esc(text)}</span>'


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

    media = paper.get("image")
    if media:
        ext = str(media).rsplit(".", 1)[-1].lower()
        if ext in ("mp4", "webm", "mov"):
            # Looping inline preview video (al-folio style); muted +
            # playsinline so mobile browsers autoplay it.
            tag = (
                f'<video src="{esc(media)}" autoplay loop muted playsinline '
                f'preload="metadata" aria-label="{esc(paper["title"])}"></video>'
            )
        else:  # png / jpg / gif / webp all render through <img>
            tag = f'<img src="{esc(media)}" alt="{esc(paper["title"])}" loading="lazy" />'
        parts.append(f'<div class="publication-image">{tag}</div>')
    parts.append("</div>")

    # Right: title, authors, venue, links
    parts.append('<div class="publication-content">')
    slug = slugify(paper["title"])
    parts.append(
        f'<div class="publication-title">'
        f'<a href="projects/{slug}/index.html" class="project-link">{esc(paper["title"])}</a>'
        f'{_status_badge(paper)}</div>'
    )
    parts.append(f'<div class="publication-authors">{highlight_author_span(esc(paper.get("authors", "")))}</div>')

    # Full citation venue: prefix + name + series/volume/pages detail,
    # same joining rules as the CV renderer.
    venue_full = paper.get("venue", "")
    if paper.get("venue_prefix"):
        venue_full = f"{paper['venue_prefix']} {venue_full}"
    detail = paper.get("venue_detail") or ""
    if detail:
        if detail.startswith("("):
            sep = "" if venue_full and venue_full[-1].isdigit() else " "
        else:
            sep = ", "
        venue_full += f"{sep}{detail}"
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
    citation += f" {esc(paper.get('title_apa') or paper['title'])}."
    # Under-review work keeps its venue in the data but doesn't show it
    # yet -- only the status badge.
    if paper.get("status"):
        pass
    elif paper.get("venue_link") and paper.get("venue_short"):
        citation += (
            f' <em><a href="{esc(paper["venue_link"])}" class="venue-link" '
            f'target="_blank" rel="noopener noreferrer">'
            f'{esc(paper["venue_short"])}</a></em>.'
        )
    elif paper.get("venue"):
        v = f"<em>{esc(paper['venue'])}</em>"
        if paper.get("venue_prefix"):
            v = f"{esc(paper['venue_prefix'])} {v}"
        detail = esc(paper.get("venue_detail") or "")
        if detail:
            if detail.startswith("("):
                sep = "" if paper["venue"][-1].isdigit() else " "
            else:
                sep = ", "
            v += sep + detail
        citation += f" {v}."

    parts.append('<div class="pub-compact-body">')
    parts.append(f'<div class="pub-compact-reference">{citation}</div>')
    parts.append(_render_awards(paper.get("awards")))
    parts.append('</div>')

    # Right column: a status badge (under-review work) or the link pills.
    if paper.get("status"):
        parts.append(_status_badge(paper))
    elif paper.get("links"):
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

_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _md_strip(text):
    """Markdown links and **bold** reduced to bare text (for alt attributes)."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", _MD_LINK.sub(r"\1", str(text)))


def _md_bold(chunk):
    """Escape a text chunk, rendering **phrase** as bold."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(chunk))


def _md_to_html(text):
    """Convert inline markdown links [phrase](url) to anchors and
    **phrase** to bold; escape everything else."""
    out, last = [], 0
    for m in _MD_LINK.finditer(text):
        out.append(_md_bold(text[last:m.start()]))
        out.append(
            f'<a href="{esc(m.group(2))}" target="_blank" rel="noopener noreferrer">'
            f'{esc(m.group(1))}</a>'
        )
        last = m.end()
    out.append(_md_bold(text[last:]))
    return "".join(out)


def _render_resume_item(title, subtitle, date, description="", logo=None,
                        links=None, logo_link=None, commitment=None,
                        advisor=None, bullets=None, awards=None, thesis=None,
                        advisor_label="Advisor"):
    """Render a single resume entry with logo, header, bullets, and links."""
    parts = ['<div class="resume-item">']

    if logo:
        parts.append('<div class="resume-logo">')
        img = f'<img src="{esc(logo)}" alt="{esc(_md_strip(subtitle))}" loading="lazy" width="40" height="40" />'
        if logo_link:
            parts.append(f'<a href="{esc(logo_link)}" target="_blank" rel="noopener noreferrer">{img}</a>')
        else:
            parts.append(img)
        parts.append("</div>")

    parts.append('<div class="resume-details">')
    parts.append(f'<div class="resume-header"><strong>{esc(title)}</strong>'
                 f'<span class="date">{esc(date)}</span></div>')

    parts.append(f'<div class="resume-subheader"><span>{_md_to_html(subtitle)}</span>')
    if commitment and str(commitment).strip():
        parts.append(f'<span class="resume-commitment">{esc(commitment)}</span>')
    parts.append("</div>")

    if thesis and thesis.get("title"):
        t = esc(thesis["title"])
        if thesis.get("link"):
            t = (f'<a href="{esc(thesis["link"])}" target="_blank" '
                 f'rel="noopener noreferrer">{t}</a>')
        parts.append(f'<div class="resume-thesis"><strong>{esc(thesis.get("label", "Thesis"))}:</strong> {t}</div>')

    if advisor and str(advisor).strip():
        parts.append(f'<div class="resume-advisor"><strong>{esc(advisor_label)}:</strong> {linkify_names_html(_md_to_html(advisor))}</div>')

    if description:
        parts.append(f"<p>{esc(description)}</p>")

    if bullets:
        parts.append('<ul class="resume-bullets">')
        for bullet in bullets:
            parts.append(f"<li>{_md_to_html(bullet)}</li>")
        parts.append("</ul>")

    parts.append(_render_awards(awards))
    parts.append(_render_pub_links(links))
    parts.append("</div></div>")
    return "\n".join(parts)


def _render_section(items, title_key, subtitle_key, date_fn, advisor_label="Advisor"):
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
            thesis=item.get("thesis"),
            advisor_label=advisor_label,
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
    return _render_section(items, "position", "company", _date_range, advisor_label="Supervisor")


def render_research(data):
    # Project / lab name carries the entry; the generic role label
    # ("Undergraduate Research Project") is the subtitle.
    items = (data.get("research") or {}).get("research", [])
    return _render_section(items, "company", "position", _date_range, advisor_label="Supervisor")


def render_teaching(data):
    items = (data.get("teaching") or {}).get("teaching", [])
    return _render_section(items, "position", "company", _date_range)


def render_honors(data):
    """Honors aggregates every award attached to a publication / degree /
    research / experience entry, plus standalone honors listed in
    extracurricular.yaml (scholarships, fellowships with no single
    parent). Sorted newest first."""
    items = list((data.get("extracurricular") or {}).get("honors", []))
    # Publication awards render as inline badges on the paper itself
    # (_render_awards), so they are intentionally excluded from the
    # aggregated Honors list to avoid duplication.
    sources = [
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


_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _md_links(text):
    """Escape text for HTML, converting [phrase](url) markdown links
    into news-style anchors and **phrase** into bold."""
    out, last = [], 0
    for m in _MD_LINK_RE.finditer(text):
        out.append(_md_bold(text[last:m.start()]))
        out.append(
            f'<a href="{esc(m.group(2))}" class="news-link" '
            f'target="_blank" rel="noopener noreferrer">{esc(m.group(1))}</a>'
        )
        last = m.end()
    out.append(_md_bold(text[last:]))
    return "".join(out)


def render_news(data):
    """News is the curated view of the timeline: every entity (paper,
    degree, position, honor) may carry `news:` entries - a date and a
    hand-written one-liner with inline markdown links - and this
    section collects them newest-first. The full record lives on the
    Timeline page; this is its `selected` cut, the way resume.pdf cuts
    cv.pdf."""
    items = []
    for paper in (data.get("publications") or {}).get("papers", []):
        items.extend(paper.get("news") or [])
    for section in ("education", "experience", "research"):
        for item in (data.get(section) or {}).get(section) or []:
            items.extend(item.get("news") or [])
    for h in (data.get("extracurricular") or {}).get("honors", []):
        items.extend(h.get("news") or [])
    items = [n for n in items if n.get("date") and n.get("text")]
    if not items:
        return ""

    items.sort(key=lambda n: parse_date(n["date"]), reverse=True)
    items = items[:_NEWS_MAX_ITEMS]

    parts = []
    for n in items:
        date_html = f'<span class="news-date">{esc(format_date(n["date"], short=True))}:</span>'
        content_html = f' <span class="news-content">{_md_links(n["text"])}</span>'
        parts.append(
            f'<li><div class="news-row">'
            f'{date_html}{content_html}</div></li>'
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Timeline - two-sided chronology, no nav entry (reached via News clicks)
# ---------------------------------------------------------------------------

# Type -> (side, dot/border colour). Publications are the primary cards
# on the LEFT; degrees sit on the RIGHT; experience / research render as
# parallel position bars along the rail.
_TIMELINE_TYPE_META = {
    "publication": ("left",  "#10b981"),
    "award":       ("left",  "#b58900"),  # orphan honors (no parent entry)
    "degree":      ("right", "#6c71c4"),  # formal credentials -> right side
    "experience":  ("right", "#2aa198"),  # processes: right column
    "research":    ("right", "#859900"),
}

# Order + labels for the timeline type-filter chips (only present types show).
_TL_FILTER_ORDER = [
    ("experience",  "Experience"),
    ("research",    "Research"),
    ("publication", "Publications"),
    ("degree",      "Education"),
    ("award",       "Awards"),
]

def _timeline_exp_event(item, ev_type):
    """Build a timeline event from an education/experience/research record.
    The `id` field is the slug used to match a publication's `source:`
    field, so a paper can be embedded inside the position card it came
    out of. The id is `item.id` if explicitly set in YAML, otherwise
    `slugify(title)` -- explicit ids are needed when several entries
    share the same position title (e.g. multiple 'Undergraduate Research
    Project' rows in research.yaml)."""
    title_link = None
    if ev_type in ("research", "experience"):
        # Position cards lead with the lab / institution name (linked to
        # the lab page); the role label becomes the subtitle.
        company = item.get("company", "")
        m = _MD_LINK.search(company)
        title_link = (m.group(2) if m else None) or item.get("logo_link")
        title = _md_strip(company)
        subtitle = item.get("position", "")
    else:
        title = item.get("degree") or item.get("position", "")
        subtitle = item.get("institution") or item.get("company", "")
    item_id = item.get("id") or slugify(item.get("degree") or item.get("position", ""))
    return {
        "date": item.get("start_date"), "end_date": item.get("end_date"),
        "type": ev_type,
        "title": title,
        "title_link": title_link,
        "id": item_id,
        "pos_id": item.get("id"),
        "subtitle": subtitle,
        "logo": item.get("logo"),
        "link": item.get("link"),
        # Scholarships and other position awards stay off the timeline
        # (they live in the Honors section and the CV awards list);
        # only merit badges on publications render here.
        "awards": [],
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
        f'</div>'
        f'<div class="nested-pub-line-2">{authors}</div>'
        f'{_render_awards(paper.get("awards"), compact=True)}'
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
        pad = 24
        date_h = 16
        title_lh = 18
        text_lh = 16
        links_h = 26
        # Multi-lane left side: with the 0.9em title / 0.78em text a
        # ~250px lane fits ~25 title chars and ~32 text chars per line.
        # Anything bigger here undercounts wraps and the per-lane
        # post-pass leaves siblings overlapping.
        # Single wide publication lane (~420px): generous lines.
        title_cpl = 34
        text_cpl = 46
    h = pad + date_h + 4
    if e.get("news_text"):
        # date line + wrapped sentence + padding
        return pad + date_h + max(1, -(-len(e["news_text"]) // text_cpl)) * text_lh
    title = e.get("title", "") or ""
    h += max(1, -(-len(title) // title_cpl)) * title_lh
    if e["type"] == "publication" and e.get("authors"):
        h += max(1, -(-len(e["authors"]) // text_cpl)) * text_lh
    if e.get("subtitle"):
        h += max(1, -(-len(e["subtitle"]) // text_cpl)) * text_lh
    for label, value in e.get("meta_rows") or []:
        # Meta rows wrap: label + value at 0.66em fits ~64 chars a line.
        txt = re.sub(r"<[^>]+>", "", f"{label} {value}")
        h += max(1, -(-len(txt) // 64)) * 15
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
        child_h = 92  # boxed chip: 3-line title clamp + 2 author lines
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


def _render_timeline_card(e, top_px, height_px=None, lane=0, lanes=1, slim=False,
                          bar_off=None, bar_top=None):
    """Render a single timeline card with absolute positioning + lane info."""
    side, color = _TIMELINE_TYPE_META.get(e["type"], ("right", "var(--accent-color)"))
    if e.get("pos_color"):
        color = e["pos_color"]
    pos_attr = f' data-pos="{esc(e["pos_id"])}"' if e.get("pos_id") else ""
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

    if e.get("news_text"):
        # Atomic news moment: a dated one-liner, no title block.
        body = [
            f'<span class="timeline-date">{date}</span>',
            f'<div class="timeline-newsline">{logo_html}<span>{_md_links(e["news_text"])}</span></div>',
        ]
        lane_ratio = lane / max(1, lanes)
        rail_marker = (
            f'<div class="rail-marker rail-marker-{side} timeline-{e["type"]}"{pos_attr} aria-hidden="true" '
            f'style="top: {top_px:.1f}px; --lane-ratio: {lane_ratio:.6f}; '
            f'--dot-color: {color};"><i class="rail-dot-hit"></i></div>'
        )
        return (
            f'<div id="{anchor}" class="timeline-item timeline-{e["type"]} timeline-{side} timeline-newsitem"{pos_attr} '
            f'style="top: {top_px:.1f}px; --dot-color: {color}; --lane: {lane}; '
            f'--lanes: {lanes}; --lane-recip: {1.0 / max(1, lanes):.6f};">'
            f'{"".join(body)}</div>' + rail_marker
        )

    title_html = esc(e["title"])
    if e.get("title_link"):
        title_html = (
            f'<a href="{esc(e["title_link"])}" target="_blank" '
            f'rel="noopener noreferrer">{title_html}</a>')
    body = [
        f'<span class="timeline-date">{date}</span>',
        f'<h4 class="timeline-title">{logo_html}<span>{title_html}</span></h4>',
    ]

    if e["type"] == "publication":
        body.append(
            f'<div class="timeline-authors">'
            f'{highlight_author(esc(e.get("authors", "")))}</div>'
        )
        if e.get("subtitle"):
            body.append(f'<div class="timeline-venue"><em>{_md_to_html(e["subtitle"])}</em></div>')
        body.append(_render_awards(e.get("awards"), compact=True))
        for label, value in e.get("meta_rows") or []:
            body.append(
                f'<div class="timeline-meta">'
                f'<span class="timeline-meta-label">{label}</span> {value}</div>')
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
            body.append(f'<div class="timeline-org">{_md_to_html(e["subtitle"])}</div>')
        body.append(_render_awards(e.get("awards"), compact=True))
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
    plain_cls = "" if e["type"] == "publication" else " timeline-plain"
    card_html = (
        f'<div id="{anchor}" class="timeline-item timeline-{e["type"]} timeline-{side}{slim_cls}{plain_cls}"{pos_attr} '
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
    # A card that covers a period (a position, a degree) is already drawn on
    # the rail as its coloured bar, so it gets the arm but no dot: a dot
    # would read as a point event on its end date and compete with the news
    # item that marks the real moment.
    span = bool(e.get("end_date"))
    span_cls = " rail-marker-span" if span else ""
    hit = "" if span else '<i class="rail-dot-hit"></i>'
    # The arm of a period card has to start ON its bar, which sits to the
    # LEFT of the rail, so it visibly ties bar and card together.
    bar_var = f" --bar-off: {bar_off}px;" if span and bar_off else ""
    # Meet the bar exactly where it ends: its tip carries the day, so it can
    # sit a few px off the month line the card was anchored on.
    drop = (bar_top - top_px) if (span and bar_top is not None) else 0
    if 0 < drop < 60:
        bar_var += f" --arm-y: {drop:.0f}px;"
    # The marker carries the same timeline-<type> class as its card so the
    # type filter (initTimelineFilter) hides a card together with its dot+arm.
    rail_marker = (
        f'<div class="rail-marker rail-marker-{side}{span_cls} timeline-{e["type"]}"{pos_attr} aria-hidden="true" '
        f'style="top: {top_px:.1f}px; --lane-ratio: {lane_ratio:.6f};{bar_var} '
        f'--dot-color: {color};">{hit}</div>'
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

    # Index the raw section items by id; one stable colour per position
    # paints its rail bar, its publications' borders / dots, and the
    # hover linkage between them.
    raw_parents = {}
    for section in ("education", "experience", "research"):
        for item in (data.get(section) or {}).get(section) or []:
            if item.get("id"):
                item["_section"] = section
                raw_parents[item["id"]] = item
    # Colours go only to positions that actually appear on the timeline
    # (a paper's source, a news owner, or a drawn bar), in an order
    # chosen so related labs land on clearly different hues. A position
    # can also pin its own colour with a `color:` field in its meta.
    _POS_PALETTE = ["#268bd2", "#2aa198", "#cb4b16", "#6c71c4", "#dc322f",
                    "#859900", "#d33682", "#b58900", "#0f766e", "#5b7eb0"]
    used = set()
    for paper in (data.get("publications") or {}).get("papers", []):
        if paper.get("source") and not paper.get("status"):
            used.add(paper["source"])
    for pid, item in raw_parents.items():
        # Anything that draws a bar or owns news gets its own colour.
        if item.get("news") or item.get("start_date"):
            used.add(pid)
    ordered = [pid for pid in raw_parents if pid in used]
    pos_colors = {}
    for i, pid in enumerate(ordered):
        pos_colors[pid] = raw_parents[pid].get("color") or _POS_PALETTE[i % len(_POS_PALETTE)]

    for edu in (data.get("education") or {}).get("education", []):
        if edu.get("timelined"):
            events.append(_timeline_exp_event(edu, "degree"))
    for exp in (data.get("experience") or {}).get("experience", []):
        if exp.get("timelined"):
            events.append(_timeline_exp_event(exp, "experience"))
    for res in (data.get("research") or {}).get("research", []):
        if res.get("timelined"):
            events.append(_timeline_exp_event(res, "research"))

    # Atomic moments of positions and degrees: every entity's `news:`
    # entries render as small dated cards, typed like their owner so
    # the filter chips rebuild the left column per entity kind.
    # (Publication news are skipped: the paper card is that moment.)
    _NEWS_EVENT_TYPE = {"experience": "experience", "research": "research",
                        "education": "degree"}
    for section, ev_type in _NEWS_EVENT_TYPE.items():
        for item in (data.get(section) or {}).get(section) or []:
            for n in item.get("news") or []:
                if n.get("date") and n.get("text"):
                    events.append({
                        "date": n["date"], "type": ev_type,
                        "title": _md_strip(n["text"])[:60],
                        "news_text": n["text"],
                        "logo": item.get("logo"),
                        "pos_id": item.get("id"),
                        "pos_color": pos_colors.get(item.get("id")),
                    })


    for paper in (data.get("publications") or {}).get("papers", []):
        if paper.get("timelined") is False:  # explicitly hidden from the timeline
            continue
        if paper.get("status"):  # under review: not an event yet
            continue
        # Publications are the timeline's primary entities: each renders
        # as a full card at its own date. `source` no longer nests the
        # paper inside the position card; instead the position's
        # supervisor / laboratory / role ride along as meta rows.
        meta_rows = []
        source = paper.get("source")
        if source:
            parent = raw_parents.get(source)
            if parent is None:
                print(
                    f"Warning: publication '{paper.get('title','')[:60]}' "
                    f"has source='{source}' but no position with that id "
                    f"exists. Available: {sorted(raw_parents)}",
                    file=sys.stderr,
                )
            else:
                # Labels follow the parent's kind: a lab position, a
                # research project, or a degree programme.
                sec = parent.get("_section")
                lab_label = {"experience": "Laboratory", "research": "Project",
                             "education": "Institution"}.get(sec, "Laboratory")
                role_label = {"experience": "Employment", "research": "Position",
                              "education": "Programme"}.get(sec, "Employment")
                if parent.get("advisor"):
                    meta_rows.append(("Supervisor",
                        linkify_names_html(_md_to_html(parent["advisor"]))))
                lab = parent.get("company") or parent.get("institution")
                if lab:
                    lab_html = _md_to_html(lab)
                    # No inline markdown link: fall back to the lab /
                    # project page, mirroring the CV renderer.
                    if "](" not in lab and parent.get("logo_link"):
                        lab_html = (
                            f'<a href="{esc(parent["logo_link"])}" target="_blank" '
                            f'rel="noopener noreferrer">{lab_html}</a>')
                    meta_rows.append((lab_label, lab_html))
                role = parent.get("position") or parent.get("degree")
                if role:
                    span = f'{format_date(parent.get("start_date"), short=True, day=False)} - '                            f'{format_date(parent.get("end_date"), short=True, day=False)}'
                    meta_rows.append((role_label, f"{esc(role)}, {esc(span)}"))
        events.append({
            "date": paper.get("date"), "type": "publication",
            "title": paper.get("title", ""),
            "authors": paper.get("authors", ""),
            "subtitle": paper.get("venue_short") or paper.get("venue", ""),
            "links": paper.get("links"),
            "awards": paper.get("awards"),
            "meta_rows": meta_rows,
            "pos_id": source if source in raw_parents else None,
            "pos_color": pos_colors.get(source),
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

    # Everything on the timeline is atomic now; ranges survive only as
    # the degree cards on the right. All atomic cards (papers, news
    # moments) share the wide left column.
    card_events = events

    for e in card_events:
        if e.get("pos_id") and not e.get("pos_color"):
            e["pos_color"] = pos_colors.get(e["pos_id"])

    left, right = [], []
    for e in card_events:
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

    # The left side is type-banded: employment hugs the axis (lane 0
    # upward), everything else (research, orphan pubs, awards) sits in
    # the lanes further out. Overlapping employment spans still fan out
    # into their own sub-lanes before the rest begin.
    # One wide lane for the publication cards; the per-lane post-pass
    # stacks same-year papers vertically.
    for e in left:
        e["_lane"] = 0
    n_left = 1
    # Right side is a single column: degree cards and education news
    # stack; the per-lane post-pass resolves any vertical overlap.
    for e in right:
        e["_lane"] = 0
    n_right = 1 if right else 1

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
        return False  # publications are primary cards now, never slim

        return e["type"] == "publication"

    columns = (
        [(g, False) for g in left_lane_groups.values()]
        + [(g, False) for g in right_lane_groups.values()]
    )

    # ---- ASYNC AXIS LAYOUT -------------------------------------------
    # The axis is monotone in time but deliberately non-linear: busy
    # stretches expand to hold their cards, quiet stretches collapse to
    # a minimum step. Cards anchor at their date on this warped axis;
    # events from the same moment simply stack. No fixed year bands, no
    # dead whitespace, no card drifting into a foreign year.
    GAP = _TIMELINE_GAP_PX
    MIN_STEP = 26        # px between consecutive distinct dates
    MIN_YEAR_SEG = 150   # room for all twelve month labels even in an empty year
    TOP_PAD = 34

    for idx, (col, _) in enumerate(columns):
        for e in col:
            e["_colkey"] = idx
            e["_est_h"] = _estimate_card_height(e, slim=_is_slim(e))

    # ---- CALENDAR-BLOCK LAYOUT ---------------------------------------
    # Years are blocks, newest first. Inside a block the year pill is
    # the header and the months run Jan -> Dec downwards, each month a
    # header with its cards beneath it (earliest day first). Busy
    # months stretch, empty months collapse to MIN_MONTH.
    GAP = _TIMELINE_GAP_PX
    MIN_MONTH = 16
    YEAR_GAP = 20    # minimum distance between a year pill and a month
    TOP_PAD = 34
    DOT_LIFT = 25   # dot centre sits this far below a card's top edge

    for idx, (col, _) in enumerate(columns):
        for e in col:
            e["_colkey"] = idx
            e["_est_h"] = _estimate_card_height(e, slim=_is_slim(e))

    # Year range covers cards AND position spans (for the bars).
    span_dates = []
    for item in raw_parents.values():
        for key in ("start_date", "end_date"):
            f = _date_frac(item.get(key))
            if f is not None:
                span_dates.append(f)
    all_fracs = [e["_end"] for e in card_events] + span_dates
    yr_max = int(max(all_fracs))
    yr_min = int(min(all_fracs))

    # Events keyed by (year, month), day-sorted ascending.
    from collections import defaultdict as _dd2
    by_month = _dd2(list)
    for e in card_events:
        Y = int(e["_end"])
        M = int((e["_end"] - Y) * 12 + 1e-6) + 1
        M = min(max(M, 1), 12)
        by_month[(Y, M)].append(e)
    for g in by_month.values():
        g.sort(key=lambda e: e["_end"], reverse=True)  # later days first

    lane_cursor = {}
    year_label_y = {}
    month_header_y = {}
    cursor = 0.0

    def _needs(events):
        """Lowest rail line on which every one of `events` would still sit
        exactly on the line, clearing whatever its own column already holds.
        Empty months ask for nothing and stay collapsed."""
        if not events:
            return -1e9
        return max(lane_cursor.get(e.get("_colkey"), -1e9) + GAP + DOT_LIFT
                   for e in events)

    def _place(line, events):
        """Anchor a month's cards on its rail line. The line has already
        cleared the columns these cards belong to, so the first card of
        each column lands on it; further cards of the same month and
        column stack underneath. Returns the lowest dot it placed, which
        the next month's line has to clear - otherwise a January dot ends
        up level with the November label."""
        col_next = {}
        last = -1e9
        for e in events:
            ck = e.get("_colkey")
            y = max(col_next.get(ck, line), lane_cursor.get(ck, -1e9) + GAP)
            e["_top_px"] = y - DOT_LIFT
            lane_cursor[ck] = e["_top_px"] + e["_est_h"]
            col_next[ck] = y + MIN_MONTH
            last = max(last, y)
        return last

    # Newest year on top. Each pill heads its own year; beneath it the
    # months run Dec -> Jan, so time descends the page without a break.
    # Quiet months collapse to MIN_MONTH; a month whose cards need room
    # pushes its own line down, which keeps every card on its date.
    carry = -1e9      # lowest dot of the block above, which Dec must clear
    for Y in range(yr_max, yr_min - 1, -1):
        cursor = max(cursor, TOP_PAD - 34)
        # The pill above a block is the BOUNDARY: start of year Y+1,
        # end of year Y - months below it belong to year Y.
        year_label_y[Y + 1] = cursor
        prev = max(cursor + YEAR_GAP - MIN_MONTH, carry)  # Dec: YEAR_GAP below
        for M in range(12, 1, -1):
            evs = by_month.get((Y, M), [])
            line = max(prev + MIN_MONTH, _needs(evs))
            month_header_y[(Y, M)] = line
            prev = max(line, _place(line, evs))
        # January owns no label of its own: its line IS the year pill.
        evs = by_month.get((Y, 1), [])
        jan_y = max(prev + YEAR_GAP, _needs(evs))
        month_header_y[(Y, 1)] = jan_y
        last = _place(jan_y, evs)
        cursor = jan_y
        carry = max(jan_y, last)
    year_label_y[yr_min] = cursor  # closing boundary sits on the last Jan line
    cursor += 8
    order = card_events
    bottom = max((e["_top_px"] + e["_est_h"] for e in order), default=TOP_PAD)
    total_h = int(max(bottom, cursor) + 40)

    def _y_at_date(d):
        """Date -> y inside its own year block (piecewise per month)."""
        Y = int(d)
        M = int((d - Y) * 12 + 1e-6) + 1
        M = min(max(M, 1), 12)
        top = month_header_y.get((Y, M))
        if top is None:
            return None
        nxt = month_header_y.get((Y, M - 1)) if M > 1 else \
            (year_label_y.get(Y, total_h))
        # A date maps onto its month LABEL line; day-level dates slip a
        # few px below it on the NOMINAL month scale, so a stretched
        # month never turns days into centimetres.
        frac_in_month = (d - Y) * 12 - (M - 1)
        span = max((nxt or top + MIN_MONTH) - top, 0)
        return top + min(frac_in_month * MIN_MONTH, span - 2 if span > 2 else span)

    # Render newest end first so DOM order matches visual stacking
    # (also what the responsive single-column collapse reads top-to-bottom).
    card_events.sort(key=lambda e: e["_end"] or 0, reverse=True)

    # Type-filter chips. Only show chips for types actually present.
    present_types = {e["type"] for e in card_events}
    chips = ['<button class="timeline-filter active" data-tl-type="">All</button>']
    for type_key, label in _TL_FILTER_ORDER:
        if type_key in present_types:
            chips.append(
                f'<button class="timeline-filter" data-tl-type="{type_key}">{label}</button>'
            )
    controls = (
        f'<div class="timeline-controls">{"".join(chips)}</div>'
        if len(chips) > 1 else ""
    )

    # Emit the per-build lane counts so the CSS computes one uniform
    # --lane-w across all sub-columns (no left-vs-right width asymmetry).
    # The publication column carries nearly all the content, the degree
    # column only slim lines: weight the left side heavier so the rail
    # sits right of centre instead of splitting the width evenly.
    left_w = n_left * 1.25
    n_total = left_w + n_right
    total_recip = 1.0 / max(1, n_total)
    timeline_style = (
        f"height: {total_h:.0f}px; "
        f"--n-left: {left_w:.2f}; --n-right: {n_right}; "
        f"--n-total: {n_total:.2f}; --total-recip: {total_recip:.6f};"
    )
    parts = [f'<div class="timeline" style="{timeline_style}">']
    # Month ticks on the rail (small dashes between consecutive year
    # labels). The band per year is variable, so each tick is placed at
    # the m/12 fraction of its year's band height.
    # Month headers: Jan sits directly under its year pill, Dec last.
    month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May",
                   6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct",
                   11: "Nov", 12: "Dec"}
    for (Y, M), ty in month_header_y.items():
        if M != 1:
            parts.append(
                f'<div class="timeline-month-tick" style="top: {ty:.1f}px"></div>')
        if M == 1:
            continue  # January's line IS the year pill: no tick, no label
        parts.append(
            f'<div id="{Y}-{M:02d}" class="timeline-month-label" style="top: {ty:.1f}px">'
            f'{month_names[M]}</div>')

    for y, y_pos in year_label_y.items():
        parts.append(
            f'<div id="{y}" class="timeline-year-label" style="top: {y_pos:.1f}px">{y}</div>'
        )

    # Position bars: one thin vertical bar per employment / research
    # span, colour-matched to that position's publications, fanned out
    # on the left flank of the rail. Hovering a publication lights up
    # its bar and vice versa (initTimelinePosHover).
    # ---- PERIOD CARDS RIDE THEIR BAR ---------------------------------
    # A position or a degree is not a point in time: the rail already
    # carries its coloured bar, so the card is free to sit anywhere
    # beside that bar. Each one slides to the first free stretch of its
    # own span, which keeps it out of crowded months like January 2025.
    # A card stops at the next period's tip: past that it would sit below
    # something that ended earlier, which reads as the wrong order.
    periods = sorted((e for e in card_events if e["_end"] > e["_start"]),
                     key=lambda e: e["_end"], reverse=True)
    for i, e in enumerate(periods):
        top, bot = _y_at_date(e["_end"]), _y_at_date(e["_start"])
        if top is None or bot is None:
            continue
        if i + 1 < len(periods):
            bot = min(bot, _y_at_date(periods[i + 1]["_end"]) or bot)
        h, ck = e["_est_h"], e.get("_colkey")
        # Work in card-top coordinates: the arm sits DOT_LIFT below the
        # card's top edge, and it has to land on the bar's own tip, which
        # carries the day (Jul 17), not just the month line.
        y = top - DOT_LIFT
        for b0, b1 in sorted((o["_top_px"], o["_top_px"] + o["_est_h"])
                             for o in card_events
                             if o is not e and o.get("_colkey") == ck):
            if b1 <= y or b0 - GAP - y >= h:
                continue          # neighbour is above, or the card fits here
            y = b1 + GAP
        if y + DOT_LIFT <= bot:
            e["_top_px"] = y

    # Position bars, split per year block so each segment lies exactly
    # over the months it covers inside that block.
    spans = []
    for pid, item in raw_parents.items():
        sfrac = _date_frac(item.get("start_date"))
        efrac = _date_frac(item.get("end_date")) or sfrac
        if sfrac is None:
            continue
        spans.append({"_start": sfrac, "_end": efrac, "_pid": pid, "_item": item})
    # Greedy interval colouring: non-overlapping spans share the lane
    # nearest the rail, so the bars sit snugly side by side.
    bar_offsets = {}   # position id -> px the bar is fanned off the rail
    bar_tops = {}      # position id -> y of the bar's tip (its end date)
    spans.sort(key=lambda sp: sp["_end"], reverse=True)
    lane_free = []  # per lane: the start (oldest frac) of its last bar
    for sp in spans:
        for li in range(len(lane_free)):
            # Spans that merely touch within the same month (defend the
            # thesis Jan 10, start the internship that January) still
            # share a lane; only real overlaps fan outwards.
            if lane_free[li] >= sp["_end"] - 1.0 / 12:
                sp["_lane"] = li
                lane_free[li] = sp["_start"]
                break
        else:
            sp["_lane"] = len(lane_free)
            lane_free.append(sp["_start"])
    for sp in spans:
        item = sp["_item"]
        role = item.get("position") or item.get("degree", "")
        dates = f'{format_date(item.get("start_date"), short=True, day=False)} - '                 f'{format_date(item.get("end_date"), short=True, day=False)}'
        who = _md_strip(item.get("company") or item.get("institution", ""))
        tip = esc(f'{who} - {role} ({dates})')
        offset = 14 + sp["_lane"] * 7
        bar_offsets[sp["_pid"]] = offset
        color = pos_colors.get(sp["_pid"], "#6c71c4")
        # Exact endpoints: each tip at its date's own coordinate, nudged
        # 4px off the boundary line so it reads inside its month.
        y0 = _y_at_date(sp["_end"])
        y1 = _y_at_date(sp["_start"])
        if y0 is None or y1 is None:
            continue
        top, hgt = min(y0, y1), abs(y1 - y0)
        bar_tops[sp["_pid"]] = top
        parts.append(
            f'<div class="tl-posbar timeline-{ {"experience": "experience", "research": "research", "education": "degree"}[item["_section"]] }" '
            f'data-pos="{esc(sp["_pid"])}" title="{tip}" '
            f'style="top: {top:.1f}px; height: {max(hgt, 8):.1f}px; '
            f'left: calc(var(--rail-x) + {offset}px); --dot-color: {color};"></div>')

    for e in card_events:
        side, color = _TIMELINE_TYPE_META.get(e["type"], ("right", ""))
        top_px = e["_top_px"]
        n_lanes = n_left if side == "left" else n_right
        slim = _is_slim(e)
        # est_h only spaces siblings during layout; the rendered card
        # keeps its natural CSS height, so an over-estimate leaves air
        # between cards, never dead space inside one.
        height_px = None
        parts.append(_render_timeline_card(
            e, top_px, height_px, lane=e.get("_lane", 0), lanes=n_lanes,
            slim=slim, bar_off=bar_offsets.get(e.get("pos_id")),
            bar_top=bar_tops.get(e.get("pos_id")),
        ))

    parts.append('</div>')
    return controls + "\n".join(parts)


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
    blogs = sorted(blogs, key=lambda b: parse_date(str(b.get("date", ""))), reverse=True)
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
        # Fold the post's full text into the search haystack: unique
        # words from the generated page, so the search box reaches the
        # article bodies, not just the ten listing lines.
        page = BASE_DIR / blog.get("path", "")
        if page.is_file():
            body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ",
                          page.read_text(errors="ignore"), flags=re.S)
            body = re.sub(r"<[^>]+>", " ", body)
            words = sorted(set(re.findall(r"[a-z0-9][a-z0-9'-]{2,}", body.lower())))
            search += " " + " ".join(words)

        # One plain bullet per post: "18 Mar 2020: Title #tag #tag",
        # title links to the post page, #tags drive the filter above.
        # Filter/search metadata rides on the <li>.
        inline_tags = " ".join(
            f'<a href="#" class="blog-tag-inline" data-tag="{esc(t)}">#{esc(t)}</a>'
            for t in own_tags
        )
        parts.append(
            f'<li class="blog-item" data-tags="{esc(data_tags)}" data-search="{esc(search)}">'
            f'<span class="blog-date">{esc(format_date(blog.get("date", ""), short=True))}</span>'
            f': <a href="{esc(blog["path"])}" class="blog-link">{esc(blog["title"])}</a>'
            f' {inline_tags}</li>'
        )
    return "\n".join(parts)


# tech tag -> (brand colour, Devicon class). Tags not listed render as plain chips.
_TECH_BADGES = {
    "python": ("#3776AB", "devicon-python-plain"),
    "pytorch": ("#EE4C2C", "devicon-pytorch-plain"),
    "tensorflow": ("#FF6F00", "devicon-tensorflow-original"),
    "jax": ("#5E97F6", "devicon-python-plain"),
    "c++": ("#00599C", "devicon-cplusplus-plain"),
    "docker": ("#2496ED", "devicon-docker-plain"),
    "apptainer": ("#0F4C81", "svg:assets/img/badges/apptainer.svg"),
    "singularity": ("#0F4C81", "svg:assets/img/badges/apptainer.svg"),
    "numpy": ("#013243", "devicon-numpy-plain"),
    # No fitting glyph in the self-hosted subsets -> icon-less badge
    "rust": ("#B7410E", "devicon-rust-plain"),
    "ros": ("#22314E", None),
    "ros2": ("#22314E", None),
    "rabbitmq": ("#FF6600", "devicon-rabbitmq-original"),
    "redis": ("#DC382D", "devicon-redis-plain"),
    # Marks missing from the icon fonts ship as inline SVG files
    "pydantic": ("#E92063", "svg:assets/img/badges/pydantic.svg"),
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
            if icon and icon.startswith("svg:"):
                from .build_config import BASE_DIR
                icon_html = (BASE_DIR / icon[4:]).read_text().strip()
            elif icon:
                icon_html = f'<i class="{icon}" aria-hidden="true"></i>'
            else:
                icon_html = ""
            out.append(
                f'<span class="tech-badge" style="background:{color}">'
                f'{icon_html}{esc(tag)}</span>'
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
        "worksFor": {"@type": "Organization", "name": primary_affiliation(bio)},
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
        (f"{site_url}/?tab=cv", today, "0.9"),
        (f"{site_url}/?tab=blogs", today, "0.8"),
        (f"{site_url}/?tab=timeline", today, "0.7"),
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


def generate_rss(bio, blogs_data):
    """Generate an RSS 2.0 feed (feed.xml) of the blog posts."""
    from datetime import datetime, timezone

    site_url = bio.get("site_url", "https://adnanhd.github.io").rstrip("/")
    name = bio.get("name", "")
    desc = bio.get("meta_description") or f"Blog posts by {name}."

    def rfc822(dt):
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

    blogs = [b for b in (blogs_data or {}).get("blogs", []) if b.get("path")]
    blogs = sorted(blogs, key=lambda b: parse_date(b.get("date", "")), reverse=True)

    items = []
    for blog in blogs:
        link = f"{site_url}/{blog['path']}"
        pub = rfc822(parse_date(blog.get("date", "")))
        cats = "".join(
            f"\n      <category>{esc(t)}</category>" for t in (blog.get("tags") or [])
        )
        items.append(
            "    <item>\n"
            f"      <title>{esc(blog.get('title', ''))}</title>\n"
            f"      <link>{esc(link)}</link>\n"
            f"      <guid isPermaLink=\"true\">{esc(link)}</guid>\n"
            f"      <pubDate>{pub}</pubDate>\n"
            f"      <description>{esc(blog.get('description', ''))}</description>"
            f"{cats}\n"
            "    </item>"
        )

    now = rfc822(datetime.now(timezone.utc))
    body = "\n".join(items)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>{esc(name)} - Blog</title>\n"
        f"    <link>{esc(site_url)}/?tab=blogs</link>\n"
        f"    <description>{esc(desc)}</description>\n"
        "    <language>en-us</language>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        f'    <atom:link href="{esc(site_url)}/feed.xml" rel="self" type="application/rss+xml" />\n'
        f"{body}\n"
        "  </channel>\n"
        "</rss>"
    )

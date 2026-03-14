"""
HTML rendering functions for the static site.

Each function takes data (dicts loaded from YAML) and returns an HTML string.
"""

import json
import re

from build_config import (
    LINK_ICONS,
    LINK_NAMES,
    PRIMARY_LINKS,
    SECONDARY_CATEGORIES,
    URL_TEMPLATES,
)
from build_utils import esc, highlight_author, highlight_author_span, parse_date


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
    """Render a fancy publication card (About page — selected works)."""
    parts = ['<div class="publication-item">']

    # Left: venue tag + image
    parts.append('<div class="publication-left">')
    venue_text = paper.get("venue_short") or paper.get("venue", "Publication")
    if paper.get("venue_link"):
        parts.append(
            f'<div class="publication-venue-tag">'
            f'<a href="{esc(paper["venue_link"])}" target="_blank" rel="noopener noreferrer" '
            f'style="color: inherit; text-decoration: none;">{esc(venue_text)}</a></div>'
        )
    else:
        parts.append(f'<div class="publication-venue-tag">{esc(venue_text)}</div>')

    if paper.get("image"):
        parts.append(
            f'<div class="publication-image">'
            f'<img src="{esc(paper["image"])}" alt="{esc(paper["title"])}" loading="lazy" /></div>'
        )
    parts.append("</div>")

    # Right: title, authors, venue, links
    parts.append('<div class="publication-content">')
    parts.append(f'<div class="publication-title">{esc(paper["title"])}</div>')
    parts.append(f'<div class="publication-authors">{highlight_author_span(esc(paper.get("authors", "")))}</div>')

    venue_full = paper.get("venue", "")
    if paper.get("date"):
        venue_full += f', {paper["date"]}'
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
        citation += f" ({esc(str(paper['date']))})."
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
    return f'{item.get("start_date", "")} - {item.get("end_date", "")}'


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
    return _render_section(items, "title", "organization", lambda e: e.get("date", ""))


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

_NEWS_TAG_COLORS = {
    "publication": "#2563eb",
    "degree": "#7c3aed",
    "internship": "#0891b2",
    "award": "#d97706",
}


def _year_from_date(date_str):
    """Extract the 4-digit year from a date string."""
    m = re.search(r"\d{4}", str(date_str))
    return int(m.group()) if m else 0


def _year_opacity(year, min_year, max_year):
    """Map a year to an opacity value (newer = more opaque)."""
    if max_year == min_year:
        return 1.0
    return 0.45 + 0.55 * (year - min_year) / (max_year - min_year)


def render_news(data):
    """Render news items as one-line list items with tags and year shading."""
    items = (data.get("news") or {}).get("items", [])
    if not items:
        return ""

    years = [_year_from_date(item["date"]) for item in items]
    min_year, max_year = min(years), max(years)

    parts = []
    for item, year in zip(items, years):
        opacity = _year_opacity(year, min_year, max_year)
        date = (
            f'<span class="news-date" style="opacity: {opacity:.2f}">'
            f'[{esc(item["date"])}]</span> '
        )

        content = f'<span class="news-content">{esc(item["content"])}</span>'
        if item.get("link"):
            content += (
                f' <a href="{esc(item["link"])}" class="news-link" '
                f'target="_blank" rel="noopener noreferrer">[link]</a>'
            )

        tag_html = ""
        tags = item.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if tags:
            tag_spans = "".join(
                f'<span class="news-tag" style="background-color: '
                f'{_NEWS_TAG_COLORS.get(tag, "var(--text-muted)")}">{esc(tag)}</span>'
                for tag in tags
            )
            tag_html = f'<span class="news-tags">{tag_spans}</span>'

        parts.append(f"<li>{date}{content}{tag_html}</li>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

def render_timeline(data):
    """Render the unified timeline from education, experience, research, and publications."""
    events = []

    # Collect timelined events from each source
    for edu in (data.get("education") or {}).get("education", []):
        if edu.get("timelined"):
            events.append({
                "date": edu["start_date"], "type": "experience",
                "title": edu["degree"], "organization": edu["institution"],
                "end_date": edu.get("end_date"),
            })

    for exp in (data.get("experience") or {}).get("experience", []):
        if exp.get("timelined"):
            events.append({
                "date": exp["start_date"], "type": "experience",
                "title": exp["position"], "organization": exp["company"],
                "end_date": exp.get("end_date"),
            })

    for res in (data.get("research") or {}).get("research", []):
        if res.get("timelined"):
            events.append({
                "date": res["start_date"], "type": "experience",
                "title": res["position"], "organization": res["company"],
                "end_date": res.get("end_date"),
            })

    for paper in (data.get("publications") or {}).get("papers", []):
        if paper.get("timelined"):
            events.append({
                "date": paper["date"], "type": "publication",
                "title": paper["title"],
                "authors": paper.get("authors", ""),
                "venue": paper.get("venue_short") or paper.get("venue", ""),
                "links": paper.get("links"),
            })

    events.sort(key=lambda e: parse_date(e["date"]), reverse=True)
    if not events:
        return ""

    parts = ['<div class="unified-timeline">']
    for event in events:
        parts.append(f'<div class="timeline-row timeline-{event["type"]}">')

        # Date column
        date_html = esc(str(event["date"]))
        if event.get("end_date"):
            date_html += f"<br>{esc(str(event['end_date']))}"
        parts.append(f'<div class="timeline-left"><div class="timeline-date">{date_html}</div></div>')

        # Marker
        parts.append('<div class="timeline-center"><div class="timeline-marker"></div></div>')

        # Content
        parts.append('<div class="timeline-right"><div class="timeline-content-box">')
        parts.append(f"<h4>{esc(event['title'])}</h4>")

        if event["type"] == "experience":
            parts.append(f'<div class="timeline-org">{esc(event.get("organization", ""))}</div>')
        else:
            parts.append(f'<div class="timeline-authors">{esc(event.get("authors", ""))}</div>')
            parts.append(f'<div class="timeline-venue"><em>{esc(event.get("venue", ""))}</em></div>')
            if event.get("links"):
                link_html = "\n".join(
                    f'<a href="{esc(l["url"])}" target="_blank" rel="noopener noreferrer" '
                    f'class="timeline-link">{esc(l["name"])}</a>'
                    for l in event["links"]
                )
                parts.append(f'<div class="timeline-links">{link_html}</div>')

        parts.append("</div></div></div>")

    parts.append("</div>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Blogs and Works
# ---------------------------------------------------------------------------

def render_blogs(blogs_data, selected_only=False):
    """Render blog post listings."""
    blogs = (blogs_data or {}).get("blogs", [])
    if selected_only:
        blogs = [b for b in blogs if b.get("selected")]

    if not blogs:
        msg = "No selected blogs yet." if selected_only else "No blog posts yet. Check back soon!"
        return f'<p style="color: var(--text-secondary);">{msg}</p>'

    parts = []
    for blog in blogs:
        desc = f"<p>{esc(blog['description'])}</p>" if blog.get("description") else ""
        parts.append(
            f'<div class="blog-item"><a href="{esc(blog["path"])}" class="blog-link">'
            f'<h3>{esc(blog["title"])}</h3>'
            f'<span class="blog-date">{esc(blog.get("date", ""))}</span>'
            f'{desc}</a></div>'
        )
    return "\n".join(parts)


def render_works(works_data):
    """Render open source project listings."""
    works = (works_data or {}).get("works", [])
    if not works:
        return '<p style="color: var(--text-secondary);">No selected works yet.</p>'

    parts = []
    for work in works:
        desc = f"<p>{esc(work['description'])}</p>" if work.get("description") else ""
        tags = ""
        if work.get("tags"):
            tag_spans = "".join(f'<span class="work-tag">{esc(t)}</span>' for t in work["tags"])
            tags = f'<div class="work-tags">{tag_spans}</div>'
        parts.append(
            f'<div class="work-item">'
            f'<a href="{esc(work["url"])}" target="_blank" rel="noopener noreferrer" class="work-link">'
            f'<h3>{esc(work["title"])}</h3>{desc}{tags}</a></div>'
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
        (f"{site_url}/#timeline", today, "0.7"),
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

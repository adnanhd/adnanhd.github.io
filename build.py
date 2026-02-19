#!/usr/bin/env python3
"""
Static site builder for personal academic website.

Reads YAML data files and template.html, produces a fully rendered index.html.

Usage:
    python build.py
"""

import re
from datetime import datetime
from html import escape
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_PATH = BASE_DIR / "template.html"
OUTPUT_PATH = BASE_DIR / "index.html"

AUTHOR_NAME = "Adnan Harun Dogan"
AUTHOR_NAME_ALT = "Adnan Harun Doğan"

URL_TEMPLATES = {
    "email": "mailto:{id}",
    "github": "https://github.com/{id}",
    "linkedin": "https://linkedin.com/in/{id}",
    "google_scholar": "https://scholar.google.com/citations?user={id}",
    "twitter": "https://twitter.com/{id}",
    "orcid": "https://orcid.org/{id}",
    "acm": "https://dl.acm.org/profile/{id}",
    "ieee": "https://ieeexplore.ieee.org/author/{id}",
    "dblp": "https://dblp.org/pid/{id}",
    "semantic_scholar": "https://www.semanticscholar.org/author/{id}",
}

LINK_NAMES = {
    "email": "Email",
    "github": "GitHub",
    "linkedin": "LinkedIn",
    "google_scholar": "Google Scholar",
    "twitter": "Twitter",
    "orcid": "ORCID",
    "acm": "ACM DL",
    "ieee": "IEEE Xplore",
    "dblp": "DBLP",
    "semantic_scholar": "Semantic Scholar",
}

LINK_ICONS = {
    "email": "fas fa-envelope",
    "github": "fab fa-github",
    "linkedin": "fab fa-linkedin",
    "google_scholar": "ai ai-google-scholar",
    "twitter": "fab fa-twitter",
    "orcid": "ai ai-orcid",
    "acm": "ai ai-acm",
    "ieee": "ai ai-ieee",
    "dblp": "ai ai-dblp",
    "semantic_scholar": "ai ai-semantic-scholar",
}


def esc(s):
    """HTML-escape a string."""
    if not s:
        return ""
    return escape(str(s))


def highlight_author(text):
    """Bold the author's name in a text string. Input should already be escaped."""
    return re.sub(
        re.escape(esc(AUTHOR_NAME)) + "|" + re.escape(esc(AUTHOR_NAME_ALT)),
        f"<strong>{esc(AUTHOR_NAME)}</strong>",
        text,
    )


def highlight_author_span(text):
    """Wrap author name in span.author-me. Input should already be escaped."""
    return re.sub(
        re.escape(esc(AUTHOR_NAME)) + "|" + re.escape(esc(AUTHOR_NAME_ALT)),
        f'<span class="author-me">{esc(AUTHOR_NAME)}</span>',
        text,
    )


def parse_date(date_str):
    """Parse a date string into a datetime for sorting."""
    if not date_str:
        return datetime(1970, 1, 1)
    s = str(date_str).strip()
    if s.lower() == "present":
        return datetime.now()

    months = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
        "January": 1, "February": 2, "March": 3, "April": 4,
        "June": 6, "July": 7, "August": 8, "September": 9,
        "October": 10, "November": 11, "December": 12,
        "Spring": 3, "Fall": 9,
    }

    m = re.match(r"^([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        month = months.get(m.group(1), 1)
        return datetime(int(m.group(2)), month, 1)

    m = re.match(r"^(\d{4})$", s)
    if m:
        return datetime(int(m.group(1)), 1, 1)

    # Try "DD Mon YYYY" or similar
    try:
        return datetime.strptime(s, "%d %b %Y")
    except ValueError:
        pass
    try:
        return datetime.strptime(s, "%d %B %Y")
    except ValueError:
        pass

    return datetime(1970, 1, 1)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data():
    """Load all YAML data files."""
    data = {}
    for name in [
        "bio", "education", "teaching", "experience",
        "research", "extracurricular", "news", "publications",
        "blogs", "works",
    ]:
        path = DATA_DIR / f"{name}.yaml"
        with open(path) as f:
            data[name] = yaml.safe_load(f)
    return data


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def render_sidebar(bio):
    """Render the sidebar: profile image, name, title, affiliation, short bio, links."""
    parts = []

    # Profile image
    parts.append(f'<div class="bio-image">')
    parts.append(f'  <img src="{esc(bio["profile_image"])}" alt="{esc(bio["name"])}" />')
    parts.append(f"</div>")

    # Name, title, affiliation
    parts.append(f'<h1 class="sidebar-name">{esc(bio["name"])}</h1>')
    parts.append(f'<p class="sidebar-title">{esc(bio.get("title", ""))}</p>')
    parts.append(f'<p class="sidebar-affiliation">{esc(bio.get("affiliation", ""))}</p>')

    # Short bio
    if bio.get("short_bio"):
        parts.append(f'<p class="bio-short">{esc(bio["short_bio"])}</p>')

    # Links
    parts.append('<div class="links">')

    # Social links
    if bio.get("social"):
        for platform, uid in bio["social"].items():
            if uid and str(uid).strip() and platform in URL_TEMPLATES:
                url = URL_TEMPLATES[platform].format(id=esc(uid))
                icon_class = LINK_ICONS.get(platform, "")
                label = LINK_NAMES.get(platform, platform)
                target = "" if platform == "email" else ' target="_blank"'
                parts.append(
                    f'<a href="{url}" class="social-link" title="{esc(label)}" '
                    f'aria-label="{esc(label)}"{target}>'
                    f'<i class="{icon_class}"></i>'
                    f'<span class="social-label">{esc(label)}</span></a>'
                )

    # Custom links
    if bio.get("custom_links"):
        for link in bio["custom_links"]:
            target = ' target="_blank"' if link["url"].startswith("http") else ""
            parts.append(f'<a href="{esc(link["url"])}"{target}>{esc(link["name"])}</a>')

    parts.append("</div>")
    return "\n".join(parts)


def render_bio(bio):
    """Render the About Me bio paragraphs. Bio text may contain HTML links."""
    paragraphs = bio.get("bio", "").split("\n\n")
    parts = []
    for para in paragraphs:
        text = para.strip()
        if text:
            # Bio text is trusted (author-controlled) and contains <a> tags
            parts.append(f"<p>{text}</p>")
    return "\n".join(parts)


def render_pub_links(links):
    """Render publication link buttons."""
    if not links:
        return ""
    parts = ['<div class="publication-links">']
    for link in links:
        parts.append(
            f'<a href="{esc(link["url"])}" class="pub-link" target="_blank">'
            f'{esc(link["name"])}</a>'
        )
    parts.append("</div>")
    return "\n".join(parts)


def render_publication_card(paper):
    """Render a fancy publication card (for About page selected works)."""
    parts = ['<div class="publication-item">']

    # Left side: venue tag + image
    parts.append('<div class="publication-left">')
    venue_text = paper.get("venue_short") or paper.get("venue", "Publication")
    if paper.get("venue_link"):
        parts.append(
            f'<div class="publication-venue-tag">'
            f'<a href="{esc(paper["venue_link"])}" target="_blank" '
            f'style="color: inherit; text-decoration: none;">{esc(venue_text)}</a></div>'
        )
    else:
        parts.append(f'<div class="publication-venue-tag">{esc(venue_text)}</div>')

    if paper.get("image"):
        parts.append(
            f'<div class="publication-image">'
            f'<img src="{esc(paper["image"])}" alt="{esc(paper["title"])}" /></div>'
        )
    parts.append("</div>")

    # Right side: title, authors, venue, links
    parts.append('<div class="publication-content">')
    parts.append(f'<div class="publication-title">{esc(paper["title"])}</div>')

    authors_html = highlight_author_span(esc(paper.get("authors", "")))
    parts.append(f'<div class="publication-authors">{authors_html}</div>')

    venue_full = paper.get("venue", "")
    if paper.get("date"):
        venue_full += f', {paper["date"]}'
    parts.append(f'<div class="publication-venue">{esc(venue_full)}</div>')

    parts.append(render_pub_links(paper.get("links")))
    parts.append("</div>")
    parts.append("</div>")
    return "\n".join(parts)


def render_compact_publication(paper):
    """Render a compact APA-style publication card (for Resume page)."""
    parts = ['<div class="publication-item-compact">']

    # APA citation
    authors_html = highlight_author(esc(paper.get("authors", "")))
    citation = authors_html
    if paper.get("date"):
        citation += f" ({esc(str(paper['date']))})."
    citation += f" {esc(paper['title'])}."
    if paper.get("venue_link") and paper.get("venue_short"):
        citation += (
            f' <em><a href="{esc(paper["venue_link"])}" target="_blank" '
            f'style="color: var(--accent-color); text-decoration: none;">'
            f'{esc(paper["venue_short"])}</a></em>.'
        )
    elif paper.get("venue"):
        citation += f" <em>{esc(paper['venue'])}</em>."

    parts.append(f'<div class="pub-compact-reference">{citation}</div>')

    # Links
    if paper.get("links"):
        parts.append('<div class="publication-links">')
        for link in paper["links"]:
            parts.append(
                f'<a href="{esc(link["url"])}" class="pub-link" target="_blank">'
                f'{esc(link["name"])}</a>'
            )
        parts.append("</div>")

    parts.append("</div>")
    return "\n".join(parts)


def render_resume_item(title, subtitle, date, description, logo=None,
                       links=None, logo_link=None, commitment=None,
                       advisor=None, bullets=None):
    """Render a single resume entry."""
    parts = ['<div class="resume-item">']

    # Logo
    if logo:
        parts.append('<div class="resume-logo">')
        if logo_link:
            parts.append(f'<a href="{esc(logo_link)}" target="_blank">')
            parts.append(f'<img src="{esc(logo)}" alt="{esc(subtitle)}" />')
            parts.append("</a>")
        else:
            parts.append(f'<img src="{esc(logo)}" alt="{esc(subtitle)}" />')
        parts.append("</div>")

    # Details
    parts.append('<div class="resume-details">')

    # Header: title + date
    parts.append('<div class="resume-header">')
    parts.append(f"<strong>{esc(title)}</strong>")
    parts.append(f'<span class="date">{esc(date)}</span>')
    parts.append("</div>")

    # Subheader: subtitle + commitment
    parts.append('<div class="resume-subheader">')
    parts.append(f"<span>{esc(subtitle)}</span>")
    if commitment and str(commitment).strip():
        parts.append(f'<span class="resume-commitment">{esc(commitment)}</span>')
    parts.append("</div>")

    # Advisor
    if advisor and str(advisor).strip():
        parts.append(
            f'<div class="resume-advisor"><strong>Advisor:</strong> {esc(advisor)}</div>'
        )

    # Description
    if description:
        parts.append(f"<p>{esc(description)}</p>")

    # Bullets
    if bullets:
        parts.append('<ul class="resume-bullets">')
        for bullet in bullets:
            course_match = re.match(r"^(CENG \d+)\s*-\s*(.+)$", bullet)
            if course_match:
                code = course_match.group(1)
                name = course_match.group(2)
                number = code.replace("CENG ", "")
                url = f"https://catalog.metu.edu.tr/course.php?course_code=5710{number}"
                parts.append(
                    f'<li><a href="{url}" target="_blank" '
                    f'style="color: var(--accent-color); text-decoration: none;">'
                    f"{esc(code)}</a> - {esc(name)}</li>"
                )
            else:
                parts.append(f"<li>{esc(bullet)}</li>")
        parts.append("</ul>")

    # Links
    parts.append(render_pub_links(links))

    parts.append("</div>")  # resume-details
    parts.append("</div>")  # resume-item
    return "\n".join(parts)


def render_resume_section(items, title_key, subtitle_key, date_fn):
    """Render a list of resume items."""
    parts = []
    for item in items:
        parts.append(render_resume_item(
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
        ))
    return "\n".join(parts)


def render_education(data):
    items = (data.get("education") or {}).get("education", [])
    return render_resume_section(
        items, "degree", "institution",
        lambda e: f'{e.get("start_date", "")} - {e.get("end_date", "")}',
    )


def render_experience(data):
    items = (data.get("experience") or {}).get("experience", [])
    return render_resume_section(
        items, "position", "company",
        lambda e: f'{e.get("start_date", "")} - {e.get("end_date", "")}',
    )


def render_research(data):
    items = (data.get("research") or {}).get("research", [])
    return render_resume_section(
        items, "position", "company",
        lambda e: f'{e.get("start_date", "")} - {e.get("end_date", "")}',
    )


def render_teaching(data):
    items = (data.get("teaching") or {}).get("teaching", [])
    return render_resume_section(
        items, "position", "company",
        lambda e: f'{e.get("start_date", "")} - {e.get("end_date", "")}',
    )


def render_honors(data):
    items = (data.get("extracurricular") or {}).get("honors", [])
    return render_resume_section(
        items, "title", "organization",
        lambda e: e.get("date", ""),
    )


def render_news(data):
    items = (data.get("news") or {}).get("items", [])
    parts = []
    for item in items:
        parts.append("<li>")
        parts.append(f'<span class="news-date">[{esc(item["date"])}]</span> ')
        if item.get("link"):
            parts.append(
                f'<span class="news-content">'
                f'<a href="{esc(item["link"])}" target="_blank">{esc(item["content"])}</a>'
                f"</span>"
            )
        else:
            parts.append(f'<span class="news-content">{esc(item["content"])}</span>')
        parts.append("</li>")
    return "\n".join(parts)


def render_timeline(data):
    """Render the unified timeline from education, experience, research, and publications."""
    events = []

    # Education
    for edu in (data.get("education") or {}).get("education", []):
        if edu.get("timelined"):
            events.append({
                "date": edu["start_date"],
                "type": "experience",
                "title": edu["degree"],
                "organization": edu["institution"],
                "end_date": edu.get("end_date"),
            })

    # Experience
    for exp in (data.get("experience") or {}).get("experience", []):
        if exp.get("timelined"):
            events.append({
                "date": exp["start_date"],
                "type": "experience",
                "title": exp["position"],
                "organization": exp["company"],
                "end_date": exp.get("end_date"),
            })

    # Research
    for res in (data.get("research") or {}).get("research", []):
        if res.get("timelined"):
            events.append({
                "date": res["start_date"],
                "type": "experience",
                "title": res["position"],
                "organization": res["company"],
                "end_date": res.get("end_date"),
            })

    # Publications
    for paper in (data.get("publications") or {}).get("papers", []):
        if paper.get("timelined"):
            events.append({
                "date": paper["date"],
                "type": "publication",
                "title": paper["title"],
                "authors": paper.get("authors", ""),
                "venue": paper.get("venue_short") or paper.get("venue", ""),
                "links": paper.get("links"),
            })

    # Sort newest first
    events.sort(key=lambda e: parse_date(e["date"]), reverse=True)

    if not events:
        return ""

    parts = ['<div class="unified-timeline">']

    for event in events:
        parts.append(f'<div class="timeline-row timeline-{event["type"]}">')

        # Left: date
        parts.append('<div class="timeline-left">')
        date_html = esc(str(event["date"]))
        if event.get("end_date"):
            date_html += f"<br>{esc(str(event['end_date']))}"
        parts.append(f'<div class="timeline-date">{date_html}</div>')
        parts.append("</div>")

        # Center: marker
        parts.append('<div class="timeline-center"><div class="timeline-marker"></div></div>')

        # Right: content
        parts.append('<div class="timeline-right">')
        parts.append('<div class="timeline-content-box">')
        parts.append(f"<h4>{esc(event['title'])}</h4>")

        if event["type"] == "experience":
            parts.append(f'<div class="timeline-org">{esc(event.get("organization", ""))}</div>')
        else:
            parts.append(f'<div class="timeline-authors">{esc(event.get("authors", ""))}</div>')
            parts.append(f'<div class="timeline-venue"><em>{esc(event.get("venue", ""))}</em></div>')
            if event.get("links"):
                parts.append('<div class="timeline-links">')
                for link in event["links"]:
                    parts.append(
                        f'<a href="{esc(link["url"])}" target="_blank" '
                        f'class="timeline-link">{esc(link["name"])}</a>'
                    )
                parts.append("</div>")

        parts.append("</div></div>")  # content-box, timeline-right
        parts.append("</div>")  # timeline-row

    parts.append("</div>")  # unified-timeline
    return "\n".join(parts)


def render_blogs(blogs_data, selected_only=False):
    """Render blog items."""
    blogs = (blogs_data or {}).get("blogs", [])
    if selected_only:
        blogs = [b for b in blogs if b.get("selected")]

    if not blogs:
        msg = "No selected blogs yet." if selected_only else "No blog posts yet. Check back soon!"
        return f'<p style="color: var(--text-secondary);">{msg}</p>'

    parts = []
    for blog in blogs:
        parts.append('<div class="blog-item">')
        parts.append(f'<a href="{esc(blog["path"])}" class="blog-link">')
        parts.append(f"<h3>{esc(blog['title'])}</h3>")
        parts.append(f'<span class="blog-date">{esc(blog.get("date", ""))}</span>')
        if blog.get("description"):
            parts.append(f"<p>{esc(blog['description'])}</p>")
        parts.append("</a></div>")
    return "\n".join(parts)


def render_works(works_data):
    """Render open source works."""
    works = (works_data or {}).get("works", [])
    if not works:
        return '<p style="color: var(--text-secondary);">No selected works yet.</p>'

    parts = []
    for work in works:
        parts.append('<div class="work-item">')
        parts.append(f'<a href="{esc(work["url"])}" target="_blank" class="work-link">')
        parts.append(f"<h3>{esc(work['title'])}</h3>")
        if work.get("description"):
            parts.append(f"<p>{esc(work['description'])}</p>")
        if work.get("tags"):
            parts.append('<div class="work-tags">')
            for tag in work["tags"]:
                parts.append(f'<span class="work-tag">{esc(tag)}</span>')
            parts.append("</div>")
        parts.append("</a></div>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    data = load_data()
    bio = data["bio"]

    # Read template
    template = TEMPLATE_PATH.read_text()

    # Selected publications (About page)
    pubs = (data.get("publications") or {}).get("papers", [])
    selected_pubs = [p for p in pubs if p.get("selected")]
    selected_pubs_html = "\n".join(render_publication_card(p) for p in selected_pubs)

    # Resume papers
    resume_pubs = [p for p in pubs if p.get("resume")]
    resume_pubs_html = "\n".join(render_compact_publication(p) for p in resume_pubs)

    # Meta description
    meta_desc = (
        f'{bio["name"]} - {bio.get("title", "")} at {bio.get("affiliation", "")}. '
        "Research in differentiable optimization and deep learning for computer vision."
    )

    # Perform replacements
    replacements = {
        "{{NAME}}": esc(bio["name"]),
        "{{META_DESCRIPTION}}": esc(meta_desc),
        "{{PROFILE_IMAGE}}": esc(bio.get("profile_image", "profile.jpeg")),
        "{{SIDEBAR}}": render_sidebar(bio),
        "{{BIO}}": render_bio(bio),
        "{{SELECTED_PUBLICATIONS}}": selected_pubs_html,
        "{{RESUME_PAPERS}}": resume_pubs_html,
        "{{SELECTED_BLOGS}}": render_blogs(data["blogs"], selected_only=True),
        "{{ALL_BLOGS}}": render_blogs(data["blogs"], selected_only=False),
        "{{WORKS}}": render_works(data["works"]),
        "{{EDUCATION}}": render_education(data),
        "{{EXPERIENCE}}": render_experience(data),
        "{{RESEARCH}}": render_research(data),
        "{{TEACHING}}": render_teaching(data),
        "{{HONORS}}": render_honors(data),
        "{{NEWS}}": render_news(data),
        "{{TIMELINE}}": render_timeline(data),
    }

    output = template
    for placeholder, html in replacements.items():
        output = output.replace(placeholder, html)

    OUTPUT_PATH.write_text(output)
    print(f"Built {OUTPUT_PATH} ({len(output):,} bytes)")


if __name__ == "__main__":
    main()

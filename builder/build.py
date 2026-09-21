#!/usr/bin/env python3
"""
Static site builder for personal academic website.

Reads YAML data files and template.html, produces:
  - index.html    (rendered static site)
  - sitemap.xml   (SEO sitemap)
  - resume.pdf    (LaTeX-generated resume)
  - cv.pdf        (LaTeX-generated long-form CV)

Usage:
    python -m builder
"""

from .build_config import BASE_DIR, OUTPUT_PATH, TEMPLATE_PATH
from .build_html import (
    _TL_FILTER_ORDER,
    generate_rss,
    generate_sitemap,
    render_bio,
    render_blog_controls,
    render_blogs,
    render_compact_publication,
    render_education,
    render_experience,
    render_honors,
    render_json_ld,
    render_news,
    render_publication_card,
    render_research,
    primary_affiliation,
    render_sidebar,
    render_social_posts,
    render_teaching,
    render_timeline,
    render_works,
)
from .build_projects import generate_project_pages
from .build_cv import build_cv_pdf
from .build_resume import build_resume_pdf
from .build_utils import esc, file_hash, load_data


def main():
    data = load_data()
    bio = data["bio"]

    template = TEMPLATE_PATH.read_text()

    # Publications. In-progress / under-review papers float to the top.
    pubs = (data.get("publications") or {}).get("papers", [])
    pubs = sorted(pubs, key=lambda p: 0 if p.get("status") else 1)
    selected_html = "\n".join(render_publication_card(p) for p in pubs if p.get("selected"))
    resume_html = "\n".join(render_compact_publication(p) for p in pubs if p.get("resume"))

    # Meta
    meta_desc = bio.get("meta_description") or (
        f'{bio["name"]} - {bio.get("title", "")} at {primary_affiliation(bio)}.'
    )
    twitter_id = (bio.get("social") or {}).get("twitter", "")

    # Template replacements
    replacements = {
        "{{CSS_HASH}}": file_hash(BASE_DIR / "assets" / "css" / "style.css"),
        "{{VENDOR_HASH}}": file_hash(BASE_DIR / "assets" / "css" / "vendor.css"),
        "{{JS_HASH}}": file_hash(BASE_DIR / "assets" / "js" / "data.js"),
        "{{SITE_URL}}": esc(bio.get("site_url", "")),
        "{{NAME}}": esc(bio["name"]),
        "{{META_DESCRIPTION}}": esc(meta_desc),
        "{{PROFILE_IMAGE}}": esc(bio.get("profile_image", "assets/img/profile.jpeg")),
        "{{TWITTER_HANDLE}}": esc(f"@{twitter_id}" if twitter_id else ""),
        "{{JSON_LD}}": render_json_ld(bio),
        "{{SIDEBAR}}": render_sidebar(bio),
        "{{BIO}}": render_bio(bio),
        "{{SELECTED_PUBLICATIONS}}": selected_html,
        "{{RESUME_PAPERS}}": resume_html,
        "{{SELECTED_BLOGS}}": render_blogs(data["blogs"], selected_only=True),
        "{{ALL_BLOGS}}": render_blogs(data["blogs"], selected_only=False),
        "{{BLOG_CONTROLS}}": render_blog_controls(data["blogs"]),
        "{{WORKS}}": render_works(data["works"]),
        "{{EDUCATION}}": render_education(data),
        "{{EXPERIENCE}}": render_experience(data),
        "{{RESEARCH}}": render_research(data),
        "{{TEACHING}}": render_teaching(data),
        "{{HONORS}}": render_honors(data),
        "{{NEWS}}": render_news(data),
        "{{TIMELINE}}": render_timeline(data),
        "{{SOCIAL_POSTS}}": render_social_posts(data),
    }

    output = template
    for placeholder, html in replacements.items():
        output = output.replace(placeholder, html)

    OUTPUT_PATH.write_text(output)
    print(f"Built {OUTPUT_PATH} ({len(output):,} bytes)")

    # Project landing pages (publications + works)
    generate_project_pages(data)

    # One standalone page per timeline filter, so a filtered view is a real
    # pre-built rail behind its own link instead of a client-side trick.
    generate_timeline_pages(data, bio)

    # Sitemap
    sitemap_path = BASE_DIR / "sitemap.xml"
    sitemap_path.write_text(generate_sitemap(bio, data["blogs"]))
    print(f"Built {sitemap_path}")

    # RSS feed (blog posts)
    feed_path = BASE_DIR / "feed.xml"
    feed_path.write_text(generate_rss(bio, data["blogs"]))
    print(f"Built {feed_path}")

    # Resume PDF
    build_resume_pdf(data)

    # Long-form CV PDF
    build_cv_pdf(data)


if __name__ == "__main__":
    main()

TIMELINE_PAGE = """<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="description" content="{description}" />
        <title>{title} - {name}</title>
        <link rel="canonical" href="{url}" />
        <link rel="stylesheet" href="../../assets/css/vendor.css" />
        <link rel="stylesheet" href="../../assets/css/style.css?v={css_hash}" />
        <link rel="icon" type="image/jpeg" href="../../assets/img/profile-sm.jpeg" />
    </head>
    <body>
        <div class="page-layout">
            <main class="main-content">
                <section class="page-section active" aria-label="Timeline">
                    <div class="content-section">
                        <a href="../../index.html?tab=timeline" class="blog-back">&larr; Back to the timeline</a>
                        <h2>{title}</h2>
{timeline}
                    </div>
                </section>
            </main>
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


def generate_timeline_pages(data, bio):
    """Write timeline/<filter>/index.html for every filter chip."""
    site = bio.get("site_url", "").rstrip("/")
    written = 0
    for key, label in _TL_FILTER_ORDER:
        html = render_timeline(data, only=key, sub=True)
        if "timeline-item" not in html:
            continue                       # nothing under this filter
        # the page sits two levels down, so in-site paths need the hop
        for rel in ("assets/", "projects/", "blogs/"):
            html = html.replace(f'src="{rel}', f'src="../../{rel}')
            html = html.replace(f'href="{rel}', f'href="../../{rel}')
        out = BASE_DIR / "timeline" / key
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(TIMELINE_PAGE.format(
            name=esc(bio["name"]),
            title=esc(f"{label} on the timeline"),
            description=esc(f"{label} from the timeline of {bio['name']}."),
            url=esc(f"{site}/timeline/{key}/"),
            css_hash=file_hash(BASE_DIR / "assets" / "css" / "style.css"),
            timeline=html,
        ))
        written += 1
    print(f"Built {written} timeline filter pages")

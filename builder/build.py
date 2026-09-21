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

import re
import sys
import shutil
import subprocess

from .build_config import BASE_DIR, OUTPUT_PATH, TEMPLATE_PATH
from .build_html import (
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
    render_timeline_views,
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
        "{{TIMELINE}}": render_timeline_views(data),
        "{{SOCIAL_POSTS}}": render_social_posts(data),
    }

    output = template
    for placeholder, html in replacements.items():
        output = output.replace(placeholder, html)

    # One page per tab, each carrying only its own section. Navigation is
    # plain links between real files, so a refresh lands where it should
    # without JavaScript deciding anything.
    for tab, out_path, depth in TAB_PAGES:
        page = _tab_page(output, tab, depth)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page)
        print(f"Built {out_path} ({len(page):,} bytes)")

    # Project landing pages (publications + works)
    generate_project_pages(data)

    # Search index over the generated post and project pages (pagefind).
    # The blog search box queries it at runtime, so the listing no longer
    # has to carry the full text of every post as an attribute.
    if shutil.which("pagefind"):
        subprocess.run(
            ["pagefind", "--site", str(BASE_DIR), "--glob",
             "{blogs,projects}/**/*.html", "--output-path",
             str(BASE_DIR / "pagefind")],
            check=False, capture_output=True,
        )
        print(f"Built {BASE_DIR / 'pagefind'}")
    else:
        print("pagefind not found: search index left as is", file=sys.stderr)

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

# tab -> (file, how many directories deep it sits)
TAB_PAGES = [
    ("about", BASE_DIR / "index.html", 0),
    ("cv", BASE_DIR / "cv" / "index.html", 1),
    ("blogs", BASE_DIR / "blogs" / "index.html", 1),
    ("timeline", BASE_DIR / "timeline" / "index.html", 1),
]
# spelled out, so the links work off the filesystem too, not just a server
TAB_PATHS = {
    "about": "index.html",
    "cv": "cv/index.html",
    "blogs": "blogs/index.html",
    "timeline": "timeline/index.html",
}


def _tab_page(html, tab, depth):
    """Cut the whole-site render down to one tab and fix its paths."""
    up = "../" * depth
    for other in TAB_PATHS:
        if other != tab:
            html = re.sub(
                rf'<section id="{other}" class="page-section.*?</section>',
                "", html, flags=re.S)
    html = html.replace(f'<section id="{tab}" class="page-section',
                        f'<section id="{tab}" class="page-section active')
    html = html.replace('class="page-section active active"',
                        'class="page-section active"')
    # nav marker for the page we are on
    html = html.replace(f'class="nav-link" data-page="{tab}"',
                        f'class="nav-link active" data-page="{tab}"')
    if tab != "about":
        html = html.replace('class="nav-link active" data-page="about"',
                            'class="nav-link" data-page="about"')
    if depth:
        # tell the scripts how to reach the site root (pagefind lives there)
        html = html.replace("<html lang=\"en\">",
                            f'<html lang="en" data-root="{up}">', 1)
        # every site-relative path needs the hop out of this folder
        def rel(m):
            attr, val = m.group(1), m.group(2)
            skip = ("http", "//", "#", "?", "/", "mailto:", "tel:", "data:", "..")
            return m.group(0) if val.startswith(skip) else f'{attr}="{up}{val}"'
        html = re.sub(r'(href|src)="([^"]*)"', rel, html)
    # ?tab=x[&...][#y] -> the file that now holds x
    def link(m):
        target = TAB_PATHS[m.group(1)]
        rest = (m.group(2) or "").replace("&filter=", "?filter=")
        rest = rest.replace("&tags=", "?tags=")
        return f'href="{up}{target}{rest}"'
    html = re.sub(r'href="\?tab=(about|cv|blogs|timeline)([^"]*)"', link, html)
    return html

#!/usr/bin/env python3
"""
Static site builder for personal academic website.

Reads YAML data files and template.html, produces:
  - index.html    (rendered static site)
  - sitemap.xml   (SEO sitemap)
  - resume.pdf    (LaTeX-generated resume)

Usage:
    python build.py
"""

from build_config import BASE_DIR, OUTPUT_PATH, TEMPLATE_PATH
from build_html import (
    generate_sitemap,
    render_bio,
    render_blogs,
    render_compact_publication,
    render_education,
    render_experience,
    render_honors,
    render_json_ld,
    render_news,
    render_publication_card,
    render_research,
    render_sidebar,
    render_teaching,
    render_timeline,
    render_works,
)
from build_resume import build_resume_pdf
from build_utils import esc, file_hash, load_data


def main():
    data = load_data()
    bio = data["bio"]

    template = TEMPLATE_PATH.read_text()

    # Publications
    pubs = (data.get("publications") or {}).get("papers", [])
    selected_html = "\n".join(render_publication_card(p) for p in pubs if p.get("selected"))
    resume_html = "\n".join(render_compact_publication(p) for p in pubs if p.get("resume"))

    # Meta
    meta_desc = bio.get("meta_description") or (
        f'{bio["name"]} - {bio.get("title", "")} at {bio.get("affiliation", "")}.'
    )
    twitter_id = (bio.get("social") or {}).get("twitter", "")

    # Template replacements
    replacements = {
        "{{CSS_HASH}}": file_hash(BASE_DIR / "style.css"),
        "{{JS_HASH}}": file_hash(BASE_DIR / "data.js"),
        "{{SITE_URL}}": esc(bio.get("site_url", "")),
        "{{NAME}}": esc(bio["name"]),
        "{{META_DESCRIPTION}}": esc(meta_desc),
        "{{PROFILE_IMAGE}}": esc(bio.get("profile_image", "profile.jpeg")),
        "{{TWITTER_HANDLE}}": esc(f"@{twitter_id}" if twitter_id else ""),
        "{{JSON_LD}}": render_json_ld(bio),
        "{{SIDEBAR}}": render_sidebar(bio),
        "{{BIO}}": render_bio(bio),
        "{{SELECTED_PUBLICATIONS}}": selected_html,
        "{{RESUME_PAPERS}}": resume_html,
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

    # Sitemap
    sitemap_path = BASE_DIR / "sitemap.xml"
    sitemap_path.write_text(generate_sitemap(bio, data["blogs"]))
    print(f"Built {sitemap_path}")

    # Resume PDF
    build_resume_pdf(data)


if __name__ == "__main__":
    main()

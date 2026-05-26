"""Generate self-hosted project landing pages for publications and repos.

Called by the main build (`python -m builder`) - depends only on in-repo YAML.
One blog-styled page per selected publication and per open-source work, written
to projects/<slug>/index.html; titles on the About page link here. Optional
`abstract:` (papers) / `body:` (works) fields are rendered as page content.
"""

import re

from .build_config import BASE_DIR
from .build_html import render_tags
from .build_utils import esc, format_date, highlight_author, slugify

PROJECT_SHELL = """<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="description" content="{description}" />
        <title>{title} - Adnan Harun Dogan</title>
        <link rel="stylesheet" href="../../assets/css/style.css" />
        <link rel="icon" type="image/jpeg" href="../../assets/img/profile-sm.jpeg" />
        <link rel="stylesheet"
            href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" />
        <link rel="stylesheet"
            href="https://cdn.jsdelivr.net/gh/devicons/devicon@v2.16.0/devicon.min.css" />
        <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
    </head>
    <body>
        <div class="blog-page project-page">
            <a href="../../index.html" class="blog-back">&larr; Back to home</a>
            <h1>{title}</h1>
            <div class="blog-meta">{meta}</div>
            {image}
            <div class="blog-body">{body}</div>
            {links}
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


def _render_summary(text):
    """Render a stored summary (static text) with a tiny markdown subset:
    '## ' -> <h3>, '- ' -> <ul><li>, blank-line-separated blocks -> <p>.
    Consecutive non-blank lines join into one paragraph. Everything is escaped;
    math delimiters \\(...\\) / \\[...\\] pass through for MathJax to render.
    No fetching or generation happens here - only formatting of stored text.
    """
    if not text:
        return ""
    html, para, bullets, table = [], [], [], []

    def flush_para():
        if para:
            html.append(f"<p>{esc(' '.join(para))}</p>")
            para.clear()

    def flush_bullets():
        if bullets:
            html.append("<ul>" + "".join(f"<li>{esc(b)}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    def flush_table():
        if not table:
            return
        rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table]
        has_head = len(rows) > 1 and all(re.fullmatch(r":?-{2,}:?", c or "") for c in rows[1])
        head = rows[0] if has_head else None
        body = rows[2:] if has_head else rows
        thead = ("<thead><tr>" + "".join(f"<th>{esc(c)}</th>" for c in head) + "</tr></thead>") if head else ""
        tbody = "<tbody>" + "".join(
            "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>" for row in body
        ) + "</tbody>"
        html.append(f'<div class="blog-table"><table>{thead}{tbody}</table></div>')
        table.clear()

    def flush_all():
        flush_para(); flush_bullets(); flush_table()

    for line in str(text).split("\n"):
        s = line.strip()
        if not s:
            flush_all()
        elif s.startswith("## "):
            flush_all()
            html.append(f"<h3>{esc(s[3:])}</h3>")
        elif s.startswith("|") and s.endswith("|"):
            flush_para(); flush_bullets()
            table.append(s)
        elif s.startswith("- "):
            flush_para(); flush_table()
            bullets.append(s[2:])
        else:
            flush_bullets(); flush_table()
            para.append(s)
    flush_all()
    return "".join(html)


def _links_html(links):
    items = "".join(
        f'<a href="{esc(l["url"])}" class="pub-link" target="_blank" '
        f'rel="noopener noreferrer">{esc(l["name"])}</a>'
        for l in (links or []) if l.get("url")
    )
    return f'<div class="publication-links">{items}</div>' if items else ""


def _write(slug, *, title, meta, description, image="", body="", links=None):
    out = BASE_DIR / "projects" / slug
    out.mkdir(parents=True, exist_ok=True)
    page = PROJECT_SHELL.format(
        title=esc(title), meta=meta, description=esc(description),
        image=image, body=body, links=_links_html(links),
    )
    (out / "index.html").write_text(page)


def generate_project_pages(data):
    """Write a project page for each selected publication and each work."""
    count = 0

    for p in (data.get("publications") or {}).get("papers", []):
        if not p.get("selected"):
            continue
        meta = " &middot; ".join(x for x in [
            highlight_author(esc(p.get("authors", ""))),
            esc(p.get("venue", "")),
            esc(format_date(p.get("date", ""))),
        ] if x)
        image = (
            f'<img class="project-image" src="../../{esc(p["image"])}" '
            f'alt="{esc(p["title"])}" />' if p.get("image") else ""
        )
        body = _render_summary(p.get("abstract"))
        _write(slugify(p["title"]), title=p["title"], meta=meta,
               description=p.get("venue", ""),
               image=image, body=body, links=p.get("links"))
        count += 1

    for w in (data.get("works") or {}).get("works", []):
        meta = render_tags(w.get("tags"))
        body = _render_summary(w.get("body") or w.get("description"))
        links = [{"name": "GitHub", "url": w["url"]}] if w.get("url") else []
        _write(slugify(w["title"]), title=w["title"], meta=meta,
               description=w.get("description", ""), body=body, links=links)
        count += 1

    print(f"Built {count} project pages")

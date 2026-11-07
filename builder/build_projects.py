"""Generate self-hosted project landing pages for publications and repos.

Called by the main build (`python -m builder`) - depends only on in-repo YAML.
One blog-styled page per selected publication and per open-source work, written
to projects/<slug>/index.html; titles on the About page link here. Optional
`body:` fields (papers: the top-level `pages:` map in publications.yaml;
works: inline) are rendered as page content.
"""

import re

from .build_config import BASE_DIR
from .build_html import home_config, render_tags
from .build_utils import esc, file_hash, format_date, highlight_author, slugify

PROJECT_SHELL = """<!doctype html>
<html lang="en" data-root="../../"{motion}>
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="description" content="{description}" />
        <title>{title} - Adnan Harun Dogan</title>
        <link rel="stylesheet" href="../../assets/css/vendor.css" />
        <link rel="stylesheet" href="../../assets/css/style.css?v={css_v}" />
        <link rel="icon" type="image/jpeg" href="../../assets/img/profile-sm.jpeg" />
        <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
    </head>
    <body>
        {top}
        <div class="blog-page project-page">
            <a href="{back}" class="blog-back">&larr; {back_label}</a>
            <h1>{title}</h1>
            <div class="blog-meta">{meta}</div>
            {image}
            <div class="blog-body">{body}</div>
            {links}
        </div>
        {bottom}
        <script>
            const saved = localStorage.getItem("theme");
            if (saved) document.documentElement.setAttribute("data-theme", saved);
            else if (window.matchMedia("(prefers-color-scheme: dark)").matches)
                document.documentElement.setAttribute("data-theme", "dark");
        </script>
        <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>
        <script>if (window.hljs) hljs.highlightAll();</script>
    </body>
</html>
"""


# With home.layout: plain a project page sits in the site's one column
# under the same top menu as the tab pages.
PLAIN_TOP = """<div class="page-layout layout-plain layout-project">
        <main class="main-content">
        <nav class="main-nav" aria-label="Page navigation">
            <div class="nav-links">
                <a href="../../index.html" class="nav-link" data-page="about">About</a>
                <a href="../../cv/index.html" class="nav-link" data-page="cv" aria-label="Curriculum Vitae"><span class="nav-long">Curriculum Vitae</span><span class="nav-short">CV</span></a>
                <a href="../../blogs/index.html" class="nav-link" data-page="blogs">Blogs</a>
                <a href="../../timeline/index.html" class="nav-link" data-page="timeline">Timeline</a>
            </div>
            <button id="theme-toggle" class="theme-toggle" aria-label="Toggle dark/light theme">
                <i class="fas fa-sun"></i>
                <i class="fas fa-moon"></i>
            </button>
        </nav>"""
PLAIN_BOTTOM = """</main>
        </div>
        <script defer src="../../assets/js/data.js"></script>"""


_MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
_MD_CODE = re.compile(r"`([^`]+)`")


def _esc_code(s):
    """Escape text, turning `code` spans into <code> elements."""
    out, last = [], 0
    for m in _MD_CODE.finditer(s):
        out.append(esc(s[last:m.start()]))
        out.append(f"<code>{esc(m.group(1))}</code>")
        last = m.end()
    out.append(esc(s[last:]))
    return "".join(out)


def _inline(s):
    """Escape text but render markdown links [label](http...) and `code` spans."""
    out, last = [], 0
    for m in _MD_LINK.finditer(s):
        out.append(_esc_code(s[last:m.start()]))
        out.append(
            f'<a href="{esc(m.group(2))}" target="_blank" rel="noopener noreferrer">'
            f'{_esc_code(m.group(1))}</a>'
        )
        last = m.end()
    out.append(_esc_code(s[last:]))
    return "".join(out)


def _render_summary(text):
    """Render a stored summary (static text) with a tiny markdown subset:
    '## ' -> <h3>, '- ' -> <ul><li>, '|...|' -> table, blank lines -> <p>.
    '[label](url)' becomes a link; math delimiters \\(...\\) / \\[...\\] pass
    through for MathJax. Static formatting only - no fetching or generation.
    """
    if not text:
        return ""
    html, para, bullets, table = [], [], [], []

    def flush_para():
        if para:
            html.append(f"<p>{_inline(' '.join(para))}</p>")
            para.clear()

    def flush_bullets():
        if bullets:
            html.append("<ul>" + "".join(f"<li>{_inline(b)}</li>" for b in bullets) + "</ul>")
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
            "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>" for row in body
        ) + "</tbody>"
        html.append(f'<div class="blog-table"><table>{thead}{tbody}</table></div>')
        table.clear()

    def flush_all():
        flush_para(); flush_bullets(); flush_table()

    def emit_code(lang, lines):
        cls = f' class="language-{esc(lang)}"' if lang else ""
        html.append(f"<pre><code{cls}>{esc(chr(10).join(lines))}</code></pre>")

    code, in_code, code_lang = [], False, ""
    for line in str(text).split("\n"):
        s = line.strip()
        if s.startswith("```"):
            if in_code:
                emit_code(code_lang, code)
                code, in_code, code_lang = [], False, ""
            else:
                flush_all(); in_code = True
                code_lang = re.sub(r"[^\w+-]", "", s[3:].strip())
            continue
        if in_code:
            code.append(line)
            continue
        if not s:
            flush_all()
        elif s.startswith("## "):
            flush_all()
            html.append(f"<h3>{esc(s[3:])}</h3>")
        elif re.fullmatch(r"!\[[^\]]*\]\(assets/[^)\s]+\)", s):
            # '![caption](assets/...)' on its own line: a figure with the
            # caption beneath, opening in the lightbox like the teaser.
            flush_all()
            cap, src = re.fullmatch(r"!\[([^\]]*)\]\((assets/[^)\s]+)\)", s).groups()
            html.append(
                f'<figure class="project-figure"><img class="project-image" src="../../{esc(src)}" '
                f'alt="{esc(cap)}" data-caption="{esc(cap)}" />'
                + (f"<figcaption>{esc(cap)}</figcaption>" if cap else "") + "</figure>")
        elif s.startswith("|") and s.endswith("|"):
            flush_para(); flush_bullets()
            table.append(s)
        elif s.startswith("- "):
            flush_para(); flush_table()
            bullets.append(s[2:])
        else:
            flush_bullets(); flush_table()
            para.append(s)
    if in_code:
        emit_code(code_lang, code)
    flush_all()
    return "".join(html)


def _links_html(links):
    items = "".join(
        f'<a href="{esc(l["url"])}" class="pub-link" target="_blank" '
        f'rel="noopener noreferrer">{esc(l["name"])}</a>'
        for l in (links or []) if l.get("url")
    )
    return f'<div class="publication-links">{items}</div>' if items else ""


def _write(slug, *, title, meta, description, back, back_label,
           image="", body="", links=None, motion="", plain=False):
    out = BASE_DIR / "projects" / slug
    out.mkdir(parents=True, exist_ok=True)
    page = PROJECT_SHELL.format(
        title=esc(title), meta=meta, description=esc(description),
        back=back, back_label=back_label,
        css_v=file_hash(BASE_DIR / "assets" / "css" / "style.css"),
        image=image, body=body, links=_links_html(links), motion=motion,
        top=PLAIN_TOP if plain else "", bottom=PLAIN_BOTTOM if plain else "",
    )
    (out / "index.html").write_text(page)


def generate_project_pages(data, motion=""):
    """Write a project page for each selected publication and each work,
    and remove the pages of entries that no longer get one. `motion` is
    the <html> attribute of bio.yaml `animations`."""
    count = 0
    written = set()
    home = home_config(data.get("bio") or {})
    plain = home["layout"] == "plain"
    papers_label = "Publications" if home["publications"] == "all" else "Selected publications"
    works_back = ("../../index.html#selected-repos" if "open_source" in home["sections"]
                  else "../../blogs/index.html#selected-repos")

    for p in (data.get("publications") or {}).get("papers", []):
        if not p.get("selected"):
            continue
        # A submitted paper's target stays unnamed (double-blind review).
        venue = "Submitted" if p.get("stage") == "submitted" else p.get("venue", "")
        meta = " &middot; ".join(x for x in [
            highlight_author(esc(p.get("authors", ""))),
            esc(venue),
            esc(format_date(p.get("date", ""))),
        ] if x)
        # The figure keeps the paper's own caption beneath it.
        image = (
            f'<figure class="project-figure"><img class="project-image" src="../../{esc(p["image"])}" '
            f'alt="{esc(p["title"])}" data-caption="{esc(p.get("image_caption", ""))}" />'
            + (f'<figcaption>{esc(p["image_caption"])}</figcaption>' if p.get("image_caption") else "")
            + '</figure>' if p.get("image") else ""
        )
        body = _render_summary(p.get("body"))
        written.add(slugify(p["title"]))
        _write(slugify(p["title"]), title=p["title"], meta=meta,
               description=venue,
               back="../../index.html#selected-works",
               back_label=papers_label,
               image=image, body=body, links=p.get("links"), motion=motion, plain=plain)
        count += 1

    for w in (data.get("works") or {}).get("works", []):
        meta = render_tags(w.get("tags"))
        body = _render_summary(w.get("body") or w.get("description"))
        links = [{"name": "GitHub", "url": w["url"]}] if w.get("url") else []
        written.add(w["id"])
        _write(w["id"], title=w["title"], meta=meta,
               description=w.get("description", ""),
               back=works_back,
               back_label="Open source",
               body=body, links=links, motion=motion, plain=plain)
        count += 1

    for d in sorted((BASE_DIR / "projects").iterdir()):
        if d.is_dir() and d.name not in written and [f.name for f in d.iterdir()] == ["index.html"]:
            (d / "index.html").unlink()
            d.rmdir()
            print(f"Removed stale project page {d.name}")
    print(f"Built {count} project pages")

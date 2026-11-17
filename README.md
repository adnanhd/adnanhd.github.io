# Adnan Harun Dogan - Personal Website

Personal site, deployed at [adnanhd.github.io](https://adnanhd.github.io).
All content lives in `data/*.yaml` and `meta/*.yaml`; a Python builder
renders it into static pages (About, CV, Blogs, Timeline, one page per
paper, project and post) and two PDFs, ready to publish on GitHub Pages.

## Data model in one paragraph

Everything is an **entry**: a unique `id`, a `data:` record, a `show:`
list of the views it appears in, and prose, awards and links beside
them. The grammar of every file is written once in `meta/schema.yaml`
and checked before each build. Publications nest under the position
that produced them via `source`; venues, authors, institutions,
courses and projects resolve from the shared pools in `meta/`; any
entry can carry dated `news` one-liners.
A news entry feeds the **News** section and the **Timeline** at once:
News is the curated cut of the Timeline, the way `resume.pdf` is the
cut of `cv.pdf`. There is no separate news file. The shapes are
explained in [`data/README.md`](data/README.md).

## Features

- **Data-driven**: every list (education, experience, research,
  publications, honors, blogs, open-source) lives in a YAML file;
  `python -m builder` regenerates the site.
- **Four pages from one template**: About (`index.html`), CV
  (`cv/index.html`), Blogs (`blogs/index.html`) and Timeline
  (`timeline/index.html`) share a sidebar identity card (`home.layout:
  plain` in `bio.yaml` drops it). Navigation is plain links between the
  files; old `?tab=` links redirect. Sections and timeline years and
  months are anchors (`timeline/index.html#2024-06`).
- **Calendar-block Timeline**: newest year on top, year pills as
  boundary markers, months as fixed rail stops; publication cards on
  the left, degrees and news on the right, positions as parallel
  coloured bars with exact date endpoints. Hovering a bar, card or
  rail dot highlights its colour group.
- **Source-nested publications**: `source` links a paper to the
  position that produced it; the paper card wears the position's
  colour and shows Supervisor / Laboratory / Employment meta rows.
- **Attached awards**: any entry can carry `awards:`; they badge the
  parent and aggregate into CV Honors.
- **Blogs**: one bullet per post (`date: linked title #tags`), tag
  filters with inheritance (`tag_tree`), full-text search over a
  [pagefind](https://pagefind.app/) index, and per-post pages generated
  from org notes with pandoc. Paper and software pages are wired into
  the same listing.
- **Two PDFs from the same data**: `resume.pdf` (entries flagged
  `resume: true`) and `cv.pdf` (everything), both via LaTeX templates.
- **Print-friendly CV**: Ctrl+P on the CV page yields a clean
  multi-page document; chrome, bars and images are stripped.
- **Light / dark theme**: persisted to `localStorage`, matches the
  system preference on first load.
- **No third-party requests**: fonts and icons are self-hosted and
  subsetted (`assets/fonts/`, `assets/css/vendor.css`).

## Requirements

Python 3 with PyYAML; `pdflatex` for the PDFs; `pagefind` on `PATH` for
the search index (without it the index is left as it is); `pdfinfo` and
`pdftotext` for the PDF checks; `pandoc` for the blog pages.
`requirements.txt` also lists matplotlib (`figures/`), fonttools and
brotli (`tools/build_vendor_fonts.py`) and scholarly, which no script
imports.

## Quick start

1. Drop a square `assets/img/profile.jpeg` (and a 160x160
   `assets/img/profile-sm.jpeg` for the sidebar).
2. Edit the YAML under `data/` and `meta/` - see
   [`data/README.md`](data/README.md) for every file and field.
3. Build.

> **Note**: `data/**` and `meta/**` are git-crypt encrypted, except
> `data/README.md` and `meta/schema.yaml` (`.gitattributes`); a fresh
> clone needs `git-crypt unlock` with the key before it builds.

## Building

```bash
python -m builder
```

Writes `index.html`, `cv/index.html`, `blogs/index.html`,
`timeline/index.html`, `sitemap.xml`, `feed.xml`, `resume.pdf`,
`cv.pdf`, the per-paper / per-work pages under `projects/` and the
`pagefind/` index, then warns about CV and resume bullets that wrap
or leave a gap (`builder/check_lines.py`). A tracked pre-commit hook
runs the build when a commit touches `data/`, `meta/`, `builder/`,
`assets/` or a template, refuses the commit when `resume.pdf` is not
one page or `python -m builder.check_links` finds a dead link (404 or
410), and stages the regenerated artifacts. Enable it once per clone:

```bash
git config core.hooksPath .githooks
```

Blog pages are built separately (they shell out to `pandoc` and read
the org notes under `~/org/roam.d/informatics`):

```bash
python -m builder.build_blogs
```

Blog figures come from `python figures/build.py` (see
[`figures/README.md`](figures/README.md)); `tools/build_vendor_fonts.py`
refreshes the self-hosted fonts.

## Local testing

The blog search loads pagefind as a module and reads its index in byte
ranges, which works neither from `file://` nor under
`python -m http.server`; `serve.py` serves the tree with Range support:

```bash
python3 serve.py            # http://localhost:8000; a port as argument
```

## Deployment

GitHub Pages: push to `main`. The build runs in the pre-commit hook,
so the committed artifacts are always up to date with the YAML.

The same artifacts also publish to a separate host via plain `rsync`:

```bash
rsync -av --delete \
  index.html 404.html sitemap.xml robots.txt feed.xml resume.pdf cv.pdf \
  assets projects blogs cv figures timeline pagefind \
  user@host:public_html/
```

`install.sh user@host:/path` copies with `scp` only `index.html`,
`sitemap.xml`, `robots.txt`, `404.html`, `resume.pdf`, the Google site
verification file, `assets/` and `blogs/`.

## File structure

```
index.html, cv/, blogs/, timeline/   Generated tab pages (python -m builder)
projects/               Generated per-paper / per-work pages
blogs/<slug>/           Generated blog posts (python -m builder.build_blogs)
pagefind/               Generated search index
resume.pdf, cv.pdf      Generated; resume: true entries only, and everything
template.html           HTML template with {{PLACEHOLDER}} slots
resume_template.tex, cv_template.tex
builder/
  build.py              Orchestrates: load YAML -> render -> write
  build_config.py       Paths, author identity, link templates
  build_html.py         Section renderers (news, timeline, blogs, ...)
  build_projects.py     Per-paper / per-work pages
  build_blogs.py        Blog pages from org notes (pandoc)
  build_resume.py       resume_template.tex -> resume.pdf
  build_cv.py           cv_template.tex -> cv.pdf
  build_utils.py        load_data + normalization, esc, format_date
  schema.py             Checks the YAML against meta/schema.yaml
  check_lines.py        Bullet wrap and gap warnings for the PDFs
  check_links.py        External link check
data/                   YAML inputs - see data/README.md
meta/                   Shared pools and schema.yaml
assets/
  css/style.css         All styling (@media print near the bottom)
  css/vendor.css        Self-hosted font and icon rules
  js/data.js            Client-side only: theme, filters, search,
                        timeline hover; no runtime YAML loading
  fonts/, img/
figures/                Blog figure generators
tools/                  Font subsetting
serve.py                Local server with Range support
.githooks/pre-commit    Build, checks and staging on commit
```

## How it works

1. `builder/build_utils.py` loads every `data/*.yaml` and `meta/*.yaml`,
   checks them against `meta/schema.yaml` (`builder/schema.py`) and
   normalizes: `data` records are hoisted, `show` and `dates` become
   flags and endpoints, the pools resolve, APA author strings and
   sentence-case titles derive.
2. `build_html.py` renders each section and substitutes the results
   into the `{{...}}` placeholders in `template.html`; `build.py` then
   writes one page per tab, each carrying only its own section.
3. `build_projects.py` renders per-item pages under
   `projects/<slug>/`; `build_blogs.py` renders posts under
   `blogs/<slug>/`; pagefind indexes the post and project pages.
4. Static assets are cache-busted with a content hash (`?v=<hash>`).

## License

MIT - see `LICENSE.md`.

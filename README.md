# Adnan Harun Dogan - Personal Website

Single-page personal site, deployed at
[adnanhd.github.io](https://adnanhd.github.io). All content lives in
`data/*.yaml`; a Python builder renders the site into static
`index.html` plus per-paper / per-project / per-post pages, ready to
publish on GitHub Pages.

## Data model in one paragraph

Everything is an **entry**: a unique `id`, a `data:` block (the record
itself) and a `meta:` block (presentation flags). Publications nest
under the position that produced them via `meta.source`, venues and
author names resolve from shared pools (`venues.yaml`,
`authors.yaml`), and any entry can carry dated `meta.news` one-liners.
A news entry feeds the **News** section and the **Timeline** at once:
News is the curated cut of the Timeline, the way `resume.pdf` is the
cut of `cv.pdf`. There is no separate news file. Field-by-field
schemas live in [`data/README.md`](data/README.md).

## Features

- **Data-driven**: every list (education, experience, research,
  publications, honors, blogs, open-source) lives in a YAML file;
  `python -m builder` regenerates the site.
- **About / CV / Blogs / Timeline** tabs share a sidebar identity
  card; navigation is client-side query-param routing over one static
  `index.html`. Sections and timeline years/months are deep-linkable
  (`?tab=timeline#2024-06`).
- **Calendar-block Timeline**: newest year on top, year pills as
  boundary markers, months as fixed rail stops; publication cards on
  the left, degrees and news on the right, positions as parallel
  coloured bars with exact date endpoints. Hovering a bar, card or
  rail dot highlights its colour group.
- **Source-nested publications**: `meta.source` links a paper to the
  position that produced it; the paper card wears the position's
  colour and shows Supervisor / Laboratory / Employment meta rows.
- **Attached awards**: any entry can carry `awards:`; they badge the
  parent and aggregate into CV Honors.
- **Blogs**: one bullet per post (`date: linked title #tags`), tag
  filters with inheritance (`tag_tree`), full-text search, and
  per-post pages generated from org notes with pandoc. Paper and
  software pages are wired into the same listing.
- **Two PDFs from the same data**: `resume.pdf` (entries flagged
  `resume: true`) and `cv.pdf` (everything), both via LaTeX templates.
- **Print-friendly CV**: Ctrl+P on the CV tab yields a clean
  multi-page document; chrome, bars and images are stripped.
- **Light / dark theme**: persisted to `localStorage`, matches the
  system preference on first load.

## Quick start

1. Drop a square `assets/img/profile.jpeg` (and a 160x160
   `assets/img/profile-sm.jpeg` for the sidebar).
2. Edit the YAML under `data/` - see [`data/README.md`](data/README.md)
   for every file and field.
3. Build.

> **Note**: in this clone, `data/*.yaml` is git-crypt encrypted with
> the key at `~/.config/git-crypt/github-page-key`
> (`data/README.md` itself stays plain text). Adapt to your own
> private clone as needed.

## Building

```bash
python -m builder
```

Writes `index.html`, `sitemap.xml`, `feed.xml`, `resume.pdf`,
`cv.pdf`, and per-paper / per-work pages under `projects/`. A tracked
pre-commit hook re-runs the build and stages the regenerated artifacts
automatically - enable it once per clone:

```bash
git config core.hooksPath .githooks
```

Blog pages are built separately (they shell out to `pandoc`):

```bash
python -m builder.build_blogs
```

## Local testing

`index.html` is fully static - open it directly in a browser, or serve
the tree:

```bash
python -m http.server 8000
```

## Deployment

GitHub Pages: push to `main`. The build runs in the pre-commit hook,
so the committed artifacts are always up to date with the YAML.

The same artifacts also publish to a separate host via plain `rsync`:

```bash
rsync -av --delete \
  index.html 404.html sitemap.xml robots.txt feed.xml resume.pdf cv.pdf \
  assets projects blogs \
  user@host:public_html/
```

## File structure

```
├── index.html              # Generated (python -m builder)
├── resume.pdf              # Generated, resume: true entries only
├── cv.pdf                  # Generated, everything
├── template.html           # HTML template with {{PLACEHOLDER}} slots
├── builder/
│   ├── build.py            # Orchestrates: load YAML -> render -> write
│   ├── build_config.py     # Paths, author identity, link templates
│   ├── build_html.py       # Section renderers (news, timeline, blogs, ...)
│   ├── build_projects.py   # Per-paper / per-work pages
│   ├── build_blogs.py      # Blog pages from org notes (pandoc)
│   ├── build_resume.py     # resume.tex -> resume.pdf
│   ├── build_cv.py         # cv.tex -> cv.pdf
│   └── build_utils.py      # load_data + normalization, esc, format_date
├── data/                   # YAML inputs - see data/README.md
├── assets/
│   ├── css/style.css       # All styling (@media print near the bottom)
│   ├── js/data.js          # Client-side only: theme, routing, filters,
│   │                       #   timeline hover; no runtime YAML loading
│   └── img/
├── projects/               # Generated per-paper / per-work pages
├── blogs/                  # Generated blog pages
└── README.md
```

## How it works

1. `builder/build_utils.py` loads every `data/*.yaml` and normalizes:
   two-layer entries are hoisted, venue and author pools resolve,
   APA author strings and sentence-case titles derive, `pages:`
   bodies attach.
2. `build_html.py` renders each section and substitutes the results
   into the `{{...}}` placeholders in `template.html`.
3. `build_projects.py` renders per-item pages under
   `projects/<slug>/`; `build_blogs.py` renders posts under
   `blogs/<slug>/`.
4. Static assets are cache-busted with a content hash (`?v=<hash>`).

## License

MIT - see `LICENSE.md`.

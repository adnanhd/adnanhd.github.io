# Adnan Harun Dogan - Personal Website

Single-page personal site, deployed at
[adnanhd.github.io](https://adnanhd.github.io). All content lives in
`data/*.yaml`; a Python builder renders the site into static
`index.html` + per-paper / per-project pages, ready to publish on GitHub
Pages.

## Features

- **Data-driven**: every list (education, experience, research,
  publications, awards, news, blogs, open-source) lives in a YAML file;
  `python -m builder` regenerates the site.
- **About / CV / Blogs** pages share a sidebar identity card. Navigation
  is client-side (hash routes) so the static `index.html` keeps every
  section.
- **Cartesian Timeline** with internships / research on the left
  (multi-lane greedy interval colouring) and degrees on the right.
  Year bands have variable heights (sized to the densest column for
  that year), with a per-year cap so a short-span dense card extends
  downward instead of inflating the year. Month ticks decorate the
  rail.
- **Source-nested publications**: each paper carries an optional
  `source:` slug pointing at the experience / research / education
  entry that produced it. Attached papers render as compact 2-line
  chips inside the parent's timeline card (venue tag + title on line
  1, authors on line 2) instead of as a separate slim card.
- **Attached awards**: any publication / education / experience /
  research entry can carry an `awards:` array. Awards surface as a
  small badge on the parent entry AND get aggregated into the CV
  Honors section (deduplicated by their parent, sorted newest first).
- **Open Source cards** (About page): the title links to the GitHub
  repository, the rest of the card surface navigates to the
  per-project detail page; the standalone `[GitHub]` pill is dropped
  on the card (it still appears on the project page itself).
- **Auto-derived News → Timeline jump**: each news row carries a
  `timeline_ref:` slug; clicking the row scrolls the Timeline page to
  the corresponding card.
- **Per-paper / per-project pages**: every selected publication and
  open-source work gets a generated page under `projects/<slug>/`,
  rendered from a markdown-ish `abstract:` / `body:` block with
  MathJax + a small subset of headings, lists and pipe-tables.
- **Print-friendly CV**: `Ctrl+P` on the CV page yields a clean
  multi-page PDF (the timeline / nav chrome is stripped, awards
  collapse to text, icon fonts are preserved).
- **Light / dark theme**: persisted to `localStorage`, matches the
  system preference on first load to avoid a flash.
- **Static `resume.pdf`**: built from the same data via a LaTeX
  template (`builder/build_resume.py` → `resume.tex`).

## Quick Start

### 1. Profile picture

Drop a square image as `assets/img/profile.jpeg` (and a 160×160 crop as
`assets/img/profile-sm.jpeg` for the sidebar).

### 2. Edit the YAML data

All content lives under `data/`. Dates use ISO precision: `YYYY`,
`YYYY-MM`, `YYYY-MM-DD`, or the literal `Present`. They render
human-readable at build time (`2025-03` → "March 2025").

> **Note**: in this clone, `data/*.yaml` is git-crypt encrypted with the
> key at `~/.config/git-crypt/github-page-key`. Adapt to your own
> private clone as needed.

#### `data/bio.yaml`

```yaml
name: "Jane Doe"
title: "PhD Student"
affiliation: "Example University"
profile_image: "assets/img/profile-sm.jpeg"
site_url: "https://janedoe.github.io"
short_bio: "One or two sentences for the sidebar."
bio: |
  Full bio (HTML allowed); blank lines separate paragraphs.
social:                           # IDs only - full URLs are generated
  email: "jane@example.com"
  github: "janedoe"
  linkedin: "jane-doe"
  google_scholar: "XXXXXXXX"
  orcid: "0000-0000-0000-0000"
custom_links:
  - name: "Resume"
    url: "resume.pdf"
```

Supported social platforms: `email`, `github`, `linkedin`,
`google_scholar`, `acm`, `ieee`, `dblp`, `semantic_scholar`, `twitter`,
`orcid`.

#### `data/education.yaml`

```yaml
education:
  - degree: "PhD in Computer Science"
    institution: "Example University"
    location: "City, Country"
    start_date: "2023-09"
    end_date: "Present"
    advisor: "Prof. A. Adviser"
    logo: "assets/img/logos/example.png"
    timelined: true                # show on the Timeline page
    id: "phd"                      # optional; defaults to slugify(degree).
                                   # Needed only when several entries share
                                   # the same degree title.
    awards:                        # optional; aggregated into CV Honors
      - name: "Departmental Fellowship"
        organization: "Example University"
        date: "2023"
        description: "..."         # shown on the Honors page
        link: "https://..."
        logo: "assets/img/logos/example.png"
```

#### `data/experience.yaml` and `data/research.yaml`

Both use the same shape (`position`, `company`, dates, `bullets`,
`logo`, `timelined`, `id`, `awards`). `experience.yaml` is internships
and salaried positions; `research.yaml` is unpaid research projects.

```yaml
experience:
  - position: "Research Intern"
    company: "Example Lab"
    location: "City, Country"
    start_date: "2024-06"
    end_date: "2024-09"
    advisor: "Prof. A. Adviser"
    commitment: "Full-time, 3 months"
    logo: "assets/img/logos/example.png"
    timelined: true
    id: "lab-intern-2024"          # optional explicit id (see below)
    bullets:
      - "What you did, one line each."
    awards:
      - name: "Intern of the Year"
        organization: "Example Lab"
        date: "2024"
```

#### `data/publications.yaml`

```yaml
papers:
  - title: "A Paper Title"
    authors: "Doe, J., Coauthor, A."
    venue: "Conference on Examples"
    venue_short: "CoE 2025"            # coloured tag on the About card
    venue_link: "https://example.org"  # optional; makes the tag clickable
    date: "2025-04"
    image: "assets/img/publications/paper.png"
    selected: true                     # show on About > Selected Publications
    resume:   true                     # show on CV > Publications
    source:   "lab-intern-2024"        # OPTIONAL: nest this paper inside its
                                       # parent timeline entry. Value is the
                                       # parent's id (or slugify(title) if no
                                       # explicit id). Validated at build
                                       # time; a build warning fires if the
                                       # slug doesn't resolve.
    abstract: |
      ## Problem
      Markdown with '## ' sections, '|' tables, and MathJax math such as
      \(a^2 + b^2 = c^2\) inline or \[ E = mc^2 \] as a display equation.
    awards:                            # optional; renders as a badge under
                                       # the paper AND on CV Honors
      - name: "Best Paper Award"
        organization: "CoE 2025"
        link: "https://doi.org/..."
        description: "..."
    links:
      - name: "Paper"
        url: "https://arxiv.org/abs/0000.00000"
      - name: "GitHub"
        url: "https://github.com/user/repo"
```

`source:` is the key to the nested-pub view. A paper with a valid
`source:` is removed from the standalone left-column timeline and
rendered as a 2-line chip inside its parent's card. A paper without
`source:` is rendered standalone (slim card on the left).

#### `data/teaching.yaml` and `data/extracurricular.yaml`

Same shape as `experience.yaml`. `extracurricular.yaml` also holds
orphan honors — awards that don't naturally attach to a publication or
position (general scholarships, fellowships):

```yaml
honors:
  - title: "Some Open Award"
    organization: "Some Foundation"
    date: "2024"
    logo: "..."
    description: "..."
    timelined: true               # show as its own row on the Timeline
                                  # (set false if it should only appear
                                  # in the CV Honors aggregate)
skills:
  - "Python"
  - "PyTorch"
```

#### `data/news.yaml`

```yaml
items:
  - date: "2025-03"
    content: "Something happened."
    link: "https://example.org"              # optional [link] anchor
    timeline_ref: "research-intern"          # optional; clicking the row
                                             # jumps to that Timeline card
    tags: [publication]                      # publication | degree |
                                             # internship | award | life-event
```

#### `data/blogs.yaml`

```yaml
tag_tree:
  machine-learning:
    - reinforcement-learning
blogs:
  - title: "A Blog Post"
    date: "2025-01"
    description: "One-line summary."
    path: "blogs/my-post/index.html"
    selected: true
    tags: [reinforcement-learning]
```

#### `data/works.yaml`

```yaml
works:
  - title: "my-project"
    description: "One line for the card."
    url: "https://github.com/user/my-project"   # title link target on About
    tags: ["Python", "PyTorch"]
    body: |
      Markdown body for the per-project page.
```

About > Open Source card title links to `url` (GitHub repo); the rest
of the card body navigates to the generated `projects/<slug>/` page.

### 3. (Optional) Auto-fetch publications from Google Scholar

```bash
pip install -r requirements.txt
# add `google_scholar_id: "XXXXXXXX"` to data/publications.yaml, then:
python builder/fetch_publications.py
```

Pulls every paper from your Scholar profile into
`data/publications.yaml` (you can still hand-edit afterwards).

## Building

```bash
python -m builder
```

Writes `index.html`, `sitemap.xml`, `resume.pdf`, and per-paper /
per-work pages under `projects/`. A tracked pre-commit hook re-runs
the build and stages the regenerated artifacts automatically — enable
it once per clone:

```bash
git config core.hooksPath .githooks
```

Blog pages are built separately (they shell out to `pandoc`):

```bash
python -m builder.build_blogs
```

## Local testing

`index.html` is fully static — open it directly in a browser, or serve
the tree:

```bash
python -m http.server 8000
# http://localhost:8000
```

## Deployment

GitHub Pages: push to `main` (or whichever branch your Pages config
points to). The build runs in the pre-commit hook, so the committed
`index.html` is always up-to-date with the YAML.

The same artifacts also publish to a separate host via plain `rsync`:

```bash
rsync -av --delete \
  index.html 404.html sitemap.xml robots.txt resume.pdf \
  assets projects blogs \
  user@host:public_html/
```

`--delete` only applies inside the synced subtrees (`assets/`,
`projects/`, `blogs/`), so unrelated top-level files on the host are
preserved.

## File structure

```
├── index.html              # Generated (python -m builder)
├── resume.pdf              # Generated from data via LaTeX
├── template.html           # HTML template with {{PLACEHOLDER}} slots
├── builder/                # Static site builder
│   ├── __main__.py         # python -m builder entry point
│   ├── build.py            # Orchestrates: load YAML -> render -> write
│   ├── build_config.py     # Paths, author identity, link templates
│   ├── build_html.py       # Section renderers (incl. timeline,
│   │                       #   render_works, render_honors,
│   │                       #   _render_nested_pub, etc.)
│   ├── build_projects.py   # Per-paper / per-work project pages
│   ├── build_blogs.py      # Blog pages from org notes (pandoc)
│   ├── build_resume.py     # Renders resume.tex -> resume.pdf
│   ├── build_utils.py      # esc, format_date, slugify, highlight_author
│   └── fetch_publications.py
├── data/                   # YAML inputs (git-crypt encrypted in author's
│   │                       #   clone; plain text for forks)
│   ├── bio.yaml
│   ├── education.yaml
│   ├── experience.yaml
│   ├── research.yaml
│   ├── teaching.yaml
│   ├── extracurricular.yaml
│   ├── publications.yaml
│   ├── news.yaml
│   ├── blogs.yaml
│   └── works.yaml
├── assets/
│   ├── css/style.css       # All styling (light/dark themes near the top,
│   │                       #   @media print near the bottom)
│   ├── js/data.js          # Client-side only: theme toggle, hash routing,
│   │                       #   blog tag filtering, news-row / open-source
│   │                       #   card click handler, image lightbox.
│   │                       #   Does NOT load YAML at runtime.
│   └── img/                # profile*.jpeg, logos/, publications/
├── projects/               # Generated per-paper / per-work pages
├── blogs/                  # Generated blog pages
└── README.md
```

## How it works

1. `python -m builder` loads every `data/*.yaml`, hydrates the in-
   memory event objects (timelined entries get an `id`; sourced
   publications attach to their parent's `child_pubs`).
2. `build_html.py` renders each named section (bio, news, selected
   publications, CV, timeline, open source, ...) and substitutes the
   results into the `{{...}}` placeholders in `template.html`.
3. `build_projects.py` walks every `selected:` paper and every entry
   in `works.yaml`, rendering a per-item page under
   `projects/<slug>/index.html`.
4. Static asset cache-busting: the build hashes the contents of
   `style.css` / `data.js` and appends `?v=<hash>` to their
   references, so hard-refresh is the only step needed after a
   deploy.

`data.js` is intentionally small: theme switching, hash-based page
routing, blog tag filter, image lightbox, and a generic click handler
for `data-href` boxes (news rows + open-source cards). All content
rendering is done at build time on the server / developer machine, not
in the browser.

## License

MIT — see `LICENSE.md`.

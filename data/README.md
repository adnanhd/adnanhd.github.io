# Data model

Every list on the site lives in one of these YAML files. `python -m
builder` loads them all, normalizes the records (see
`builder/build_utils.py`), and renders every view from the same
in-memory objects. The shared pools live in `meta/`; the top-level
`README.md` gives the one-paragraph overview.

The grammar of every file is written once, in
[`meta/schema.yaml`](../meta/schema.yaml), and `builder/schema.py` checks
all files against it before anything is normalized: an unknown field, a
missing required field, a key that is not in its pool or a malformed
date stops the build with `file.entry.field: problem`. This page
explains the shapes; the schema is the reference.

Naming: field names are snake_case, pool keys lowercase kebab-case, and
entry ids `uni__unit__role-or-supervisor` (`eth__siplab__holz`,
`metu__imagelab-denge__kalkan-akbas`, `metu__ceng__msc`,
`metu__ceng__ta`). Markdown links appear only in prose fields
(description, bullets, news text, body); names are plain text and links
live in `url` fields, the one name every link field uses.

Dates are ISO: a point is `date: 2025-06` (`YYYY`, `YYYY-MM`,
`YYYY-MM-DD`, optionally `HH:MM` for blogs), a span is
`dates: 2022-09-12/2025-01-10`, an ongoing span `dates: 2023-02/..`, a
year range `2022/2023`, a term `2024-spring`. They render
human-readable at build time (`2025-03` becomes "March 2025").

## One entry shape

Publications, education, experience, research and teaching entries all
share one layout: an `id`, a `data:` record, a `show:` list, and the
rest beside them.

```yaml
- id: eth__siplab__holz
  data:                       # the record
    position: "Research Intern"
    org: siplab               # meta/institutions.yaml
    advisors: [ch]            # meta/authors.yaml keys; co_advisors likewise
    dates: "2025-01/2025-10"
    load: full-time           # or hours: 6; remote: true; course: me460
  show: [timeline]            # where else it appears
  news:                       # see "News entries" below
    - date: "2025-01"
      text: "Started a research internship at [SIPLab](https://siplab.org/), ETH Zürich"
  description: "..."
  bullets: [...]
  awards:
    - {name: "...", org: tubitak, date: "2022/2023", show: [], url: "..."}
  links: [{name: DOI, url: "..."}]
```

The commitment line ("Remote, full-time, 4 months") is assembled from
`load`, `hours`, `remote` and `course`, with the duration of a finished
position taken from its dates. Advisor lines print each key's `title`
and `name`. Publications reference a position via `source`, and the
Timeline uses the same link to colour a paper with its parent
position's colour.

`show` tokens: entries take `timeline`; awards and honors `resume`
(listed in resume.pdf's honors) and `timeline` (honors only);
publications `front` (About page cards), `resume` and `timeline`.
cv.pdf lists everything.

## News entries

Any entry may carry `news`, a list of dated one-liners:

```yaml
news:
  - date: "2026-06"
    text: 'Our paper "[FW-NKF](https://arxiv.org/...)" accepted at **IEEE/ICRA 2026** in Vienna'
```

`text` is a plain string with two inline markers: `[phrase](url)` for
links and `**phrase**` for bold. Nothing else is interpreted; what you
mark is exactly what renders.

Each news entry feeds two views at once:

- the **News** section on the About page (newest first, capped at
  `_NEWS_MAX_ITEMS`), and
- a small news card on the **Timeline**, coloured like its owning
  entry.

An entry without `news` still appears on the Timeline (as a card or
position bar) but contributes nothing to News. News is therefore the
curated cut of the Timeline, the way `resume.pdf` is the cut of
`cv.pdf`. There is no separate news file.

## Pools (`meta/`)

- **`meta/venues.yaml`** - one record per venue under a lowercase key
  (`name`, `short`, `url`, `double_blind`, `selected`). A paper names
  the key (`venue: icra`, `target: cvpr`); the year suffix (`ICRA'26`)
  derives from the paper's date. Prestigious venues set
  `selected: true` once, in the pool; a paper overrides with its own
  `selected: true|false`.
- **`meta/authors.yaml`** - one record per co-author under a short key
  of initials (`oub`): `apa` (the reference form), `name`, `title` (the
  academic title for advisor lines), and any of `site`, `scholar`,
  `github`. The name links to the first of site, scholar, github.
- **`meta/institutions.yaml`** - one record per institution or lab:
  `name`, `short`, `url`, `parent`, `location`, `logo`. Cards print
  `name ([short](url)), <parent short or name>`; awards print
  `name (short)`; bio affiliations print `name`.
- **`meta/courses.yaml`** - one record per course (`code`, `name`,
  `url`). Teaching lists `courses: [{course: ceng280, terms:
  [2024-spring, ...]}]` and its dates derive from the terms; a degree
  lists `coursework: {optimization: [ie553, ...]}` under the groups of
  bio.yaml `coursework_groups`; a position may name `course: me460`.

## `publications.yaml`

```yaml
proper_nouns: [Kalman, Cappadocia, ...]   # survive sentence-casing

papers:
  - id: fwnkf
    kind: proceedings            # article | proceedings | chapter | thesis
    # stage: submitted           # published (default) | preprint | submitted
    # target: cvpr               # where a preprint or submitted paper is sent
    data:
      title: "Frequency-Weighted Neural Kalman Filters"
      authors: [ahd, bud, ch]    # pool keys or literal "Celtik, S. O."
      venue: icra                # pool key, or an inline dict:
      #venue: {id: ..., name: ..., prefix: ..., detail: ..., short: ..., url: ...}
      date: "2026-06"
    # selected: false            # overrides the venue's selected flag
    show: [front, resume, timeline]
    source: eth__siplab__holz    # nest under this position (colour, meta rows)
    image: "assets/img/publications/icra2026.png"
    news: [...]
    links:                       # DOI, ISBN, arXiv, PDF, Thesis, Code, Data
      - {name: arXiv, url: "..."}
    awards:
      - {name: "Best Paper Award", organization: "...", url: "..."}
    body: |                      # the project page (selected papers only)
      ## Problem
      Markdown-ish body with MathJax.
```

A submitted paper shows a "Submitted" badge and no venue name when its
target is double-blind; it stays off the Timeline until it appears.
cv.pdf lists every paper (Selected, Other, Theses). Author lists are
joined to APA form (`,` + final `&`) and the sentence-case `title_apa`
derives automatically, keeping `proper_nouns` capitalized. A degree's
`thesis: msc-thesis` names the paper whose title and Thesis link the
degree prints.

## `education.yaml`, `experience.yaml`, `research.yaml`, `teaching.yaml`

The one entry shape above. `education` uses `degree` (plus `thesis`,
a paper id or an inline `{label, title, url}`, and `coursework`); the
other three use `position`. `experience` is salaried positions and
internships, `research` is unpaid research projects. Timelined positions
draw as parallel coloured bars along the Timeline rail with exact date
endpoints.

## `extracurricular.yaml` and `bio.yaml` keywords

`honors` holds orphan awards that attach to no entry (same fields as
awards). `skills` maps an id to `{title, items}`, an item being plain
text or `{name, url}`; each renders as one bold-labelled line. The
resume's research-area lines are not written here: they come from
bio.yaml `research_keywords` (coursework group -> phrases), title-cased
under the group's `resume` name, and the site lists the same phrases
as its keywords.

## `blogs.yaml`

The listing for the Blogs tab. Entries point either at generated blog
pages (`blogs/<slug>/index.html`, built by `builder/build_blogs.py`
from org notes) or at existing paper / software pages under
`projects/`.

```yaml
tag_tree:                  # tag inheritance: a #policy-gradient post
  machine-learning:        # also matches the Machine Learning filter
    - reinforcement-learning
  reinforcement-learning:
    - policy-gradient
  software:
    - design-patterns

blogs:
  - title: "Policy Gradients: REINFORCE, Baselines, and GAE"
    date: "2026-01-15 14:32"
    description: "One-line summary."
    path: "blogs/policy-gradient-foundations/index.html"
    selected: true         # feature on the About page
    tags: [policy-gradient]   # leaves only; parents come via tag_tree
```

The listing renders as one bullet per post (`date: linked title
#tags`), sorted by date. The search box matches the full text of each
post (the builder folds the generated page's words into the search
index), and the inline `#tags` drive the same filter as the chips.

## `bio.yaml`, `works.yaml`, `social_posts.yaml`

- `bio.yaml` - identity card: name, title, affiliation, bio prose,
  social IDs (full URLs are generated), custom links.
- `works.yaml` - open-source cards; each gets a generated page under
  `projects/<id>/`.
- `social_posts.yaml` - curated link-preview cards for the "Media
  Posts" section of the Blogs tab.

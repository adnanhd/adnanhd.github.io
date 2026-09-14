# Data model

Every list on the site lives in one of these YAML files. `python -m
builder` loads them all, normalizes the records (see
`builder/build_utils.py`), and renders every view from the same
in-memory objects. This file documents the record shapes; the top-level
`README.md` gives the one-paragraph overview.

Dates use ISO precision everywhere: `YYYY`, `YYYY-MM`, `YYYY-MM-DD`,
optionally with `HH:MM` (blogs), or the literal `Present`. They render
human-readable at build time (`2025-03` becomes "March 2025").

## The two-layer entry

`publications`, `education`, `experience`, `research` and `teaching`
entries all share one layout:

```yaml
- id: "eth-siplab-cholz"      # unique slug, the cross-reference key
  data:                       # the record itself
    position: "Intern"
    company: "..."
    start_date: "2025-01"
    end_date: "2025-10"
    advisor: "Prof. Dr. Christian Holz"
  meta:                       # presentation flags
    logo: "assets/img/logos/eth.png"
    logo_link: "https://siplab.org/"
    timelined: true           # draw on the Timeline
    resume: true              # include in resume.pdf (cv.pdf takes all)
    news:                     # see "News entries" below
      - date: "2025-01"
        text: "Started a research internship at [SIPLab](https://siplab.org/), ETH Zürich"
  description: "..."          # prose, bullets, awards, links stay top-level
  bullets: [...]
  awards: [...]
  links: [...]
```

`id` is what everything else points at. Convention for positions:
`uni-lab-supervisor` (`metu-imagelab-kalkan-akbas` for multiple
supervisors). Publications reference a position via `meta.source`, and
the Timeline uses the same link to colour a paper with its parent
position's colour.

## News entries

Any entry may carry `meta.news`, a list of dated one-liners:

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

An entry without `meta.news` still appears on the Timeline (as a card
or position bar) but contributes nothing to News. News is therefore
the curated cut of the Timeline, the way `resume.pdf` is the cut of
`cv.pdf`. There is no separate news file.

## Pools

- **`venues.yaml`** - one record per venue (`name`, `short`, `link`,
  `double_blind`, `selected`). A paper's `venue:` can be just the pool
  key (`venue: "ICRA"`); the year suffix (`ICRA'26`) derives from the
  paper's date. Prestigious venues set `selected: true` once, in the
  pool.
- **`authors.yaml`** - display names, diacritics and profile links for
  co-authors. Any name that appears in an `advisor:` line or an author
  string renders as a link if the pool has one.

## `publications.yaml`

```yaml
proper_nouns: [Kalman, Cappadocia, ...]   # survive sentence-casing

papers:
  - id: "fwnkf"
    data:
      title: "Frequency-Weighted Neural Kalman Filters"
      authors: "Dogan, A. H.; Demirel, B. U.; Holz, C."   # "; "-separated
      venue: "ICRA"              # pool key, or an inline dict:
      #venue: {name: ..., prefix: ..., detail: ..., short: ..., link: ...}
      date: "2026-06"
    meta:
      source: "eth-siplab-cholz" # nest under this position (colour, meta rows)
      status: "under-review"     # optional; anonymizes double-blind venues
      selected: true             # About > Selected Publications
      resume: true               # resume.pdf (cv.pdf lists everything)
      timelined: true
      image: "assets/img/publications/icra2026.png"
      news: [...]
    links:
      - {name: "arXiv", url: "..."}
    awards:
      - {name: "Best Paper Award", organization: "...", link: "..."}

pages:                           # per-paper page bodies, keyed by id
  fwnkf: |
    ## Problem
    Markdown-ish body with MathJax.
```

Author strings are joined to APA form (`,` + final `&`) and the
sentence-case `title_apa` derives automatically, keeping
`proper_nouns` capitalized.

## `education.yaml`, `experience.yaml`, `research.yaml`, `teaching.yaml`

Same two-layer shape. `education` uses `degree` / `institution` (plus
optional `thesis`); the other three use `position` / `company`.
`experience` is salaried positions and internships, `research` is
unpaid research projects. Timelined positions draw as parallel
coloured bars along the Timeline rail with exact date endpoints.

## `extracurricular.yaml`

Holds `honors` (orphan awards that attach to no entry; `timelined:
true` gives them their own Timeline row) and `skills` (a map of
category to items, rendered one bold-labelled line each).

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
  `projects/<slug>/`.
- `social_posts.yaml` - curated link-preview cards for the "Media
  Posts" section of the Blogs tab.

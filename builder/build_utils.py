"""
Shared utilities: escaping, date parsing, author highlighting, data loading.
"""

import hashlib
import re
import sys
from datetime import date, datetime
from html import escape
from pathlib import Path

import yaml

from .build_config import AUTHOR_DISPLAY_NAME, AUTHOR_NAME, AUTHOR_NAME_ALT, DATA_DIR, META_DIR


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def file_hash(path, length=8):
    """Return a short content hash for cache busting."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:length]


def esc(s):
    """HTML-escape a string."""
    if not s:
        return ""
    return escape(str(s))


def slugify(text):
    """URL slug from a title: 'Bucketed Ranking Loss' -> 'bucketed-ranking-loss'."""
    s = re.sub(r"[^\w\s-]", "", str(text).lower())
    return re.sub(r"[\s_-]+", "-", s).strip("-")


def highlight_author(text):
    """Bold the author's name in a text string. Input should already be escaped."""
    pattern = re.escape(esc(AUTHOR_NAME)) + "|" + re.escape(esc(AUTHOR_NAME_ALT))
    return _linkify_authors_html(re.sub(pattern, f"<strong>{esc(AUTHOR_NAME)}</strong>", text))


def highlight_author_span(text):
    """Wrap author name in span.author-me. Input should already be escaped."""
    pattern = re.escape(esc(AUTHOR_NAME)) + "|" + re.escape(esc(AUTHOR_NAME_ALT))
    return _linkify_authors_html(
        re.sub(pattern, f'<span class="author-me">{esc(AUTHOR_NAME)}</span>', text))


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    "January": 1, "February": 2, "March": 3, "April": 4,
    "June": 6, "July": 7, "August": 8, "September": 9,
    "October": 10, "November": 11, "December": 12,
    "Spring": 3, "Fall": 9,
}

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

SHORT_MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def format_date(value, short=False, day=True):
    """Render an ISO (full or partial) date as human-readable text.

    Defaults to long month names ('March 2025'); set short=True for
    three-letter month abbreviations ('Mar 2025'). Set day=False to drop
    the day component from full dates ('Mar 12, 2025' -> 'Mar 2025').
    'Present' is normalized; unknown strings (e.g. 'Spring 2019') pass
    through.
    """
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if s.lower() == "present":
        return "Present"
    names = SHORT_MONTH_NAMES if short else MONTH_NAMES
    # Datetime "YYYY-MM-DD HH:MM(:SS)" -> "Mon D, YYYY, HH:MM"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})", s)
    if m and 1 <= int(m.group(2)) <= 12:
        base = f"{names[int(m.group(2))]} {int(m.group(3))}, {m.group(1)}"
        return f"{base}, {m.group(4)}:{m.group(5)}" if day else f"{names[int(m.group(2))]} {m.group(1)}"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m and 1 <= int(m.group(2)) <= 12:
        if not day:
            return f"{names[int(m.group(2))]} {m.group(1)}"
        return f"{names[int(m.group(2))]} {int(m.group(3))}, {m.group(1)}"
    m = re.match(r"^(\d{4})-(\d{2})$", s)
    if m and 1 <= int(m.group(2)) <= 12:
        return f"{names[int(m.group(2))]} {m.group(1)}"
    if re.match(r"^\d{4}$", s):
        return s
    return s


def parse_date(date_str):
    """Parse a date string into a datetime for sorting."""
    if not date_str:
        return datetime(1970, 1, 1)
    s = str(date_str).strip()
    if s.lower() == "present":
        return datetime.now()

    # ISO datetime "YYYY-MM-DD HH:MM(:SS)"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$", s)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                        int(m.group(4)), int(m.group(5)), int(m.group(6) or 0))

    # ISO "YYYY-MM-DD" / "YYYY-MM"
    m = re.match(r"^(\d{4})-(\d{2})(?:-(\d{2}))?$", s)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))

    # Academic-year range "YYYY-YYYY" -> sort by the end year (when awarded)
    m = re.match(r"^(\d{4})-(\d{4})$", s)
    if m:
        return datetime(int(m.group(2)), 1, 1)

    # "Mon YYYY"
    m = re.match(r"^([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        return datetime(int(m.group(2)), MONTHS.get(m.group(1), 1), 1)

    # "YYYY"
    m = re.match(r"^(\d{4})$", s)
    if m:
        return datetime(int(m.group(1)), 1, 1)

    # "DD Mon YYYY" or "DD Month YYYY"
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    return datetime(1970, 1, 1)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

YAML_FILES = [
    "bio", "education", "teaching", "experience",
    "research", "extracurricular", "publications",
    "blogs", "works", "social_posts",
]
META_FILES = ["venues", "authors", "courses", "institutions"]


def load_data():
    """Load all YAML data files from the data/ directory."""
    data = {}
    for name, path in ([(n, DATA_DIR / f"{n}.yaml") for n in YAML_FILES]
                       + [(n, META_DIR / f"{n}.yaml") for n in META_FILES]):
        try:
            with open(path) as f:
                data[name] = yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Warning: {path} not found, using empty data", file=sys.stderr)
            data[name] = {}
        except yaml.YAMLError as e:
            print(f"Error: {path} has invalid YAML: {e}", file=sys.stderr)
            sys.exit(1)
    set_author_pool((data.get("authors") or {}).get("authors") or {})
    _normalize_publications(data)
    _normalize_sections(data)
    _normalize_coursework(data)
    orgs = (data.get("institutions") or {}).get("institutions") or {}
    for h in (data.get("extracurricular") or {}).get("honors") or []:
        _normalize_award(h, orgs, "extracurricular.yaml")
        h["title"] = h.pop("name")
    return data


def _normalize_sections(data):
    """Hoist the data/meta groups of education / experience / research
    (and teaching, if it adopts the layout) into flat fields."""
    orgs = (data.get("institutions") or {}).get("institutions") or {}
    for section in ("education", "experience", "research", "teaching"):
        for item in (data.get(section) or {}).get(section) or []:
            for group in ("data", "meta"):
                g = item.pop(group, None)
                if isinstance(g, dict):
                    for k, v in g.items():
                        item.setdefault(k, v)
            _normalize_people_and_load(item, data, section)
            org = orgs.get(item.pop("org", None))
            if org is None:
                sys.exit(f"{section}.yaml: {item.get('id')}: org is not a key in meta/institutions.yaml")
            item["institution" if section == "education" else "company"] = org["name"]
            for k in ("location", "logo", "logo_link"):
                if org.get(k):
                    item.setdefault(k, org[k])
            if section == "teaching":
                _normalize_teaching(item, (data.get("courses") or {}).get("courses") or {})
            # A co-advisor folds into the advisor line everywhere.
            if item.get("co_advisor"):
                item["advisor"] = (
                    f"{item.get('advisor', '')}, Co-advisor: {item.pop('co_advisor')}".lstrip(", "))


def _months(start, end):
    """Inclusive month count between two ISO dates ('Present' is today)."""
    def ym(s):
        if str(s).lower() == "present":
            d = date.today()
            return d.year, d.month
        y, m = str(s).split("-")[:2]
        return int(y), int(m)
    (y0, m0), (y1, m1) = ym(start), ym(end)
    return (y1 - y0) * 12 + (m1 - m0) + 1


def _duration(start, end):
    n = _months(start, end)
    return f"{n} months" if n < 18 else f"{round(n / 12)} years"


def _normalize_people_and_load(item, data, section):
    """Advisor keys -> the advisor line (titles from meta/authors.yaml, a
    co-advisor appended); load / hours / remote / course -> the commitment
    line, with the duration of a finished position derived from its dates."""
    pool = (data.get("authors") or {}).get("authors") or {}

    def people(keys):
        out = []
        for k in keys:
            a = pool.get(k)
            if not a or not a.get("title"):
                sys.exit(f"{section}.yaml: {item.get('id')}: advisor {k!r} needs a key with a title in meta/authors.yaml")
            out.append(f"{a['title']} {a['name']}")
        return ", ".join(out)
    if item.get("advisors"):
        item["advisor"] = people(item.pop("advisors"))
    if item.get("co_advisors"):
        item["co_advisor"] = people(item.pop("co_advisors"))

    parts = []
    if item.pop("remote", False):
        parts.append("Remote")
    load, hours = item.pop("load", None), item.pop("hours", None)
    if load == "full-time":
        parts.append("Full-time" if not parts else "full-time")
    elif load:
        sys.exit(f"{section}.yaml: {item.get('id')}: load {load!r} is not full-time")
    if hours:
        parts.append(f"{hours} hours/week")
    course = item.pop("course", None)
    if course:
        c = ((data.get("courses") or {}).get("courses") or {}).get(course)
        if not c:
            sys.exit(f"{section}.yaml: {item.get('id')}: course {course!r} is not a key in meta/courses.yaml")
        parts.append(f"Term project ({c['code']})")
    end = item.get("end_date")
    if parts and item.get("start_date") and end and str(end).lower() != "present" and section != "teaching":
        parts.append(_duration(item["start_date"], end))
    if parts:
        item["commitment"] = ", ".join(parts)

    thesis = item.get("thesis") or {}
    if thesis.get("link"):
        item.setdefault("link", thesis["link"])

    orgs = (data.get("institutions") or {}).get("institutions") or {}
    for a in item.get("awards") or []:
        _normalize_award(a, orgs, f"{section}.yaml: {item.get('id')}")


def _normalize_award(a, orgs, where):
    """An award or honor: `org` -> organization (and logo); an ISO year
    range 2022/2023 -> the 2022-2023 the renderers print."""
    if a.get("org"):
        o = orgs.get(a.pop("org"))
        if not o:
            sys.exit(f"{where}: award org is not a key in meta/institutions.yaml")
        a["organization"] = o["name"]
        if o.get("logo"):
            a.setdefault("logo", o["logo"])
    m = re.match(r"^(\d{4})/(\d{4})$", str(a.get("date", "")))
    if m:
        a["date"] = f"{m.group(1)}-{m.group(2)}"


def _normalize_coursework(data):
    """Collect each degree's `coursework` (group -> course keys) into the
    bio-level selected_coursework (group title -> course lines) and
    resume_coursework_categories (group title -> resume area) the
    renderers read, in the order of bio.yaml coursework_groups."""
    bio = data.get("bio") or {}
    groups = bio.get("coursework_groups") or {}
    pool = (data.get("courses") or {}).get("courses") or {}
    lines = {}
    for edu in (data.get("education") or {}).get("education") or []:
        for g, keys in (edu.pop("coursework", None) or {}).items():
            if g not in groups:
                sys.exit(f"education.yaml: {edu.get('id')}: coursework group {g!r} is not in bio.yaml coursework_groups")
            for k in keys:
                c = pool.get(k)
                if not c:
                    sys.exit(f"education.yaml: {edu.get('id')}: course {k!r} is not a key in meta/courses.yaml")
                lines.setdefault(g, []).append(f"{c['name']} ([{c['code']}]({c['link']}))")
    bio["selected_coursework"] = {groups[g]["title"]: lines[g] for g in groups if g in lines}
    bio["resume_coursework_categories"] = {groups[g]["title"]: groups[g]["resume"] for g in groups if g in lines}


# A term's first and last month; fall runs into January of the next year.
_TERM_MONTHS = {"spring": ((0, 2), (0, 6)), "summer": ((0, 7), (0, 8)), "fall": ((0, 10), (1, 1))}


def _term_bounds(term):
    m = re.match(r"^(\d{4})-(spring|summer|fall)$", str(term))
    if not m:
        sys.exit(f"teaching.yaml: term {term!r} is not YYYY-spring|summer|fall")
    y = int(m.group(1))
    (dy0, m0), (dy1, m1) = _TERM_MONTHS[m.group(2)]
    return f"{y + dy0}-{m0:02d}", f"{y + dy1}-{m1:02d}"


def _term_label(term):
    year, season = str(term).split("-")
    return f"{season.capitalize()} {year}"


def _normalize_teaching(item, pool):
    """Resolve `courses: [{course, terms}]` against meta/courses.yaml into
    the course lines the renderers print (newest term first), and derive
    start_date / end_date (ISO) and date_label (a term range) from the
    terms; the end is Present while the last term is still running."""
    rows = []
    for c in item.pop("courses", None) or []:
        info = pool.get(c.get("course"))
        if not info:
            sys.exit(f"teaching.yaml: {item.get('id')}: course {c.get('course')!r} is not a key in meta/courses.yaml")
        terms = sorted(c.get("terms") or [], key=lambda t: _term_bounds(t)[0])
        rows.append((_term_bounds(terms[-1])[0], info, terms))
    rows.sort(key=lambda r: r[0], reverse=True)
    item["bullets"] = [f"[{i['code']}]({i['link']}) - {i['name']} ({', '.join(_term_label(t) for t in ts)})"
                       for _, i, ts in rows]
    every = sorted({t for _, _, ts in rows for t in ts}, key=lambda t: _term_bounds(t)[0])
    first, last = every[0], every[-1]
    item["start_date"] = _term_bounds(first)[0]
    running = _term_bounds(last)[1] >= date.today().strftime("%Y-%m")
    item["end_date"] = "Present" if running else _term_bounds(last)[1]
    item["date_label"] = f"{_term_label(first)} - {'Present' if running else _term_label(last)}"


def _sentence_case(title, proper):
    """APA sentence case: lowercase everything except the first word, the
    word after a colon, acronyms / mixed-case words (EEG, CoFINN), and
    the proper nouns listed in publications.yaml."""
    out, cap_next = [], True
    for tok in str(title).split(" "):
        parts = []
        for part in tok.split("-"):
            core = re.sub(r"[^\w]", "", part)
            if core in proper or any(c.isupper() for c in core[1:]):
                parts.append(part)
            else:
                parts.append(part.lower())
        w = "-".join(parts)
        if cap_next and w:
            w = w[0].upper() + w[1:]
        cap_next = w.endswith(":")
        out.append(w)
    return " ".join(out)


def _join_authors(names):
    """["A, B.", "C, D."] -> "A, B., & C, D." (APA ampersand form)."""
    names = [str(n) for n in names]
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + ", & " + names[-1]


PAPER_KINDS = {"article", "proceedings", "chapter", "thesis"}
PAPER_STAGES = {"published", "preprint", "submitted"}
PAPER_SHOW = {"front", "resume", "timeline"}


def _normalize_publications(data):
    """Expand the publication grammar (see the header of
    data/publications.yaml) into the flat fields the renderers consume:
    hoist `ref`, turn `show` into the front / selected / resume /
    timelined flags, resolve author keys against meta/authors.yaml and
    join them, derive the sentence-case APA title, and resolve `venue`
    (or, for a submitted paper, `target`) against meta/venues.yaml into
    venue / venue_short / venue_link / venue_prefix / venue_detail."""
    keys = (data.get("authors") or {}).get("authors") or {}
    pool = (data.get("venues") or {}).get("venues") or {}
    proper = set((data.get("publications") or {}).get("proper_nouns") or [])
    pages = (data.get("publications") or {}).get("pages") or {}
    for paper in (data.get("publications") or {}).get("papers") or []:
        page = pages.get(paper.get("id")) or pages.get(paper.get("title"))
        if page:
            paper.setdefault("body", page)
        elif paper.get("abstract"):  # legacy inline field
            paper.setdefault("body", paper["abstract"])
        pid = paper.get("id")
        for k, v in (paper.pop("ref", None) or {}).items():
            paper.setdefault(k, v)
        if paper.get("kind") not in PAPER_KINDS:
            sys.exit(f"publications.yaml: {pid}: kind {paper.get('kind')!r} not in {sorted(PAPER_KINDS)}")
        paper.setdefault("stage", "published")
        if paper["stage"] not in PAPER_STAGES:
            sys.exit(f"publications.yaml: {pid}: stage {paper['stage']!r} not in {sorted(PAPER_STAGES)}")
        show = paper.pop("show", None)
        if not isinstance(show, list) or set(show) - PAPER_SHOW:
            sys.exit(f"publications.yaml: {pid}: show {show!r} must be a list from {sorted(PAPER_SHOW)}")
        paper["front"] = "front" in show
        paper["resume"] = "resume" in show
        paper["timelined"] = "timeline" in show

        names = []
        for a in paper.get("authors") or []:
            if "," in a:
                names.append(a)
            elif a in keys:
                names.append(keys[a]["apa"])
            else:
                sys.exit(f"publications.yaml: {pid}: author {a!r} is neither an APA string nor a key in authors.yaml")
        paper["authors"] = _join_authors(names)
        if paper.get("title"):
            paper.setdefault("title_apa", _sentence_case(paper["title"], proper))

        if paper["stage"] == "submitted" and paper.get("venue"):
            sys.exit(f"publications.yaml: {pid}: a submitted paper names its target, not a venue")
        # A submitted paper is listed under its target; any other paper
        # under the venue it appeared in.
        raw = paper.get("target") if paper["stage"] == "submitted" else paper.get("venue")
        spec = raw if isinstance(raw, dict) else {}
        key = spec.get("id") if spec else raw
        entry = pool.get(key) if isinstance(key, str) else None
        for k, v in (("venue or target", key), ("target", paper.get("target"))):
            if isinstance(v, str) and v not in pool:
                sys.exit(f"publications.yaml: {pid}: {k} {v!r} is not a key in venues.yaml")

        name = spec.get("name") or (entry or {}).get("name") or (key if isinstance(key, str) else "")
        if spec.get("volume"):
            name = f"{name}, {spec['volume']}"
        if name:
            paper["venue"] = name
        if spec.get("prefix"):
            paper["venue_prefix"] = spec["prefix"]
        if spec.get("detail"):
            paper["venue_detail"] = spec["detail"]
        link = spec.get("link") or (entry or {}).get("link")
        if link:
            paper.setdefault("venue_link", link)
        if (entry or {}).get("double_blind"):
            paper["venue_double_blind"] = True
        if "selected" not in paper:
            paper["selected"] = bool((entry or {}).get("selected"))

        if not paper.get("venue_short"):
            if spec.get("short"):
                year = str(paper.get("date", ""))[:4]
                paper["venue_short"] = f"{spec['short']} {year}" if year else spec["short"]
            elif entry and entry.get("short"):
                yy = str(paper.get("date", ""))[:4][-2:]
                if entry.get("short_year") is False or not yy:
                    paper["venue_short"] = entry["short"]
                else:
                    paper["venue_short"] = f"{entry['short']}'{yy}"


# ---------------------------------------------------------------------------
# Author pool - names in `authors` strings that should carry links
# ---------------------------------------------------------------------------

_AUTHOR_POOL = {}


def set_author_pool(pool):
    """Index the pool by APA form; an author's link is the first of site,
    scholar, github."""
    global _AUTHOR_POOL
    _AUTHOR_POOL = {}
    for v in pool.values():
        link = v.get("site") or v.get("scholar") or v.get("github")
        if link:
            _AUTHOR_POOL[v["apa"]] = {**v, "link": link}


def get_author_pool():
    return _AUTHOR_POOL


def get_name_links():
    """Full name -> link, for advisor strings ("Prof. Dr. Sinan Kalkan")."""
    return {v["name"]: v["link"] for v in _AUTHOR_POOL.values() if v.get("name")}


def linkify_names_html(html):
    """Wrap pool full names in plain anchors. Input is already-escaped
    HTML that contains no anchors of its own."""
    for name, url in get_name_links().items():
        needle = esc(name)
        if needle in html:
            html = html.replace(
                needle,
                f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{needle}</a>')
    return html


def _linkify_authors_html(text):
    """Wrap pool author names (already-escaped text) in understated links."""
    for apa, info in _AUTHOR_POOL.items():
        needle = esc(apa)
        if needle in text:
            text = text.replace(
                needle,
                f'<a href="{esc(info["link"])}" class="author-link" '
                f'target="_blank" rel="noopener noreferrer">{needle}</a>',
            )
    return text

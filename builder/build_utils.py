"""
Shared utilities: escaping, date parsing, author highlighting, data loading.
"""

import hashlib
import re
import sys
from datetime import datetime
from html import escape
from pathlib import Path

import yaml

from .build_config import AUTHOR_DISPLAY_NAME, AUTHOR_NAME, AUTHOR_NAME_ALT, DATA_DIR


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
    "research", "extracurricular", "news", "publications",
    "blogs", "works", "social_posts", "venues", "authors",
]


def load_data():
    """Load all YAML data files from the data/ directory."""
    data = {}
    for name in YAML_FILES:
        path = DATA_DIR / f"{name}.yaml"
        try:
            with open(path) as f:
                data[name] = yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Warning: {path} not found, using empty data", file=sys.stderr)
            data[name] = {}
        except yaml.YAMLError as e:
            print(f"Error: {path} has invalid YAML: {e}", file=sys.stderr)
            sys.exit(1)
    _normalize_publications(data)
    _normalize_sections(data)
    set_author_pool((data.get("authors") or {}).get("authors") or {})
    return data


def _normalize_sections(data):
    """Hoist the data/meta groups of education / experience / research
    (and teaching, if it adopts the layout) into flat fields."""
    for section in ("education", "experience", "research", "teaching"):
        for item in (data.get(section) or {}).get(section) or []:
            for group in ("data", "meta"):
                g = item.pop(group, None)
                if isinstance(g, dict):
                    for k, v in g.items():
                        item.setdefault(k, v)


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


def _normalize_publications(data):
    """Expand the two-layer publication schema into the flat fields the
    renderers consume: hoist `meta` keys, join the author list, derive
    the sentence-case APA title, and resolve `venue` (a pool key, or a
    dict of id/name/volume/detail/prefix/short/link) against
    data/venues.yaml into venue / venue_short / venue_link /
    venue_prefix / venue_detail."""
    pool = (data.get("venues") or {}).get("venues") or {}
    proper = set((data.get("publications") or {}).get("proper_nouns") or [])
    pages = (data.get("publications") or {}).get("pages") or {}
    for paper in (data.get("publications") or {}).get("papers") or []:
        page = pages.get(paper.get("id")) or pages.get(paper.get("title"))
        if page:
            paper.setdefault("body", page)
        elif paper.get("abstract"):  # legacy inline field
            paper.setdefault("body", paper["abstract"])
        record = paper.pop("data", None)
        if isinstance(record, dict):
            for k, v in record.items():
                paper.setdefault(k, v)
        authors = paper.get("authors")
        if isinstance(authors, list):
            paper["authors"] = _join_authors(authors)
        elif isinstance(authors, str) and ";" in authors:
            paper["authors"] = _join_authors([a.strip() for a in authors.split(";") if a.strip()])
        if paper.get("title"):
            paper.setdefault("title_apa", _sentence_case(paper["title"], proper))
        meta = paper.pop("meta", None)
        if isinstance(meta, dict):
            for k, v in meta.items():
                paper.setdefault(k, v)

        raw = paper.get("venue")
        spec = raw if isinstance(raw, dict) else {}
        key = spec.get("id") if spec else raw
        entry = pool.get(key) if isinstance(key, str) else None

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
        if "selected" not in paper and (entry or {}).get("selected"):
            paper["selected"] = True

        if not paper.get("venue_short"):
            if spec.get("short"):
                paper["venue_short"] = spec["short"]
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
    global _AUTHOR_POOL
    _AUTHOR_POOL = {k: v for k, v in pool.items() if isinstance(v, dict) and v.get("link")}


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

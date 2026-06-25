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
    return re.sub(pattern, f"<strong>{esc(AUTHOR_NAME)}</strong>", text)


def highlight_author_span(text):
    """Wrap author name in span.author-me. Input should already be escaped."""
    pattern = re.escape(esc(AUTHOR_NAME)) + "|" + re.escape(esc(AUTHOR_NAME_ALT))
    return re.sub(pattern, f'<span class="author-me">{esc(AUTHOR_NAME)}</span>', text)


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
    "blogs", "works", "social_posts",
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
    return data

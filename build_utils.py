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

from build_config import AUTHOR_DISPLAY_NAME, AUTHOR_NAME, AUTHOR_NAME_ALT, DATA_DIR


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


def parse_date(date_str):
    """Parse a date string into a datetime for sorting."""
    if not date_str:
        return datetime(1970, 1, 1)
    s = str(date_str).strip()
    if s.lower() == "present":
        return datetime.now()

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
    "blogs", "works",
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

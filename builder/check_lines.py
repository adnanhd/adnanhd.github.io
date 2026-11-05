"""Warn when a former bullet line wraps, or leaves a gap, in cv.pdf or resume.pdf.

Every `bullets:` line of experience.yaml and research.yaml is one
sentence that must fit on one printed line. After the PDFs are built,
each line's plain text is looked up in the PDF's text (pdftotext -raw,
one entry per printed line): found whole on one line, it fits; found only
by its opening words, it wraps and a warning names it. A line that fits
but spans less than MIN_FILL of its column (from pdftotext -bbox-layout,
the column's right edge being the page's rightmost text) leaves a gap and
is named too. A line a PDF does not print is skipped for that PDF. Runs
from the build; warns, never fails.
"""
import re
import shutil
import subprocess
import sys

from xml.etree import ElementTree

from .build_config import CV_OUTPUT_PATH, RESUME_OUTPUT_PATH

MIN_FILL = 0.88

_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_FOLD = str.maketrans({"–": "-", "—": "-", "’": "'", "‘": "'",
                       "“": '"', "”": '"', "ﬁ": "fi", "ﬂ": "fl",
                       "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"})


def _norm(text):
    text = _MD_LINK.sub(r"\1", str(text)).replace("**", "")
    return re.sub(r"\s+", " ", text.translate(_FOLD)).strip()


def _pdf_lines(path):
    out = subprocess.run(["pdftotext", "-raw", str(path), "-"],
                         capture_output=True, text=True, check=False).stdout
    return [_norm(l) for l in out.splitlines()]


def _pdf_boxes(path):
    """[(text, xMin, xMax)] per printed line, and the page's right text edge."""
    out = subprocess.run(["pdftotext", "-bbox-layout", str(path), "-"],
                         capture_output=True, text=True, check=False).stdout
    out = re.sub(r"<!DOCTYPE[^>]*>", "", out).replace('xmlns="http://www.w3.org/1999/xhtml"', "")
    boxes = []
    for line in ElementTree.fromstring(out).iter("line"):
        text = _norm(" ".join(w.text or "" for w in line.iter("word")))
        boxes.append((text, float(line.get("xMin")), float(line.get("xMax"))))
    return boxes, max(x2 for _, _, x2 in boxes)


def bullet_lines(data):
    """(entry id, text) for every bullet of experience and research."""
    for section in ("experience", "research"):
        for item in (data.get(section) or {}).get(section) or []:
            for b in item.get("bullets") or []:
                yield item.get("id", section), b


def wrapped(data):
    """[(pdf name, entry id, text)] for each bullet that wraps."""
    if not shutil.which("pdftotext"):
        print("check_lines: pdftotext not found; bullet wrapping not checked", file=sys.stderr)
        return []
    bad = []
    for pdf in (CV_OUTPUT_PATH, RESUME_OUTPUT_PATH):
        if not pdf.exists():
            continue
        lines = _pdf_lines(pdf)
        for eid, text in bullet_lines(data):
            t = _norm(text)
            if any(t in l for l in lines):
                continue
            head = t[:30]
            if any(head in l for l in lines):
                bad.append((pdf.name, eid, t))
    return bad


def short(data):
    """[(pdf name, entry id, fill, text)] for each one-line bullet below MIN_FILL."""
    if not shutil.which("pdftotext"):
        return []
    bad = []
    for pdf in (CV_OUTPUT_PATH, RESUME_OUTPUT_PATH):
        if not pdf.exists():
            continue
        boxes, right = _pdf_boxes(pdf)
        for eid, text in bullet_lines(data):
            t = _norm(text)
            hit = [(x1, x2) for l, x1, x2 in boxes if t in l]
            if hit:
                x1, x2 = hit[0]
                fill = (x2 - x1) / (right - x1)
                if fill < MIN_FILL:
                    bad.append((pdf.name, eid, fill, t))
    return bad


def warn(data):
    for pdf, eid, text in wrapped(data):
        print(f"Warning: {pdf}: bullet of {eid} wraps: {text}", file=sys.stderr)
    for pdf, eid, fill, text in short(data):
        print(f"Warning: {pdf}: bullet of {eid} fills {fill:.0%} of its line: {text}", file=sys.stderr)

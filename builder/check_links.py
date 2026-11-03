"""Check every URL in data/ and meta/: python -m builder.check_links

Collects each http(s) URL from the YAML files (url fields, pool links,
markdown links inside prose) and requests it: HEAD first, GET when HEAD
is refused. Prints only the failures, with the file and field they come
from. A manual tool; neither the build nor the pre-commit hook runs it.
"""
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import yaml

from .build_config import DATA_DIR, META_DIR

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MD_LINK = re.compile(r"\]\((https?://[^)\s]+)\)")
BARE = re.compile(r"^https?://\S+$")
TIMEOUT = 10
WORKERS = 8


def collect():
    """{url: [where, ...]} over every data/ and meta/ YAML file."""
    found = {}

    def walk(node, where):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{where}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                label = (v.get("id") or v.get("name")) if isinstance(v, dict) else None
                walk(v, f"{where}[{label or i}]")
        elif isinstance(node, str):
            urls = [node] if BARE.match(node.strip()) else MD_LINK.findall(node)
            for u in urls:
                found.setdefault(u.strip(), []).append(where)

    for d in (DATA_DIR, META_DIR):
        for path in sorted(d.glob("*.yaml")):
            with open(path) as f:
                walk(yaml.safe_load(f) or {}, f"{d.name}/{path.name}")
    return found


def probe(url):
    """None when the URL answers below 400, else a short reason."""
    last = None
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                if r.status < 400:
                    return None
                last = f"HTTP {r.status}"
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
        except Exception as e:  # DNS, TLS, timeout
            last = type(e).__name__ + (f": {e.reason}" if hasattr(e, "reason") else "")
    return last


def main():
    found = collect()
    with ThreadPoolExecutor(WORKERS) as pool:
        results = dict(zip(found, pool.map(probe, found)))
    bad = {u: r for u, r in results.items() if r}
    for u, reason in sorted(bad.items()):
        print(f"{reason}  {u}")
        for where in found[u]:
            print(f"    {where}")
    print(f"{len(bad)} of {len(found)} URLs failed", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

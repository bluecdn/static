#!/usr/bin/env python3
"""Generate 3 new HTML pages for static.img.et / bluecdn.com / tujing.io,
based on lanting.html as the template."""
import pathlib

HTML_DIR = pathlib.Path("/Users/gentpan/projects/static.r2/_html")
TPL = (HTML_DIR / "lanting.html").read_text()

# Source brand strings in the template, in replacement order
# (longest/most-specific first to avoid clobbering).
ORIG_HOST  = "static.lanting.ai"
ORIG_ROOT  = "lanting.ai"
ORIG_TITLE = "Lanting"
ORIG_LOWER = "lanting"

SITES = [
    {"file": "imget.html",   "host": "static.img.et",      "root": "img.et",      "title": "Imget",   "lower": "imget"},
    {"file": "bluecdn.html", "host": "static.bluecdn.com", "root": "bluecdn.com", "title": "BlueCDN", "lower": "bluecdn"},
    {"file": "tujing.html",  "host": "static.tujing.io",   "root": "tujing.io",   "title": "Tujing",  "lower": "tujing"},
]

for s in SITES:
    out = TPL
    out = out.replace(ORIG_HOST,  s["host"])   # 1) full host (longest)
    out = out.replace(ORIG_ROOT,  s["root"])   # 2) bare domain (audit url, footer href)
    out = out.replace(ORIG_TITLE, s["title"])  # 3) Title Case (header link text, title)
    out = out.replace(ORIG_LOWER, s["lower"])  # 4) lowercase (description, h1, previews)
    path = HTML_DIR / s["file"]
    path.write_text(out)
    # sanity check: should have zero leftover original brand strings
    leftover = sum(s in out for s in [ORIG_HOST, ORIG_ROOT, ORIG_TITLE, ORIG_LOWER])
    print(f"  {s['file']:<15} host={s['host']:<25} leftover={leftover}  bytes={len(out):,}")

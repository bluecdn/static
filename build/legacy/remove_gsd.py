#!/usr/bin/env python3
"""Remove Google Sans Display references from the 4 HTML pages."""
import re, pathlib

HTML_DIR = pathlib.Path("/Users/gentpan/projects/static.r2/_html")
PAGES = ["index.html", "lanting.html", "giantaccel.html", "litepic.html"]

# 1) Head link line  (with surrounding newline)
LINK_RE = re.compile(
    r'\n<link rel="stylesheet" href="https://[^"]+/fonts/google-sans-display/result\.css">',
)

# 2) The whole <div class="res">…Google Sans Display…</div> card incl. trailing blank
CARD_RE = re.compile(
    r'\n      <div class="res">\s*\n'
    r'\s*<div class="res-name">Google Sans Display.*?'
    r'</div>\s*\n\s*</div>\s*\n',
    re.S,
)

for fname in PAGES:
    p = HTML_DIR / fname
    src = p.read_text()
    new = LINK_RE.sub("", src, count=1)
    new = CARD_RE.sub("\n", new, count=1)
    if new == src:
        print(f"  {fname}: no change (already removed?)")
        continue
    p.write_text(new)
    removed_bytes = len(src) - len(new)
    print(f"  {fname}: removed {removed_bytes} bytes (link + card)")

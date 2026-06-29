#!/usr/bin/env python3
import re, os, urllib.request, sys, pathlib

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

FONTS = [
    ("Inter",            "inter",            "wght@400;500;700"),
    ("Roboto",           "roboto",           "wght@400;500;700"),
    ("Cabin",            "cabin",            "wght@400;500;700"),
    ("Sora",             "sora",             "wght@400;500;700"),
    ("Google Sans",      "google-sans",      "wght@400;500;700"),
    ("Ubuntu",           "ubuntu",           "wght@400;500;700"),
    ("Google Sans Code", "google-sans-code", "wght@400;700"),
]
KEEP = {"latin", "latin-ext"}

BASE = pathlib.Path("/Users/gentpan/projects/static.r2/_fonts")
BASE.mkdir(exist_ok=True)

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

# Match: /* subset */\n@font-face { ... }
BLOCK_RE = re.compile(r"/\*\s*([^*\s][^*]*?)\s*\*/\s*@font-face\s*\{[^}]*\}", re.S)

for family, dirname, axis in FONTS:
    out = BASE / dirname
    out.mkdir(exist_ok=True)
    url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}:{axis}&display=swap"
    css = fetch(url, {"User-Agent": UA}).decode("utf-8")

    kept_blocks = []
    for m in BLOCK_RE.finditer(css):
        subset = m.group(1).strip()
        if subset in KEEP:
            kept_blocks.append(m.group(0))

    new_css = "\n\n".join(kept_blocks) + "\n"

    urls = sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", new_css)))
    for u in urls:
        fname = u.rsplit("/", 1)[-1]
        local = out / fname
        if not local.exists():
            local.write_bytes(fetch(u))
        new_css = new_css.replace(u, f"./{fname}")

    (out / "result.css").write_text(new_css)
    sz_total = sum(p.stat().st_size for p in out.iterdir())
    print(f"{family:<8} subsets={len(kept_blocks):2d} woff2={len(urls):2d} total={sz_total/1024:7.1f}KB -> {out}")

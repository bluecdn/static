#!/usr/bin/env python3
"""Patch 4 HTML files: add 5 new font <link>s and 5 font cards.
Each page uses its own host (self-host pattern)."""
import re, pathlib

HTML_DIR = pathlib.Path("/Users/gentpan/projects/static.r2/_html")

# page -> host
PAGES = {
    "index.html":      "static.utterlog.com",
    "lanting.html":    "static.lanting.ai",
    "giantaccel.html": "static.giantaccel.com",
    "litepic.html":    "static.litepic.io",
}

# (dir, family, weights-desc, purpose-desc)
NEW_FONTS = [
    ("inter",       "Inter",       "VF 400..700 · Latin / Lat-Ext · 现代正文"),
    ("roboto",      "Roboto",      "VF 400..700 · Latin / Lat-Ext · 通用 UI"),
    ("cabin",       "Cabin",       "VF 400..700 · Latin / Lat-Ext · 圆润标题"),
    ("sora",        "Sora",        "VF 400..700 · Latin / Lat-Ext · 几何无衬线"),
    ("google-sans", "Google Sans", "400 / 500 / 700 · Latin / Lat-Ext · 品牌正文"),
]
PREVIEW_TEXT = "The quick brown fox jumps over the lazy dog"

# anchor to find for insertion
HEAD_ANCHOR = "google-sans-display/result.css\">"   # last existing font link in head
BODY_ANCHOR_RE = re.compile(
    r"(<div class=\"res\">\s*\n"
    r"\s*<div class=\"res-name\">Google Sans Display.*?"
    r"</div>\s*\n\s*</div>)\s*\n",
    re.S,
)

def build_head_links(host):
    lines = [
        f'<link rel="stylesheet" href="https://{host}/fonts/{d}/result.css">'
        for d, _, _ in NEW_FONTS
    ]
    return "\n".join(lines)

def build_body_card(host, dirname, family, desc):
    url = f"https://{host}/fonts/{dirname}/result.css"
    html_snippet = f'<link rel="stylesheet" href="{url}">'
    # css family-name uses quotes; for the data-copy attr we use single quotes outside
    # so embedded must be double quotes -- matches the existing style
    return (
        '      <div class="res">\n'
        f'        <div class="res-name">{family} <span class="sub">{desc}</span></div>\n'
        f'        <div class="res-url">{url}</div>\n'
        f'        <div class="copy-actions"><button class="copy-btn copy-icon" data-copy=\'{url}\' title="复制直链"><i class="fa-light fa-link"></i></button><button class="copy-btn copy-icon" data-copy=\'{html_snippet}\' title="复制 HTML 代码"><i class="fa-light fa-code"></i></button></div>\n'
        f'        <div class="res-preview" style="font-family: \'{family}\', sans-serif; font-size: 28px;">{PREVIEW_TEXT}</div>\n'
        '      </div>'
    )

def patch(path, host):
    src = path.read_text()

    # 1) Insert head <link>s right after the google-sans-display line
    head_block = build_head_links(host)
    new_anchor = f'google-sans-display/result.css">\n{head_block}'
    if HEAD_ANCHOR not in src:
        raise RuntimeError(f"{path.name}: head anchor not found")
    if "fonts/inter/result.css" in src:
        print(f"  {path.name}: already patched, skipping")
        return None
    src = src.replace(HEAD_ANCHOR, new_anchor, 1)

    # 2) Insert cards after the Google Sans Display card
    body_cards = "\n\n".join(build_body_card(host, d, f, desc) for d, f, desc in NEW_FONTS)
    m = BODY_ANCHOR_RE.search(src)
    if not m:
        raise RuntimeError(f"{path.name}: body anchor not found")
    end = m.end()
    src = src[:end] + "\n" + body_cards + "\n\n" + src[end:]

    return src

for fname, host in PAGES.items():
    p = HTML_DIR / fname
    new = patch(p, host)
    if new is not None:
        p.write_text(new)
        print(f"  {fname}: patched (host={host}, {len(new):,} bytes)")

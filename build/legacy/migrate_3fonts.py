#!/usr/bin/env python3
"""Migrate Ubuntu / Google Sans Code / PaperMono in the 4 HTML pages
from inline @font-face + woff2 direct refs → result.css link style."""
import re, pathlib

HTML_DIR = pathlib.Path("/Users/gentpan/projects/static.r2/_html")
PAGES = {
    "index.html":      "static.utterlog.com",
    "litepic.html":    "static.litepic.io",
    "giantaccel.html": "static.giantaccel.com",
    "bluecdn.html":    "static.bluecdn.com",
}

# (dirname, family, desc, preview_style_suffix)
NEW = [
    ("ubuntu",           "Ubuntu",           "400 / 500 / 700 · Latin / Lat-Ext · UI 正文",  "sans-serif"),
    ("google-sans-code", "Google Sans Code", "VF 400..700 · Latin / Lat-Ext · 等宽代码",     "monospace"),
    ("papermono",        "PaperMono",        "400 · 等宽代码 · 可选备用",                    "monospace"),
]
PREVIEW = "Always believe that something wonderful is about to happen"

# Style-block inline @font-face lines to remove (these are stable across pages)
INLINE_TO_REMOVE = [
    '  @font-face{font-family:"Ubuntu";src:url("/fonts/ubuntu-400.woff2") format("woff2");font-weight:400;font-style:normal;font-display:swap}\n',
    '  @font-face{font-family:"Ubuntu";src:url("/fonts/ubuntu-500.woff2") format("woff2");font-weight:500;font-style:normal;font-display:swap}\n',
    '  @font-face{font-family:"Ubuntu";src:url("/fonts/ubuntu-700.woff2") format("woff2");font-weight:700;font-style:normal;font-display:swap}\n',
    '  @font-face{font-family:"Google Sans Code";src:url("/fonts/google-sans-code-400.woff2") format("woff2");font-weight:400;font-style:normal;font-display:swap}\n',
    '  @font-face{font-family:"Google Sans Code";src:url("/fonts/google-sans-code-700.woff2") format("woff2");font-weight:700;font-style:normal;font-display:swap}\n',
    '  @font-face{font-family:"PaperMono";src:url("/fonts/PaperMono-Regular.woff2") format("woff2");font-weight:400;font-style:normal;font-display:swap}\n',
]

# anchor to insert head links after (the fontawesome line, host-specific)
def head_links(host):
    return "\n".join(
        f'<link rel="stylesheet" href="https://{host}/fonts/{d}/result.css">'
        for d, _, _, _ in NEW
    )

def make_card(host, dirname, family, desc, preview_suffix):
    url = f"https://{host}/fonts/{dirname}/result.css"
    return (
        '      <div class="res">\n'
        f'        <div class="res-name">{family} <span class="sub">{desc}</span></div>\n'
        f'        <div class="res-url">{url}</div>\n'
        f'        <div class="copy-actions"><button class="copy-btn copy-icon" data-copy=\'{url}\' title="复制直链"><i class="fa-light fa-link"></i></button><button class="copy-btn copy-icon" data-copy=\'<link rel="stylesheet" href="{url}">\' title="复制 HTML 代码"><i class="fa-light fa-code"></i></button></div>\n'
        f'        <div class="res-preview" style="font-family: \'{family}\', {preview_suffix};">{PREVIEW}</div>\n'
        '      </div>'
    )

def replace_card(src, family, new_card_html):
    """Find <div class='res'>…<div class='res-name'>FAMILY <span>…</span></div>…</div></div> block, replace whole."""
    marker = f'<div class="res-name">{family} <span class="sub">'
    pos = src.find(marker)
    if pos < 0:
        return src, False
    start = src.rfind('<div class="res">', 0, pos)
    # find double </div> (res-preview close + res close)
    end_m = re.compile(r'</div>\s*\n\s*</div>').search(src, pos)
    if not end_m:
        return src, False
    end = end_m.end()
    # preserve leading whitespace on the <div class="res"> line
    line_start = src.rfind('\n', 0, start) + 1
    return src[:line_start] + new_card_html + src[end:], True

for fname, host in PAGES.items():
    p = HTML_DIR / fname
    src = p.read_text()
    new = src
    changes = []

    # 1) Head: insert 3 link lines after the fontawesome line (host-specific)
    fa_line = f'<link rel="stylesheet" href="https://{host}/libs/fontawesome/7.2.0/css/all.min.css">'
    if fa_line in new and f'/fonts/ubuntu/result.css' not in new:
        replacement = fa_line + "\n" + head_links(host)
        new = new.replace(fa_line, replacement, 1)
        changes.append("head+3links")

    # 2) Style: remove the 6 inline @font-face lines
    removed = 0
    for line in INLINE_TO_REMOVE:
        if line in new:
            new = new.replace(line, "", 1)
            removed += 1
    if removed:
        changes.append(f"inline-rm={removed}")

    # 3) Body cards: replace 3 cards
    for dirname, family, desc, preview_suffix in NEW:
        card = make_card(host, dirname, family, desc, preview_suffix)
        new, ok = replace_card(new, family, card)
        if ok:
            changes.append(f"card:{family}")

    p.write_text(new)
    print(f"  {fname}: {', '.join(changes)}  ({len(src):,} → {len(new):,} bytes)")

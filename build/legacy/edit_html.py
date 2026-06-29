#!/usr/bin/env python3
"""Apply 3 edits to the 4 HTML pages:
1. remove the '推荐:全部一行接入' preview block (only contains fontawesome).
2. unify all Latin .res-preview text -> 'Always believe …'
3. unify all CJK .res-preview text -> '永远相信美好的事情即将发生'
"""
import re, pathlib

HTML_DIR = pathlib.Path("/Users/gentpan/projects/static.r2/_html")
PAGES = ["index.html", "litepic.html", "giantaccel.html", "bluecdn.html"]

EN = "Always believe that something wonderful is about to happen"
ZH = "永远相信美好的事情即将发生"

# (1) Remove the whole <div class="preview">…</div> block that contains 推荐：全部一行接入
PREVIEW_BLOCK_RE = re.compile(
    r'\n\s*<div class="preview">\s*\n'
    r'.*?推荐：全部一行接入.*?'
    r'</div>\s*\n',
    re.S,
)

# (2/3) For every <div class="res-preview" style="…">CONTENT</div>, swap content based on language.
PREVIEW_RE = re.compile(
    r'(<div class="res-preview" style="[^"]*">)([^<]*)(</div>)',
)

CJK_RE = re.compile(r'[㐀-鿿豈-﫿＀-￯　-〿]')

def swap_preview(m):
    open_tag, content, close_tag = m.group(1), m.group(2), m.group(3)
    new = ZH if CJK_RE.search(content) else EN
    return open_tag + new + close_tag

for fname in PAGES:
    p = HTML_DIR / fname
    src = p.read_text()
    new = src

    # 1) preview block
    new, n1 = PREVIEW_BLOCK_RE.subn("\n", new, count=1)

    # 2/3) unify previews
    new, n2 = PREVIEW_RE.subn(swap_preview, new)

    p.write_text(new)
    print(f"  {fname}: removed preview-blocks={n1}, swapped res-previews={n2}, bytes {len(src):,} -> {len(new):,}")

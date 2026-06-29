#!/usr/bin/env python3
"""Fix the broken HTML: remove the 4-line orphan tail left after the earlier bad regex."""
import re, pathlib

HTML_DIR = pathlib.Path("/Users/gentpan/projects/static.r2/_html")
PAGES = ["index.html", "litepic.html", "giantaccel.html", "bluecdn.html"]

# After the res-list closing </div>, the broken delete left this orphan tail:
#   <div class="copy-actions">…</div>
#   </div>
#   <pre><code>…</code></pre>
#   </div>
# Match the res-list close + the 4 orphan lines; keep the res-list close.
ORPHAN_RE = re.compile(
    r'(\n\s*</div>\s*\n)'                                 # group 1: res-list close
    r'\s*<div class="copy-actions">[^\n]*</div>\s*\n'     # orphan: copy-actions
    r'\s*</div>\s*\n'                                     # orphan: stray </div>
    r'\s*<pre><code>[^\n]*</code></pre>\s*\n'             # orphan: stray <pre>
    r'\s*</div>\s*\n'                                     # orphan: stray </div>
)

for fname in PAGES:
    p = HTML_DIR / fname
    src = p.read_text()
    new, n = ORPHAN_RE.subn(r'\1', src, count=1)
    if n == 0:
        print(f"  {fname}: no orphan found (already clean?)")
        continue
    p.write_text(new)
    print(f"  {fname}: fixed (-{len(src)-len(new)} bytes)")

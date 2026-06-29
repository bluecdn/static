#!/usr/bin/env python3
"""Build 100 EN fonts from Google Fonts into the new flat scheme:
   /fonts/{slug}.css  +  /fonts/{slug}/*.woff2  (css url -> ./{slug}/file.woff2)
Reads /root/fonts.json. Run on the SV box (can reach Google Fonts)."""
import json, re, os, pathlib, urllib.request
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
KEEP = {"latin", "latin-ext"}
OUT = pathlib.Path("/www/sites/static.bluecdn.com/fonts")
man = json.load(open("/root/fonts.json"))
en = [f for f in man["fonts"] if f["lang"] == "latin" and f["source"] == "google"]
BLOCK = re.compile(r"/\*\s*([^*]+?)\s*\*/\s*@font-face\s*\{[^}]*\}", re.S)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

ok = 0; fail = []
for f in en:
    slug, name = f["slug"], f["name"]
    weights = f.get("weights") or [400]
    axis = "wght@" + ";".join(str(w) for w in weights)
    url = f"https://fonts.googleapis.com/css2?family={name.replace(' ', '+')}:{axis}&display=swap"
    try:
        css = fetch(url).decode("utf-8")
    except Exception as e:
        fail.append(f"{slug}: css {e}"); continue
    blocks = [m.group(0) for m in BLOCK.finditer(css) if m.group(1).strip() in KEEP]
    if not blocks:
        blocks = [m.group(0) for m in BLOCK.finditer(css)]
    new = "\n\n".join(blocks) + "\n"
    d = OUT / slug; d.mkdir(parents=True, exist_ok=True)
    for u in sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", new))):
        fn = u.rsplit("/", 1)[-1]
        loc = d / fn
        if not loc.exists():
            try: loc.write_bytes(fetch(u))
            except Exception as e: fail.append(f"{slug}/{fn}: {e}"); continue
        new = new.replace(u, f"./{slug}/{fn}")
    (OUT / f"{slug}.css").write_text(new)
    ok += 1
    print(f"OK {slug}")
print(f"=== DONE ok={ok}/{len(en)} fail={len(fail)} ===")
for x in fail: print("FAIL", x)

#!/usr/bin/env python3
"""Idempotent: add <head> link + CJK card for any deployed CN font missing from index.html."""
import pathlib, re, json
ROOT = pathlib.Path("/www/sites/static.bluecdn.com")
H = ROOT / "index.html"; FB = ROOT / "fonts"
s = H.read_text(); (ROOT / "index.html.bak.cnall").write_text(s)
man = {f["slug"]: f for f in json.load(open("/root/fonts.json"))["fonts"] if f["lang"] == "cjk"}

def family_of(slug):
    t = (FB / f"{slug}.css").read_text()
    m = re.search(r'font-family:\s*["\']?([^"\';]+)', t)
    return m.group(1).strip() if m else slug

# CN fonts on disk that are in the manifest, and missing from the page
missing = []
for slug in sorted(p.stem for p in FB.glob("*.css")):
    if slug in man and f"/fonts/{slug}.css" not in s:
        name = man[slug]["name"]
        missing.append((slug, name, family_of(slug)))

if not missing:
    print("nothing to add"); raise SystemExit
links = "".join(f'<link rel="stylesheet" href="https://static.bluecdn.com/fonts/{sl}.css">\n' for sl, _, _ in missing)
s = s.replace("<style>", links + "<style>", 1)

def card(sl, nm, fam):
    return ('      <div class="res">\n'
            f'        <div class="res-name">{nm} <span class="sub">family: {fam}</span></div>\n'
            f'        <div class="res-url">https://static.bluecdn.com/fonts/{sl}.css</div>\n'
            f"        <div class=\"copy-actions\"><button class=\"copy-btn copy-icon\" data-copy='https://static.bluecdn.com/fonts/{sl}.css' title=\"复制直链\"><i class=\"fa-light fa-link\"></i></button><button class=\"copy-btn copy-icon\" data-copy='<link rel=\"stylesheet\" href=\"https://static.bluecdn.com/fonts/{sl}.css\">' title=\"复制 HTML 代码\"><i class=\"fa-light fa-code\"></i></button></div>\n"
            f"        <div class=\"res-preview\" style=\"font-family: '{fam}', sans-serif;\">永远相信美好的事情即将发生</div>\n"
            '      </div>\n')

cards = "\n" + "".join(card(*x) for x in missing)
m = re.search(r'(中文字体 \(CJK Webfonts\).*?<div class="res-list">)', s, re.S)
s = s[:m.end()] + cards + s[m.end():]
H.write_text(s)
print("added cards:", [x[0] for x in missing])

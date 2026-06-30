#!/usr/bin/env python3
# 为每个字体把示例文字渲染成 SVG(字形转 path),卡片用 <img> 显示,无需下载字体
import os, re, glob
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

FB = "/www/sites/static.bluecdn.com/fonts"
OUT = FB + "/preview"
EN = "Always believe that something wonderful is about to happen"
CN = "永远相信美好的事情即将发生"
FILL = "#666"
os.makedirs(OUT, exist_ok=True)

def parse_faces(cssfile):
    txt = open(cssfile, errors="ignore").read()
    faces = []
    for m in re.finditer(r'@font-face\s*\{(.*?)\}', txt, re.S):
        b = m.group(1)
        s = re.search(r'url\(\s*["\']?([^)"\']+\.woff2)', b)
        if not s:
            continue
        ur = re.search(r'unicode-range:\s*([^;}]+)', b)
        faces.append((os.path.basename(s.group(1)), ur.group(1).strip() if ur else None))
    return faces

def covers(rng, cp):
    if rng is None:
        return True
    for part in rng.split(','):
        part = part.strip()
        if not part.upper().startswith('U+'):
            continue
        p = part[2:]
        if '-' in p:
            a, b = p.split('-', 1)
        else:
            a = b = p
        a = a.replace('?', '0'); b = b.replace('?', 'F')
        try:
            if int(a, 16) <= cp <= int(b, 16):
                return True
        except ValueError:
            pass
    return False

def round_d(d):
    return re.sub(r'-?\d+\.\d+', lambda m: str(round(float(m.group()))), d)

def build(slug):
    css = f"{FB}/{slug}.css"
    if not os.path.exists(css):
        return None
    faces = parse_faces(css)
    if not faces:
        return None
    fonts = {}  # woff2name -> TTFont
    def load(name):
        if name in fonts:
            return fonts[name]
        path = f"{FB}/{slug}/{name}"
        if not os.path.exists(path):
            path = f"{FB}/{name}"
        try:
            f = TTFont(path, fontNumber=0, lazy=True)
        except Exception:
            f = None
        fonts[name] = f
        return f
    def has_glyph(cp):
        wf = next((nm for nm, r in faces if covers(r, cp)), None)
        if not wf:
            return False
        f = load(wf)
        try:
            return f is not None and f.getBestCmap().get(cp) is not None
        except Exception:
            return False
    text = CN if has_glyph(0x6C38) else EN
    upm = ascent = descent = None
    x = 0; paths = []
    for ch in text:
        cp = ord(ch)
        wf = next((nm for nm, r in faces if covers(r, cp)), None)
        if not wf:
            continue
        f = load(wf)
        if f is None:
            continue
        try:
            cmap = f.getBestCmap()
        except Exception:
            continue
        gname = cmap.get(cp)
        if not gname:
            continue
        if upm is None:
            upm = f['head'].unitsPerEm
            ascent = f['hhea'].ascent; descent = f['hhea'].descent
        gs = f.getGlyphSet()
        pen = SVGPathPen(gs)
        try:
            gs[gname].draw(pen)
        except Exception:
            adv = f['hmtx'].metrics.get(gname, (upm, 0))[0]; x += adv; continue
        d = round_d(pen.getCommands())
        adv = f['hmtx'].metrics.get(gname, (upm, 0))[0]
        if d:
            paths.append(f'<path transform="translate({x} 0)" d="{d}"/>')
        x += adv
    if not paths or upm is None:
        return None
    H = ascent - descent
    W = x
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{round(W)}" height="{H}" '
           f'viewBox="0 0 {round(W)} {H}" fill="{FILL}">'
           f'<g transform="translate(0 {ascent}) scale(1 -1)">' + ''.join(paths) + '</g></svg>')
    open(f"{OUT}/{slug}.svg", "w").write(svg)
    return len(svg)

slugs = [os.path.basename(p)[:-4] for p in glob.glob(FB + "/*.css")]
ok = []; fail = []; sizes = []
for s in sorted(slugs):
    try:
        r = build(s)
    except Exception as e:
        r = None
    if r:
        ok.append(s); sizes.append(r)
    else:
        fail.append(s)
open(OUT + "/_ok.txt", "w").write("\n".join(ok))
print(f"OK {len(ok)}  FAIL {len(fail)}  avg {round(sum(sizes)/max(1,len(sizes)))}B  max {max(sizes) if sizes else 0}B")
if fail:
    print("FAILED:", " ".join(fail[:40]))

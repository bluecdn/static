import os, re, glob
from fontTools.ttLib import TTFont
FB="/www/sites/static.bluecdn.com/fonts"
def parse(css):
    t=open(css,errors="ignore").read(); faces=[]
    for m in re.finditer(r'@font-face\s*\{(.*?)\}',t,re.S):
        b=m.group(1); s=re.search(r'url\(\s*["\']?([^)"\']+\.woff2)',b)
        if not s: continue
        ur=re.search(r'unicode-range:\s*([^;}]+)',b)
        faces.append((os.path.basename(s.group(1)), ur.group(1).strip() if ur else None))
    return faces
def covers(rng,cp):
    if rng is None: return True
    for part in rng.split(','):
        part=part.strip()
        if not part.upper().startswith('U+'): continue
        p=part[2:]; a,b=(p.split('-',1) if '-' in p else (p,p))
        a=a.replace('?','0'); b=b.replace('?','F')
        try:
            if int(a,16)<=cp<=int(b,16): return True
        except: pass
    return False
simp=[]; trad=[]; jp=[]
for css in sorted(glob.glob(FB+"/*.css")):
    slug=os.path.basename(css)[:-4]; faces=parse(css)
    if not faces: continue
    cache={}
    def load(nm):
        if nm in cache: return cache[nm]
        for p in (f"{FB}/{slug}/{nm}",f"{FB}/{nm}"):
            if os.path.exists(p):
                try: cache[nm]=TTFont(p,lazy=True); return cache[nm]
                except: pass
        cache[nm]=None; return None
    def has(cp):
        wf=next((n for n,r in faces if covers(r,cp)),None)
        if not wf: return False
        f=load(wf)
        try: return f is not None and f.getBestCmap().get(cp) is not None
        except: return False
    if not has(0x6C38): continue  # 永,非中文
    has_kana = has(0x3042) or has(0x30A2)   # あ ア
    has_simp = has(0x56FD) and has(0x53D1)   # 国 发
    has_trad = has(0x570B) and has(0x767C)   # 國 發
    if has_kana: jp.append(slug)
    elif has_trad and not has_simp: trad.append(slug)
    else: simp.append(slug)
print("简体(或简繁兼有):",len(simp))
print("繁体:",len(trad),"->", " ".join(trad))
print("日文:",len(jp),"->"," ".join(jp))

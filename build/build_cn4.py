#!/usr/bin/env python3
import pathlib, re, subprocess, shutil, json, urllib.request, urllib.parse
FB = pathlib.Path("/www/sites/static.bluecdn.com/fonts")
TMP = pathlib.Path("/tmp/cn4"); TMP.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}
REPO = "wordshub/free-font"; BR = "master"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BR}/"

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()

tree = json.loads(get(f"https://api.github.com/repos/{REPO}/git/trees/{BR}?recursive=1").decode())["tree"]
allf = [t["path"] for t in tree if t["path"].lower().endswith((".ttf", ".otf"))]

def wt(name):
    n = name.lower()
    for k, w in [("thin",100),("extralight",200),("-l.",300),("light",300),("-m.",500),("medium",500),
                 ("semibold",600),("-b.",700),("bold",700),("heavy",900),("black",900),("-r.",400),("regular",400)]:
        if k in n: return w
    return 400

# slug -> (family, folder-substr, wanted weights)
JOBS = {
    "alibaba-puhuiti": ("Alibaba PuHuiTi", "阿里巴巴普惠体", {400, 500, 700}),
    "oppo-sans":       ("OPPO Sans", "OPPO Sans", {400, 500, 700}),
}

ok, fail = [], []
for slug, (family, folder, weights) in JOBS.items():
    try:
        cands = [p for p in allf if folder in p]
        chosen = {}
        for p in cands:
            w = wt(p.split("/")[-1])
            if w in weights and w not in chosen:
                chosen[w] = p
        if not chosen:
            fail.append(f"{slug}: none of {weights} in {[c.split('/')[-1] for c in cands][:6]}"); continue
        dl = TMP/slug; shutil.rmtree(dl, ignore_errors=True); dl.mkdir(parents=True)
        stg = TMP/("s-"+slug); shutil.rmtree(stg, ignore_errors=True); stg.mkdir(parents=True)
        comb = []
        for w, path in sorted(chosen.items()):
            url = RAW + urllib.parse.quote(path)
            fp = dl/("%d.ttf" % w); fp.write_bytes(get(url))
            outd = TMP/f"o-{slug}-{w}"; shutil.rmtree(outd, ignore_errors=True)
            subprocess.run(["cn-font-split","run","-i",str(fp),"-o",str(outd),"--chunkSize","4000000",
                            "--css.fontFamily",family,"--css.fontWeight",str(w)], check=True, capture_output=True)
            for x in outd.glob("*.woff2"): shutil.copy(str(x), str(stg/x.name))
            comb.append(re.sub(r'(url\(["\']?)\./', rf"\1./{slug}/", (outd/"result.css").read_text()))
            shutil.rmtree(outd, ignore_errors=True)
        shutil.rmtree(FB/slug, ignore_errors=True); shutil.move(str(stg), str(FB/slug))
        (FB/f"{slug}.css").write_text("\n".join(comb)+"\n")
        ws=[p.stat().st_size for p in (FB/slug).glob("*.woff2")]
        ok.append(f"{slug}: weights {sorted(chosen)} -> {len(ws)} chunks max {max(ws)/1024:.0f}KB")
    except Exception as e:
        fail.append(f"{slug}: {str(e)[:80]}")
print("OK:", ok); print("FAIL:", fail)

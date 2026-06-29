#!/usr/bin/env python3
"""Download CN fonts from GitHub latest releases, slice (<2MB) and deploy."""
import pathlib, re, subprocess, shutil, json, urllib.request, zipfile, os
FB = pathlib.Path("/www/sites/static.bluecdn.com/fonts")
TMP = pathlib.Path("/tmp/ghcn"); TMP.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}

# slug -> (repo, family, asset_name_regex)  pick ttf/otf assets (or inside zip) matching regex
JOBS = {
    "lxgw-wenkai-screen": ("lxgw/LxgwWenkaiScreen", "LXGW WenKai Screen", r"Screen\.ttf$"),
    "lxgw-neo-xihei":     ("lxgw/LxgwNeoXiHei", "LXGW Neo XiHei", r"LXGWNeoXiHei\.ttf$"),
    "smiley-sans":        ("atelier-anchor/smiley-sans", "Smiley Sans", r"\.ttf$"),
    "glow-sans-sc":       ("welai/glow-sans", "Glow Sans SC", r"GlowSansSC-Normal-Regular\.otf$"),
}

def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read() if binary else r.read().decode()

def weight_of(name):
    n = name.lower()
    for k, w in [("thin",100),("extralight",200),("light",300),("medium",500),
                 ("semibold",600),("bold",700),("black",900),("heavy",900),("regular",400)]:
        if k in n: return w
    return 400

def deploy(slug, family, fontfiles):
    staging = TMP / ("stg-" + slug)
    shutil.rmtree(staging, ignore_errors=True); staging.mkdir(parents=True)
    combined = []
    for fp in fontfiles:
        wt = weight_of(fp.name)
        outd = TMP / f"o-{slug}-{wt}"
        shutil.rmtree(outd, ignore_errors=True)
        subprocess.run(["cn-font-split","run","-i",str(fp),"-o",str(outd),"--chunkSize","4000000",
                        "--css.fontFamily",family,"--css.fontWeight",str(wt)], check=True, capture_output=True)
        for w in outd.glob("*.woff2"): shutil.copy(str(w), str(staging / w.name))
        rc = (outd/"result.css").read_text()
        combined.append(re.sub(r'(url\(["\']?)\./', rf"\1./{slug}/", rc))
        shutil.rmtree(outd, ignore_errors=True)
    shutil.rmtree(FB/slug, ignore_errors=True); shutil.move(str(staging), str(FB/slug))
    (FB/f"{slug}.css").write_text("\n".join(combined)+"\n")
    sizes=[p.stat().st_size for p in (FB/slug).glob("*.woff2")]
    return len(sizes), max(sizes)/1024 if sizes else 0

ok, fail = [], []
for slug,(repo,family,rgx) in JOBS.items():
    try:
        rel = json.loads(get(f"https://api.github.com/repos/{repo}/releases/latest"))
        assets = rel.get("assets", [])
        fontfiles = []
        dl = TMP/slug; shutil.rmtree(dl, ignore_errors=True); dl.mkdir(parents=True)
        # direct ttf/otf assets matching regex
        for a in assets:
            if re.search(rgx, a["name"]):
                p = dl/a["name"]; p.write_bytes(get(a["browser_download_url"], binary=True)); fontfiles.append(p)
        # if none, look inside zip assets
        if not fontfiles:
            for a in assets:
                if a["name"].endswith(".zip"):
                    zp = dl/a["name"]; zp.write_bytes(get(a["browser_download_url"], binary=True))
                    with zipfile.ZipFile(zp) as z:
                        for nm in z.namelist():
                            if re.search(rgx, nm.split("/")[-1]):
                                z.extract(nm, dl); fontfiles.append(dl/nm)
                    if fontfiles: break
        if not fontfiles:
            fail.append(f"{slug}: no asset matching {rgx} (assets: {[a['name'] for a in assets][:5]})"); continue
        n, mx = deploy(slug, family, fontfiles)
        ok.append(f"{slug}: {n} chunks, max {mx:.0f}KB (from {[f.name for f in fontfiles]})")
    except Exception as e:
        fail.append(f"{slug}: {str(e)[:80]}")
print("=== OK ==="); [print(" ",x) for x in ok]
print("=== FAIL ==="); [print(" ",x) for x in fail]

#!/usr/bin/env python3
import pathlib, re, subprocess, shutil, json, urllib.request
FB = pathlib.Path("/www/sites/static.bluecdn.com/fonts")
TMP = pathlib.Path("/tmp/cn3"); TMP.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}
HRAW = "https://raw.githubusercontent.com/IKKI2000/harmonyos-fonts/main/fonts/HarmonyOS_Sans_SC/"

# slug -> (family, [(url, weight)])
DIRECT = {
    "harmonyos-sans-sc": ("HarmonyOS Sans SC", [
        (HRAW + "HarmonyOS_Sans_SC_Regular.ttf", 400),
        (HRAW + "HarmonyOS_Sans_SC_Medium.ttf", 500),
        (HRAW + "HarmonyOS_Sans_SC_Bold.ttf", 700)]),
}
# slug -> (repo, family, regex, {filename-substr: weight})
RELEASE = {
    "yozai": ("lxgw/yozai-font", "Yozai", r"Yozai-(Light|Medium|Regular)\.ttf$",
              {"Light": 300, "Regular": 400, "Medium": 500}),
}

def get(url, b=True):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()

def build(slug, family, files):  # files: [(localpath, weight)]
    stg = TMP / ("s-" + slug); shutil.rmtree(stg, ignore_errors=True); stg.mkdir(parents=True)
    comb = []
    for fp, wt in files:
        outd = TMP / f"o-{slug}-{wt}"; shutil.rmtree(outd, ignore_errors=True)
        subprocess.run(["cn-font-split","run","-i",str(fp),"-o",str(outd),"--chunkSize","4000000",
                        "--css.fontFamily",family,"--css.fontWeight",str(wt)], check=True, capture_output=True)
        for w in outd.glob("*.woff2"): shutil.copy(str(w), str(stg / w.name))
        comb.append(re.sub(r'(url\(["\']?)\./', rf"\1./{slug}/", (outd/"result.css").read_text()))
        shutil.rmtree(outd, ignore_errors=True)
    shutil.rmtree(FB/slug, ignore_errors=True); shutil.move(str(stg), str(FB/slug))
    (FB/f"{slug}.css").write_text("\n".join(comb)+"\n")
    ws=[p.stat().st_size for p in (FB/slug).glob("*.woff2")]
    return len(ws), max(ws)/1024

ok, fail = [], []
for slug,(family,items) in DIRECT.items():
    try:
        dl=TMP/slug; shutil.rmtree(dl,ignore_errors=True); dl.mkdir(parents=True)
        files=[]
        for url,wt in items:
            p=dl/url.split("/")[-1]; p.write_bytes(get(url)); files.append((p,wt))
        n,mx=build(slug,family,files); ok.append(f"{slug}: {n} chunks max {mx:.0f}KB")
    except Exception as e: fail.append(f"{slug}: {str(e)[:70]}")
for slug,(repo,family,rgx,wmap) in RELEASE.items():
    try:
        rel=json.loads(get(f"https://api.github.com/repos/{repo}/releases/latest").decode())
        dl=TMP/slug; shutil.rmtree(dl,ignore_errors=True); dl.mkdir(parents=True)
        files=[]
        for a in rel["assets"]:
            if re.search(rgx,a["name"]):
                wt=next((w for k,w in wmap.items() if k in a["name"]),400)
                p=dl/a["name"]; p.write_bytes(get(a["browser_download_url"])); files.append((p,wt))
        if not files: fail.append(f"{slug}: no asset"); continue
        n,mx=build(slug,family,files); ok.append(f"{slug}: {n} chunks max {mx:.0f}KB")
    except Exception as e: fail.append(f"{slug}: {str(e)[:70]}")
print("OK:", ok); print("FAIL:", fail)

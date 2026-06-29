#!/usr/bin/env python3
"""Download whole CN TTFs from github.com/google/fonts, build /fonts/{slug}.css.
   Slice (cn-font-split chunkSize 4MB) if the woff2 would be >2MB, else keep whole."""
import pathlib, re, subprocess, shutil, urllib.request, os
FB = pathlib.Path("/www/sites/static.bluecdn.com/fonts")
RAW = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
# slug -> (gf_dir, [(ttf_file, weight)], css_family)
FONTS = {
    "ma-shan-zheng":        ("mashanzheng",        [("MaShanZheng-Regular.ttf", 400)], "Ma Shan Zheng"),
    "zhi-mang-xing":        ("zhimangxing",        [("ZhiMangXing-Regular.ttf", 400)], "Zhi Mang Xing"),
    "long-cang":            ("longcang",           [("LongCang-Regular.ttf", 400)], "Long Cang"),
    "liu-jian-mao-cao":     ("liujianmaocao",      [("LiuJianMaoCao-Regular.ttf", 400)], "Liu Jian Mao Cao"),
    "zcool-kuaile":         ("zcoolkuaile",        [("ZCOOLKuaiLe-Regular.ttf", 400)], "ZCOOL KuaiLe"),
    "zcool-qingke-huangyou":("zcoolqingkehuangyou",[("ZCOOLQingKeHuangYou-Regular.ttf", 400)], "ZCOOL QingKe HuangYou"),
    "zcool-xiaowei":        ("zcoolxiaowei",       [("ZCOOLXiaoWei-Regular.ttf", 400)], "ZCOOL XiaoWei"),
    "dotgothic16":          ("dotgothic16",        [("DotGothic16-Regular.ttf", 400)], "DotGothic16"),
    "klee-one":             ("kleeone",            [("KleeOne-Regular.ttf", 400), ("KleeOne-SemiBold.ttf", 600)], "Klee One"),
    "yuji-syuku":           ("yujisyuku",          [("YujiSyuku-Regular.ttf", 400)], "Yuji Syuku"),
}
TMP = pathlib.Path("/tmp/gfcn"); TMP.mkdir(exist_ok=True)

def dl(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())

ok, fail = [], []
for slug, (gdir, files, fam) in FONTS.items():
    try:
        staging = TMP / slug
        shutil.rmtree(staging, ignore_errors=True); staging.mkdir(parents=True)
        combined = []
        for ttf, wt in files:
            tpath = staging / ttf
            dl(RAW + gdir + "/" + ttf, tpath)
            outd = TMP / f"{slug}-{wt}"
            shutil.rmtree(outd, ignore_errors=True)
            subprocess.run(["cn-font-split", "run", "-i", str(tpath), "-o", str(outd),
                            "--chunkSize", "4000000", "--css.fontFamily", fam,
                            "--css.fontWeight", str(wt)], check=True, capture_output=True)
            for w in outd.glob("*.woff2"):
                shutil.copy(str(w), str(staging / w.name))
            rc = (outd / "result.css").read_text()
            rc = re.sub(r'(url\(["\']?)\./', rf"\1./{slug}/", rc)
            combined.append(rc)
            tpath.unlink()
            shutil.rmtree(outd, ignore_errors=True)
        # deploy
        shutil.rmtree(FB / slug, ignore_errors=True)
        shutil.move(str(staging), str(FB / slug))
        (FB / f"{slug}.css").write_text("\n".join(combined) + "\n")
        n = len(list((FB / slug).glob("*.woff2")))
        mx = max((p.stat().st_size for p in (FB / slug).glob("*.woff2")), default=0) / 1024
        ok.append(f"{slug}: {n} chunks, max {mx:.0f}KB")
    except Exception as e:
        fail.append(f"{slug}: {str(e)[:60]}")
print("=== OK ==="); [print(" ", x) for x in ok]
print("=== FAIL ==="); [print(" ", x) for x in fail]

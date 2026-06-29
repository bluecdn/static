#!/usr/bin/env python3
"""Normalize early FontAwesome versions so every version has css/all.min.css + webfonts/."""
import pathlib, shutil
FA = pathlib.Path("/www/sites/static.bluecdn.com/libs/fontawesome")
fixed, reextract = [], []
for vdir in sorted(FA.iterdir()):
    if not vdir.is_dir():
        continue
    v = vdir.name
    if (vdir / "css" / "all.min.css").exists():
        continue
    wfc = vdir / "web-fonts-with-css"
    if wfc.exists() and (wfc / "css" / "fontawesome-all.min.css").exists():
        # 5.0.x old layout: lift css/ and webfonts/ to version root
        if not (vdir / "css").exists() and (wfc / "css").exists():
            shutil.move(str(wfc / "css"), str(vdir / "css"))
        if not (vdir / "webfonts").exists() and (wfc / "webfonts").exists():
            shutil.move(str(wfc / "webfonts"), str(vdir / "webfonts"))
        fa_all_min = vdir / "css" / "fontawesome-all.min.css"
        fa_all = vdir / "css" / "fontawesome-all.css"
        if fa_all_min.exists():
            shutil.copy(str(fa_all_min), str(vdir / "css" / "all.min.css"))
        if fa_all.exists():
            shutil.copy(str(fa_all), str(vdir / "css" / "all.css"))
        fixed.append(v)
    else:
        reextract.append(v)
print("normalized(5.0.x):", fixed)
print("need-reextract:", reextract)

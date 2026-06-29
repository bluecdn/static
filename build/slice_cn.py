#!/usr/bin/env python3
"""Re-slice CN fonts whose single woff2 > 2MB, using cn-font-split (chunkSize 4MB
so every chunk < 2MB). Keeps font-family/weight from the existing {slug}.css.
Other CN fonts (<=2MB) are left whole."""
import pathlib, re, subprocess, shutil
FB = pathlib.Path("/www/sites/static.bluecdn.com/fonts")
SLICE = ["lxgw-wenkai", "maple-mono-cn", "alimama-fangyuanti"]
CHUNK = "4000000"

for slug in SLICE:
    cssf = FB / f"{slug}.css"
    txt = cssf.read_text()
    faces = []
    for m in re.finditer(r"@font-face\s*\{[^}]*\}", txt, re.S):
        b = m.group(0)
        fam = re.search(r'font-family:\s*["\']?([^"\';]+)', b)
        wt = re.search(r"font-weight:\s*(\d+)", b)
        url = re.search(r'url\(["\']?\./' + re.escape(slug) + r'/([^"\')]+\.woff2)', b)
        if url:
            faces.append((url.group(1), wt.group(1) if wt else "400",
                          fam.group(1).strip() if fam else slug))
    if not faces:
        print(f"{slug}: no faces parsed, SKIP"); continue
    staging = pathlib.Path(f"/tmp/sliced-{slug}")
    shutil.rmtree(staging, ignore_errors=True); staging.mkdir(parents=True)
    combined = []
    for fname, wt, fam in faces:
        src = FB / slug / fname
        if not src.exists():
            print(f"  MISS {src}"); continue
        outd = pathlib.Path(f"/tmp/cfs-{slug}-{wt}")
        shutil.rmtree(outd, ignore_errors=True)
        subprocess.run(["cn-font-split", "run", "-i", str(src), "-o", str(outd),
                        "--chunkSize", CHUNK, "--css.fontFamily", fam,
                        "--css.fontWeight", wt], check=True, capture_output=True)
        for w in outd.glob("*.woff2"):
            shutil.copy(str(w), str(staging / w.name))
        rc = (outd / "result.css").read_text()
        rc = re.sub(r'(url\(["\']?)\./', rf"\1./{slug}/", rc)
        combined.append(rc)
        shutil.rmtree(outd, ignore_errors=True)
    shutil.rmtree(FB / slug)
    shutil.move(str(staging), str(FB / slug))
    cssf.write_text("\n".join(combined) + "\n")
    sizes = sorted((p.stat().st_size for p in (FB / slug).glob("*.woff2")), reverse=True)
    mx = sizes[0] / 1024 if sizes else 0
    over = sum(1 for s in sizes if s > 2 * 1024 * 1024)
    print(f"{slug}: {len(faces)} weights -> {len(sizes)} chunks, max {mx:.0f}KB, over2MB={over}")

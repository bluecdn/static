#!/usr/bin/env python3
"""Parse fonts-candidates.md -> fonts.json (the single source of truth).

All rows are included (user decision: keep everything). The checkbox column is
recorded as `picked` for reference but does NOT exclude rows.

Schema per entry:
  slug, name, lang ("latin"|"cjk"), category ("sans"|"serif"|"mono"|"display"),
  weights (list[int] | null=auto), source ("google"|"manual"), license, note, picked
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MD = ROOT / "fonts-candidates.md"
OUT = ROOT / "fonts.json"

# section header -> (lang, category, default_license, default_source)
SECTION = {
    "Sans-serif": ("latin", "sans", "OFL/Apache-2.0", "google"),
    "Serif":      ("latin", "serif", "OFL/Apache-2.0", "google"),
    "Monospace":  ("latin", "mono", "OFL/Apache-2.0", "google"),
    "Display":    ("latin", "display", "OFL/Apache-2.0", "google"),
    "开源 / 免费商用": ("cjk", "sans", "open", "manual"),
    "免费商用但有条件": ("cjk", "sans", "free-conditional", "manual"),
    "品牌 / 受限":     ("cjk", "display", "restricted", "manual"),
}

ROW = re.compile(r"^\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*(?:\|\s*(.*?)\s*)?\|?\s*$")


def parse_weights(s):
    nums = re.findall(r"\d+", s)
    return [int(n) for n in nums] if nums else None


def main():
    text = MD.read_text(encoding="utf-8")
    cur = None
    fonts = []
    seen = set()
    for line in text.splitlines():
        h = line.strip()
        if h.startswith("#"):
            for key, meta in SECTION.items():
                if key in h:
                    cur = meta
                    break
            continue
        if not cur or not h.startswith("|"):
            continue
        # skip table header / separator rows
        if h.startswith("| ✓") or h.startswith("| ---") or set(h) <= set("| -:"):
            continue
        m = ROW.match(h)
        if not m:
            continue
        check, slug, name, c4, c5 = m.groups()
        slug = slug.strip().strip("`")
        if not slug or slug in ("slug",) or " " in slug:
            continue
        if slug in seen:
            continue
        seen.add(slug)
        lang, category, lic, src = cur
        picked = check.strip().lower() in ("x", "✓")
        weights = note = None
        if lang == "latin":
            weights = parse_weights(c4 or "")
        else:  # cjk: green=授权|来源, yellow/red=说明
            if lic == "open" and c5:
                lic = (c4 or "open").strip()
                note = (c5 or "").strip()
            else:
                note = (c4 or "").strip()
        fonts.append({
            "slug": slug, "name": name.strip(), "lang": lang, "category": category,
            "weights": weights, "source": src, "license": lic,
            "note": note, "picked": picked,
        })

    manifest = {
        "version": 1,
        "base": "https://static.bluecdn.com/fonts",
        "count": {
            "total": len(fonts),
            "latin": sum(f["lang"] == "latin" for f in fonts),
            "cjk": sum(f["lang"] == "cjk" for f in fonts),
        },
        "fonts": fonts,
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"  total={manifest['count']['total']}  latin={manifest['count']['latin']}  cjk={manifest['count']['cjk']}")
    by_lic = {}
    for f in fonts:
        if f["lang"] == "cjk":
            by_lic[f["license"]] = by_lic.get(f["license"], 0) + 1
    print(f"  cjk by license: {by_lic}")


if __name__ == "__main__":
    main()

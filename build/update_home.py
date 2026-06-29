#!/usr/bin/env python3
"""Update the deployed index.html: font CSS paths -> /fonts/{slug}.css,
   and FontAwesome version dropdown -> all installed versions."""
import pathlib, re
ROOT = pathlib.Path("/www/sites/static.bluecdn.com")
H = ROOT / "index.html"
s = H.read_text()
(ROOT / "index.html.bak.prefa").write_text(s)

# 1) font css paths: /fonts/cn/X/result.css and /fonts/X/result.css -> /fonts/X.css
s = re.sub(r'/fonts/cn/([^/"\']+)/result\.css', r'/fonts/\1.css', s)
s = re.sub(r'/fonts/([^/"\']+)/result\.css', r'/fonts/\1.css', s)

# 2) FontAwesome version dropdown -> all installed versions (semver desc)
fadir = ROOT / "libs" / "fontawesome"
vers = sorted([d.name for d in fadir.iterdir() if d.is_dir()],
              key=lambda v: [int(x) for x in re.findall(r"\d+", v)], reverse=True)
opts = []
for i, v in enumerate(vers):
    label = v + " (最新)" if i == 0 else v
    sel = " selected" if i == 0 else ""
    opts.append('\t\t\t<option value="%s"%s>%s</option>' % (v, sel, label))
optstr = "\n".join(opts)
s, n = re.subn(r'(<select id="fa-version"[^>]*>).*?(</select>)',
               lambda m: m.group(1) + "\n" + optstr + "\n\t\t" + m.group(2),
               s, flags=re.S)

H.write_text(s)
print("FA versions:", len(vers), "latest:", vers[0])
print("select replaced:", n)
print("leftover result.css refs:", s.count("result.css"))
print("leftover /fonts/cn/ refs:", s.count("/fonts/cn/"))

#!/usr/bin/env python3 -B
"""
gistsite.py, render konfig-style gists into a static catalog (cli)
(c) 2026, Tim Menzies <timm@ieee.org>, MIT license

Hit the GitHub gists API for a user, keep only the curated ones (a
file named `,<name>.md` is the README hook -- see konfig style_gist),
fetch each README, run it through pandoc (gfm -> html), and write
<name>.html plus an index.html roster. Pure stdlib + pandoc; pages
inherit timm.fyi's site.css, so the catalog looks like the rest of
the site with zero extra config.

Note: GitHub gists have no folders, so the API returns EVERY gist with
a ,name.md hook -- including retired ones. A local old/ dir means
nothing to the API; exclude stale gists by slug with --skip.

Options:
 -u --user  github user                       user=timm
 -o --out   output dir                         out=docs
 -c --css   stylesheet href for every page     css=https://timm.fyi/site.css
 -x --skip  comma list of slugs to exclude     skip=

eg: python3 gistsite.py --checks     # self-tests (no network)
    python3 gistsite.py -o docs      # render catalog -> docs/
    python3 gistsite.py --skip ape,ruler   # drop retired gists
"""
import os, re, sys, json, subprocess
from urllib.request import urlopen, Request
from types import SimpleNamespace as o

HDRS = {"User-Agent": "gistsite",
        "Accept": "application/vnd.github+json"}
HOOK = re.compile(r"^,(.+)\.md$")   # a curated gist's README filename

# ## github + render --------------------------------------------
def get(url, raw=False):
  "Fetch a url with the API headers; json unless raw."
  txt = urlopen(Request(url, headers=HDRS)).read().decode()
  return txt if raw else json.loads(txt)

def gists(user):
  "Every gist for a user, walking the paginated API."
  out, page = [], 1
  while batch := get(f"https://api.github.com/users/{user}"
                     f"/gists?per_page=100&page={page}"):
    out += batch; page += 1
  return out

def slug(s):
  "Filesafe page name: lowercase, runs of non-alphanumerics -> single -."
  return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def curated(gist):
  "If a gist has a ,name.md README, return its catalog record, else None."
  for fname, f in gist["files"].items():
    if m := HOOK.match(fname):
      return o(name=slug(m.group(1)), raw=f["raw_url"], url=gist["html_url"],
               desc=gist["description"] or m.group(1),
               at=(gist["updated_at"] or "")[:10])

def pandoc(md):
  "gfm markdown -> html fragment."
  p = subprocess.run(["pandoc", "-f", "gfm", "-t", "html"],
                     input=md, capture_output=True, text=True)
  return p.stdout

def ghanchor(filename):
  "GitHub gist's in-page anchor id for a filename (lowercase, .->-)."
  return "file-" + re.sub(r"[^a-z0-9_]", "-", filename.lower())

def relink(html, gist):
  "Point README #file-* links at the real file (raw url), else the gist."
  raws = {ghanchor(fn): f["raw_url"] for fn, f in gist["files"].items()}
  fix = lambda m: 'href="%s"' % raws.get(
    m.group(1), gist["html_url"] + "#" + m.group(1))
  return re.sub(r'href="#(file-[a-z0-9_-]+)"', fix, html)

# ## html templates ---------------------------------------------
def esc(s):
  return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

STYLE = """<style>
body{max-width:860px}
pre{overflow-x:auto;white-space:pre;color:#e6edf3;
    background:linear-gradient(145deg,#0d1117 0%,#161b22 60%,#1b2230 100%);
    border:1px solid #30363d;border-left:3px solid #ffb86c;
    border-radius:8px;padding:12px 14px;
    box-shadow:inset 0 1px 0 #000, 0 0 20px rgba(255,184,108,.07)}
code{font-family:ui-monospace,Menlo,Consolas,monospace}
.sourceCode .co{color:#888;font-style:italic}
.sourceCode .kw,.sourceCode .cf{color:#ff7b72}
.sourceCode .fu,.sourceCode .at{color:#d2a8ff}
.sourceCode .st,.sourceCode .vs,.sourceCode .ss{color:#a5d6ff}
.sourceCode .dv,.sourceCode .bn,.sourceCode .fl{color:#79c0ff}
.sourceCode .va,.sourceCode .cn{color:#ffa657}
.sourceCode .op,.sourceCode .sc{color:#e0e0e0}
</style>"""

HEAD = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="{css}">
{style}
<title>{title}</title></head><body><main>
<nav><span><b><a href="index.html">tools</a></b> |
<a href="https://timm.fyi">timm.fyi</a></span>
<span><a href="https://github.com/{user}">github</a></span></nav>
<hr>
"""
FOOT = ('\n<hr>\n<p class="foot"><span>built by '
        '<a href="https://github.com/aiez/gistsite">gistsite</a></span></p>\n'
        '</main></body></html>\n')

def wrap(title, body, the):
  head = HEAD.format(css=the.css, title=esc(title), user=the.user, style=STYLE)
  return head + body + FOOT

def roster(items, the):
  "The index.html body: one table row per curated gist."
  rows = "\n".join(
    f'<tr><td><a href="{g.name}.html">{esc(g.name)}</a></td>'
    f'<td>{esc(g.desc)}</td>'
    f'<td><a href="{g.url}">src</a></td><td>{g.at}</td></tr>'
    for g in items)
  return (f"<h1>tools</h1>\n<p>{len(items)} curated gists by "
          f'<a href="https://github.com/{the.user}">{the.user}</a>. each '
          "carries a one-file README, runs in three commands.</p>\n"
          "<table><tr><th>tool</th><th>what</th><th>src</th>"
          f"<th>updated</th></tr>\n{rows}\n</table>")

# ## build ------------------------------------------------------
def build(the):
  os.makedirs(the.out, exist_ok=True)
  skip = {s for s in getattr(the, "skip", "").split(",") if s}
  items = []
  for gist in gists(the.user):
    if (g := curated(gist)) and g.name not in skip:
      open(f"{the.out}/{g.name}.html", "w").write(
        wrap(g.name, relink(pandoc(get(g.raw, raw=True)), gist), the))
      items.append(g); print("ok", g.name)
  items.sort(key=lambda g: g.name)
  open(f"{the.out}/index.html", "w").write(wrap("gists", roster(items, the), the))
  print(f"# {len(items)} gists -> {the.out}")

# ## checks (run via --checks; no network) ----------------------
def test_curated():
  "A ,name.md file marks a curated gist; its name drops comma + ext."
  g = curated({"description": "d", "html_url": "u",
    "updated_at": "2026-06-15T09:00:00Z",
    "files": {",xomo.md": {"raw_url": "r"}, "xomo.py": {"raw_url": "r2"}}})
  assert g.name == "xomo" and g.desc == "d" and g.at == "2026-06-15"

def test_skip():
  "No ,name.md -> not curated."
  assert curated({"description": None, "html_url": "u", "updated_at": "",
                  "files": {"README.md": {"raw_url": "r"}}}) is None

def test_pandoc():
  "pandoc turns gfm into html."
  assert "<h1" in pandoc("# hi")

def test_wrap():
  "Page carries the title and the css href."
  p = wrap("x", "body", o(css="c.css", user="timm"))
  assert "<title>x</title>" in p and 'href="c.css"' in p

def test_esc():
  assert esc("a&<b>") == "a&amp;&lt;b&gt;"

def test_slug():
  "Slug is lowercase + filesafe; punctuation collapses to one hyphen."
  assert slug("dot files") == "dot-files" and slug("Preci0us") == "preci0us"
  assert slug("sand-box") == "sand-box"

def test_ghanchor():
  "Filename -> GitHub gist anchor: lowercase, dot/punct -> -, _ kept."
  assert ghanchor("auto93.csv") == "file-auto93-csv"
  assert ghanchor("a_b.c-d.CSV") == "file-a_b-c-d-csv"

def test_relink():
  "A #file-* link points at the matching file's raw url, else the gist."
  g = {"html_url": "U", "files": {"auto93.csv": {"raw_url": "RAW"}}}
  assert 'href="RAW"' in relink('<a href="#file-auto93-csv">x</a>', g)
  assert 'href="U#file-gone-csv"' in relink('<a href="#file-gone-csv">x</a>', g)

# ## lib + cli --------------------------------------------------
def settings(s):
  "Parse var=val pairs from a string into an o (val may be empty)."
  return o(**dict(re.findall(r"(\w+)=(\S*)", s)))

def main(the, g):
  argv = sys.argv[1:]
  vals = {"-u": "user", "--user": "user", "-o": "out", "--out": "out",
          "-c": "css", "--css": "css", "-x": "skip", "--skip": "skip"}
  i = 0
  while i < len(argv):
    a = argv[i]
    if "=" in a and a.lstrip("-").split("=")[0] in vals.values():
      k, v = a.lstrip("-").split("=", 1); setattr(the, k, v)
    elif a in vals and i+1 < len(argv):
      setattr(the, vals[a], argv[i+1]); i += 1
    i += 1
  if "-h" in argv or "--help" in argv: return print((__doc__ or "").strip())
  if "--checks" in argv:
    tests = {k: v for k, v in g.items() if k.startswith("test_")}
    ok = 0
    for name, fn in tests.items():
      try: fn(); ok += 1; print("PASS", name)
      except Exception as e: print("FAIL", name, e)
    return print(f"# {ok}/{len(tests)} ok")
  build(the)

the = settings(__doc__)
if __name__ == "__main__":
  main(the, globals())

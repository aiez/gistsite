<!-- Copyright (c) 2026 Tim Menzies, MIT License https://opensource.org/licenses/MIT -->
<a href="https://timm.fyi"><img align="right" alt="Author" src="https://img.shields.io/badge/Author-timm-dc143c?logo=readme&logoColor=white"></a><img align="right" alt="Language" src="https://img.shields.io/badge/Language-Python%203.12+-000080?logo=python&logoColor=white"><img align="right" alt="Deps" src="https://img.shields.io/badge/Deps-pandoc-32cd32?logo=markdown&logoColor=white"><a href="https://choosealicense.com/licenses/mit/"><img align="right" alt="License" src="https://img.shields.io/badge/License-MIT-32cd32?logo=open-source-initiative&logoColor=white"></a><img align="right" alt="Purpose" src="https://img.shields.io/badge/Purpose-Static%20Catalog-7b68ee?logo=githubcopilot&logoColor=white"><br>

### [http://tiny.cc/gistsite](http://tiny.cc/gistsite)
gistsite: one short file that turns a GitHub user's gists into a
static catalog. It keeps only the *curated* ones -- gists whose files
include a `,<name>.md` README hook (the konfig convention) -- fetches
each README, pipes it through `pandoc` (gfm -> html), and writes
`<name>.html` plus an `index.html` roster. Pure stdlib + pandoc; every
page links [timm.fyi](https://timm.fyi)'s `site.css`, so the catalog
matches the rest of the site with no extra config.

```bash
# install and test
git clone http://tiny.cc/gistsite && cd gistsite
python3 -B gistsite.py --checks      # self-tests (no network)
python3 -B gistsite.py -o docs       # render catalog -> docs/
```

**Sections:** [NAME](#name) | [SYNOPSIS](#synopsis) | [OPTIONS](#options) | [DETECT](#detect) | [OUTPUT](#output) | [TESTS](#tests) | [SEE ALSO](#see-also) | [LICENSE](#license) | [AUTHOR](#author)

**Files:** [gistsite.py](#file-gistsite-py) | [Makefile](#file-makefile) | [pyproject.toml](#file-pyproject-toml)

## NAME

    gistsite - render konfig-style gists into a static html catalog

## SYNOPSIS

    python3 -B gistsite.py [-u USER] [-o DIR] [-c CSS] [--checks] [-h]

## OPTIONS

    -u --user  github user                       user=timm
    -o --out   output dir                         out=docs
    -c --css   stylesheet href for every page     css=https://timm.fyi/site.css
       --checks run self-tests (no network)
    -h --help  show the docstring

## DETECT

A gist is *curated* if one of its files is named `,<name>.md`. The
leading comma sorts that README to the top of the gist listing (see
konfig's style_gist). gistsite reads the GitHub gists API, keeps only
those gists, and takes `<name>` (comma + `.md` stripped) as the page
slug. Everything else -- scratch gists, snippets -- is skipped.

    ,xomo.md     -> xomo.html      (curated)
    ,nuff.md     -> nuff.html      (curated)
    README.md    -> skipped
    snippet.py   -> skipped

## OUTPUT

One `<name>.html` per curated gist (its rendered README) plus an
`index.html` roster:

    gist     what                                    src   updated
    nuff     tiny stdlib python tricks library       src   2026-06-12
    xomo     Monte-Carlo COCOMO-II + COQUALMO        src   2026-06-15

The `src` link points back to the gist on github; the gist name links
to its rendered page. Unauthenticated, the API allows 60 requests/hour
-- ample for a personal roster.

## TESTS

`--checks` runs every `test_*` (no network needed):

    test_curated   ,name.md is detected, slug strips comma + ext
    test_skip      a gist with no ,name.md is ignored
    test_pandoc    pandoc renders gfm to html
    test_wrap      a page carries its title + css href
    test_esc       html-special chars are escaped in the roster

## SEE ALSO

    konfig    http://tiny.cc/konfig   shared Makefile/boilerplate + styles
    nuff      http://tiny.cc/nuff     tiny stdlib python tricks (a catalog entry)
    xomo      http://tiny.cc/xomo     cocomo-ii + coqualmo    (a catalog entry)
    live      https://timm.fyi/gists/ the rendered catalog

## LICENSE

MIT. https://choosealicense.com/licenses/mit/

## AUTHOR

Tim Menzies, timm@ieee.org

# vim: ts=2 sw=2 sts=2 et :
# knobs only; shared targets live in $(KONFIG)/Makefile
KONFIG ?= ../konfig
APP    := gistsite
MAIN   := gistsite.py
EXT    := py
LANG   := python
SRC    := *.py
LINT   := ruff check gistsite.py
TOOLS  := python3:run pandoc:render ruff:lint
PKG    := python3 pandoc gawk ruff neovim tmux

$(KONFIG)/Makefile:
	@test -f $@ || { echo "missing konfig: git clone https://github.com/aiez/konfig $(KONFIG)"; exit 1; }
include $(KONFIG)/Makefile

OUT ?= docs   # for: make demo OUT=dir

demo: ## render the catalog into $(OUT)/ (hits the github gists api)
	@python3 -B gistsite.py -o $(OUT)

CHECKS: ## test: self-checks pass (no network)
	@python3 -B gistsite.py --checks | \
	  gawk -F'[ /]' '$$2==$$3 && $$3>0 && $$4=="ok"{f=1} END{exit !f}' \
	  && echo "ok checks"

test: ## run every UPPERCASE rule
	@gawk -F: '/^[A-Z][A-Z_]*:[^=]/ {print $$1}' $(MAKEFILE_LIST) | \
	  sort -u | while read t; do \
	    printf "\n=== %s ===\n" "$$t"; $(MAKE) -s $$t; done

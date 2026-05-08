# noxus-lab — interface to the lab.
# All non-trivial logic lives in bin/ so CI uses the exact same code.

SHELL := sh

ifeq ($(OS),Windows_NT)
PY := .venv/Scripts/python.exe
NOXUSLAB := .venv/Scripts/noxuslab.exe
else
PY := .venv/bin/python
NOXUSLAB := .venv/bin/noxuslab
endif

TOPIC ?= octopus cognition

.PHONY: help setup hello run kb chat ask list agents pull push lint fmt test typecheck ci clean new template-update

help:
	@echo 'use:'
	@echo '  hello            build a workflow, print its id'
	@echo '  run ID=<id>      run a workflow (TOPIC=... optional)'
	@echo '  kb [DOC=path]    create kb, ingest doc, search it'
	@echo '  chat [AGENT=id]  interactive conversation with a Noxus agent'
	@echo '  ask Q="..."      one-shot question (pipe-friendly)'
	@echo ''
	@echo 'browse:'
	@echo '  list             list workflows in the workspace'
	@echo '  agents           list agents in the workspace'
	@echo ''
	@echo 'sync:'
	@echo '  pull ID=<id>     fetch a workflow as a Python file under examples/'
	@echo '  push FILE=<p>    save a Python-defined workflow back to Noxus'
	@echo ''
	@echo 'dev:'
	@echo '  setup            create .venv, install deps, seed .env'
	@echo '  lint             ruff check + format --check'
	@echo '  fmt              ruff --fix + format'
	@echo '  test             pytest'
	@echo '  typecheck        pyright (warning-only)'
	@echo '  ci               same as CI: lint + test (run before pushing)'
	@echo '  clean            remove venv and caches'
	@echo '  new NAME=<dir>   scaffold a new project from this template'
	@echo '  template-update  pull updates from the upstream template'

setup:
	sh bin/setup

hello:
	$(PY) examples/01_hello.py

run:
	@test -n "$(ID)" || (echo 'usage: make run ID=<workflow_id> [TOPIC=...]' >&2; exit 2)
	$(PY) examples/02_run.py $(ID) "$(TOPIC)"

kb:
	$(PY) examples/03_kb.py $(DOC)

chat:
	$(NOXUSLAB) chat $(if $(AGENT),--agent $(AGENT)) $(if $(MODEL),--model $(MODEL))

ask:
	@test -n "$(Q)" || (echo 'usage: make ask Q="your question" [AGENT=id]' >&2; exit 2)
	$(NOXUSLAB) ask $(if $(AGENT),--agent $(AGENT)) $(if $(MODEL),--model $(MODEL)) "$(Q)"

list:
	$(NOXUSLAB) list

agents:
	$(NOXUSLAB) agents

pull:
	@test -n "$(ID)" || (echo 'usage: make pull ID=<workflow_id> [OUT=path.py]' >&2; exit 2)
	$(NOXUSLAB) pull $(ID) $(if $(OUT),--out $(OUT))

push:
	@test -n "$(FILE)" || (echo 'usage: make push FILE=examples/NN_x.py' >&2; exit 2)
	$(NOXUSLAB) push $(FILE)

lint:
	sh bin/lint

fmt:
	sh bin/fmt

test:
	sh bin/test

typecheck:
	sh bin/typecheck

ci: lint test

clean:
	sh bin/clean

new:
	@test -n "$(NAME)" || (echo 'usage: make new NAME=my-project' >&2; exit 2)
	$(NOXUSLAB) init --with-makefile $(NAME)

template-update:
	@if [ ! -f .noxuslab-template-version ]; then \
		echo 'no .noxuslab-template-version found; this is the upstream template itself.' >&2; exit 2; \
	fi
	@cur=$$(cat .noxuslab-template-version); \
	echo "current template version: $$cur"; \
	echo ""; \
	echo "to pull updates from upstream, run:"; \
	echo "  git remote add template https://github.com/AdvanceWorks/noxus-lab.git 2>/dev/null || true"; \
	echo "  git fetch template main"; \
	echo "  git merge template/main --allow-unrelated-histories"; \
	echo ""; \
	echo "for the CLI alone:  pip install -U noxuslab"

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

TOPIC ?= the Plan 9 operating system

.PHONY: help setup hello run kb pull push lint fmt test typecheck clean

help:
	@echo 'targets:'
	@echo '  setup            create .venv, install deps, seed .env'
	@echo '  hello            build a workflow, print its id'
	@echo '  run ID=<id>      run a workflow (TOPIC=... optional)'
	@echo '  kb [DOC=path]    create kb, ingest doc, search it'
	@echo '  pull ID=<id>     fetch a workflow as a Python file under examples/'
	@echo '  push FILE=<p>    save a Python-defined workflow back to Noxus'
	@echo '  lint             ruff check + format --check'
	@echo '  fmt              ruff --fix + format'
	@echo '  test             pytest'
	@echo '  typecheck        pyright (warning-only)'
	@echo '  clean            remove venv and caches'

setup:
	sh bin/setup

hello:
	$(PY) examples/01_hello.py

run:
	@test -n "$(ID)" || (echo 'usage: make run ID=<workflow_id> [TOPIC=...]' >&2; exit 2)
	$(PY) examples/02_run.py $(ID) "$(TOPIC)"

kb:
	$(PY) examples/03_kb.py $(DOC)

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

clean:
	sh bin/clean

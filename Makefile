# noxus-lab — interface to the lab.
# All non-trivial logic lives in bin/ so CI uses the exact same code.

SHELL := sh

ifeq ($(OS),Windows_NT)
PY := .venv/Scripts/python.exe
else
PY := .venv/bin/python
endif

TOPIC ?= the Plan 9 operating system

.PHONY: help setup hello run kb lint fmt clean

help:
	@echo 'targets:'
	@echo '  setup           create .venv, install deps, seed .env'
	@echo '  hello           build a workflow, print its id'
	@echo '  run ID=<id>     run a workflow (TOPIC=... optional)'
	@echo '  kb [DOC=path]   create kb, ingest doc, ask question'
	@echo '  lint            ruff check + format --check'
	@echo '  fmt             ruff --fix + format'
	@echo '  clean           remove venv and caches'

setup:
	sh bin/setup

hello:
	$(PY) examples/01_hello.py

run:
	@test -n "$(ID)" || (echo 'usage: make run ID=<workflow_id> [TOPIC=...]' >&2; exit 2)
	$(PY) examples/02_run.py $(ID) "$(TOPIC)"

kb:
	$(PY) examples/03_kb.py $(DOC)

lint:
	sh bin/lint

fmt:
	sh bin/fmt

clean:
	sh bin/clean

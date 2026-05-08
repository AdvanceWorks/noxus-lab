# Philosophy

Three rules. That's it.

## 1. The reader matters more than the writer

Code is read 10 000 times for every time it's written. Examples are
read 100 000 times. We optimise for the reader on their first day,
sitting in front of `01_hello.py`, with no mental model yet.

That means: top-level scripts, no `def main`, no `__future__`, no
abstractions until they pay rent. A file you can read top-to-bottom is
worth more than a file that's clever.

## 2. Small surface, sharp edges

The package exports two things you actually use: `workflow_to_python`
and a CLI (`pull`, `push`, `diff`, `chat`, `ask`, `list`, `agents`,
`show`, `init`, `version`). Everything else is private (`_term`,
`_slug`, `_topo_order`, `_net`, `_secrets`, `_audit`). When in doubt,
prefix with `_`. When in doubt about adding something, don't.

If a piece of logic appears twice in `examples/`, it might belong in
`noxuslab/`. If it appears once, it stays inline. If it never appears,
delete it.

## 3. Standard library first

We depend on `noxus-sdk` (the whole point) and `python-dotenv` (the
ergonomic floor). Everything else is stdlib. `runpy`, `argparse`,
`difflib`, `pathlib`, `re`. They've been stable since you were born and
will outlive the dependency you almost added.

The first question for any new dependency is: "what does this give us
that 30 lines of stdlib wouldn't?" If the answer isn't loud, the answer
is no.

---

## Corollaries

- **No Docker.** This is a Python CLI. `pip install noxuslab` and
  `make setup` work on Linux, macOS, and Windows (Git Bash). A
  Dockerfile would add a 200 MB layer for a tool that fits in
  500 lines. Ken Thompson didn't ship `cat` in a container.
- **No build step.** Hatchling is the build backend; the source is
  the artifact. No transpiler, no bundler, no codegen pre-pass.
- **No optional features behind feature flags.** If it's worth
  shipping, it's worth shipping unconditionally. If it isn't, delete
  it.

---

These rules came from people who built UNIX, C, Plan 9, and Go. They
work because they're true, not because of who said them. If you find a
better rule, propose it — but bring receipts.

# Security policy

## Reporting a vulnerability

Email **luis.tunes@advanceworks.ai** with details and a proof of
concept. Do **not** open a public GitHub issue. We acknowledge within
a few business days and aim to ship a fix within two weeks for
anything credible.

## Scope

- The `noxuslab` package and CLI in this repository.
- The example scripts under `examples/`.

## Out of scope

- The Noxus AI platform: report at https://noxus.ai/security
- The `noxus-sdk`: report at https://github.com/Noxus-AI/noxus-sdk

## Hardening notes

- `.env` is gitignored; the lab refuses to start without
  `NOXUS_API_KEY`.
- Pre-commit runs `gitleaks` and `detect-private-key`. Treat any
  leaked key as compromised; rotate immediately on the Noxus
  dashboard.
- `noxuslab push` and `noxuslab fmt` import target files with
  `runpy.run_path` in a fresh namespace (the SDK `Client` is stubbed
  during `fmt`). Only push code you wrote or reviewed.
- `noxuslab agents push` uses the same sandbox. The file's three
  module-level variables (`agent_name`, `agent_id`, `agent_settings`)
  are the entire contract.
- For shared machines, set `NOXUSLAB_SECRETS_CMD=<cmd>` to fetch
  `NOXUS_API_KEY` from a secrets manager instead of `.env`.
- Set `NOXUSLAB_AUDIT_LOG=/path/to/file` to append a JSONL audit line
  per CLI invocation (id, command, host, time_ms, exit code).

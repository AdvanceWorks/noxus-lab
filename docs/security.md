# Security policy

This is a learning sandbox, not production software. If you find a real
vulnerability — please email **luis.tunes@advanceworks.ai** with the details
and a proof of concept. Do not file a public issue first.

We will acknowledge within a few business days and aim to ship a fix
within two weeks for anything credible.

## Scope

- The `noxuslab` package and CLI in this repository.
- The example scripts under `examples/`.

## Out of scope

- The Noxus AI platform itself: report to https://noxus.ai/security
- The `noxus-sdk`: report at https://github.com/Noxus-AI/noxus-sdk

## Hardening notes

- `.env` is gitignored; the lab refuses to start without `NOXUS_API_KEY`.
- Pre-commit runs `gitleaks` and `detect-private-key` to keep secrets out
  of commits. Treat any leaked key as compromised; rotate immediately on
  the Noxus dashboard.
- `noxuslab push` imports the file with `runpy.run_path` in a fresh
  namespace. Only push code you wrote or reviewed.

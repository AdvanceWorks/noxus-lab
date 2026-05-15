# Environments — staging and production

This repo deploys to two Noxus tenants from one branch (`main`) with
no per-environment forks. Tenant selection is purely configuration:
swap `NOXUS_API_KEY` + `NOXUS_BACKEND_URL` and every push goes to the
right place. Workflows are idempotent (matched by name), so the same
commit can be safely deployed to both tenants in sequence.

## Local development

Keep one `.env.<name>` file per tenant. They are gitignored.

```
.env.staging
.env.prod
```

Each one sets at least:

```
NOXUS_API_KEY=...
NOXUS_BACKEND_URL=https://api.staging.your-tenant.noxus.ai   # or prod URL
OPENAI_API_KEY=...
```

Switch the active environment with the `noxuslab` CLI:

```
noxuslab env use staging   # copies .env.staging -> .env
noxuslab env use prod      # copies .env.prod    -> .env
noxuslab env               # show the currently active env
```

Then run anything that talks to the platform:

```
python scripts/deploy.py            # deploy all workspaces
python scripts/deploy.py pagamentos # deploy one workspace
```

The `make_client()` helper in `noxuslab` reads `NOXUS_API_KEY` (via
`_secrets.resolve_api_key()` — env, `.env`, or `NOXUSLAB_SECRETS_CMD`)
and `NOXUS_BACKEND_URL` from the active environment.

## CI/CD (GitHub Actions)

Two triggers, one workflow file (`.github/workflows/deploy.yml`):

| Trigger | Target |
| --- | --- |
| Push to `main` (after CI green) | `staging` (auto, no approval) |
| Tag matching `v*.*.*` | `production` (requires approval) |
| `workflow_dispatch` (manual) | Either, chosen at dispatch time |

The workflow injects the secrets of the target *GitHub Environment*
directly into the job — no `.env` file is written. The same code
that runs locally (`scripts/deploy.py` → `make_client()`) picks them
up from `os.environ`.

## One-time GitHub setup

In **repo Settings → Environments**, create two environments:

### `staging`

- No required reviewers, no deployment branch restrictions.
- Secrets:
  - `NOXUS_API_KEY`
  - `NOXUS_BACKEND_URL`
  - `OPENAI_API_KEY` (only if a deploy step needs it)

### `production`

- **Required reviewers**: 1 (yourself / release manager).
- **Deployment branches and tags**: restrict to `main` + tags matching
  `v*.*.*`. This ensures a stray feature branch cannot reach prod.
- Same three secrets, populated with prod values.

In **repo Settings → Branches**, protect `main`:

- Require status check `ci` to pass before merging.
- Require pull request review (optional for solo repos).

## Promoting staging → production

1. Confirm staging looks good after the auto-deploy.
2. Tag the same commit:

   ```
   git tag v1.4.0
   git push origin v1.4.0
   ```

3. The `deploy` workflow starts and pauses on the `production`
   environment, waiting for your approval.
4. Approve in the Actions UI. The same `scripts/deploy.py` runs with
   production secrets injected.

## Rollback

Workflows are matched by name, so `push_workflow` replaces them in
place. To roll back production to a previously known-good commit:

```
git tag -f v1.4.0 <previous-good-sha>
git push -f origin v1.4.0
```

Then re-approve the production deploy. The workflow IDs on the
platform do not change; only their definitions revert.

If you do not want to rewrite an existing tag, cut a fresh patch tag
on the older commit (`v1.4.1` pointing back at `v1.3.7`'s tree) and
let the normal pipeline ship it. Same end result, cleaner history.

## Adding a new environment (e.g. `qa`)

1. Create `.env.qa` locally; never commit it.
2. Add a `qa` GitHub Environment with its three secrets.
3. Extend the trigger logic in `.github/workflows/deploy.yml` — for
   example, a `release-candidate-*` tag pattern pointing at `qa`.
4. No code changes elsewhere; `make_client()` is environment-agnostic.

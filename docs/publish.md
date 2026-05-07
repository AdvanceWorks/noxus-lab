# publishing

## first push

From the repo root:

    git init -b main
    git add .
    git commit -m "init"
    git remote add origin <url>
    git push -u origin main

The `.gitignore` covers `.env`, `.venv`, caches and build artefacts.
Double-check before the first commit:

    git status --ignored | head
    git ls-files | xargs grep -l NOXUS_API_KEY ; true   # must be empty

## remote already initialised

If the remote was created with a default branch (README, license),
rebase first:

    git pull --rebase origin main
    git push -u origin main

## day-to-day

    git switch -c <topic>
    # edit, save
    make lint
    git commit -am "<imperative subject>"
    git push -u origin <topic>

Pre-commit (`pre-commit install`) runs ruff on staged files. CI
(`.github/workflows/ci.yml`) re-runs `bin/lint` on every push.

## undoing

- last commit, not pushed:    `git reset --soft HEAD~1`
- last commit, already pushed: `git revert HEAD && git push`

Never `push --force` to a shared branch.

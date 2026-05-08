# Quickstart — zero to running in 15 minutes

This guide assumes nothing. No Python, no Git, no terminal experience.
Follow it top to bottom.

---

## Step 1 — install three tools (once, ever)

Open **PowerShell** (press `Win`, type `powershell`, press Enter).

```powershell
# 1. Python
winget install Python.Python.3.12

# 2. Git
winget install Git.Git

# 3. Make
winget install GnuWin32.Make
```

Close PowerShell and open a fresh one after each install so the PATH
updates.

> **Mac?** Install [Homebrew](https://brew.sh), then:
> `brew install python git make`

---

## Step 2 — create your own copy of this project

1. Go to **https://github.com/AdvanceWorks/noxus-lab**
2. Click the green **"Use this template"** button → **"Create a new repository"**
3. Name it (e.g. `my-noxus-project`), set visibility to **Private**, click **Create**
4. Click the green **"Code"** button on your new repo → copy the URL

In PowerShell:

```powershell
git clone <paste URL here>
cd my-noxus-project
```

---

## Step 3 — install the project

```powershell
make setup
```

This creates a local Python environment and copies `.env`.

---

## Step 4 — add your API key

Open `.env` in Notepad:

```powershell
notepad .env
```

Replace `your_key_here` with your Noxus API key.
Get it at: **Noxus UI → Settings → Workspace → API Keys**.

---

## Step 5 — talk to an agent

```powershell
make chat AGENT=<agent-id>
```

Your team lead will share the agent ID. Type your question and press
Enter. Type `/exit` to quit.

```
you> What is the status of project Orion?
ai>  Based on the latest report, project Orion is in phase 2...
```

Or ask a single question without entering the chat:

```powershell
make ask Q="summarise the Q1 results" AGENT=<agent-id>
```

---

## That's it.

For more: `make help` lists everything you can do.

---

# CLI vs make — which and when?

> *"Have one tool do one thing well, and let other tools call it."*
> — Unix philosophy

`noxuslab` is the **tool**. `make` is a **shortcut menu** for people
inside this repo. They are not alternatives — `make` calls `noxuslab`
under the hood. Here is when to use each:

| Use `make ...` | Use `noxuslab ...` directly |
|---|---|
| You are inside this repo | You are in any directory — your own scripts, CI pipelines, other projects |
| You want muscle memory (`make chat`, `make pull`) | You want to compose with other tools: `noxuslab pull <id> -o - \| diff - local.py` |
| You are not writing code | You are writing a shell script or automating a task |
| You want to see all available commands (`make help`) | You need an exact flag not exposed by the Makefile |

The CLI is the real tool. `make` saves you from remembering long commands
when you are in one specific repo. The moment you leave that repo, or you
want to pipe output somewhere, or automate something — reach for
`noxuslab` directly.

```sh
# Make: convenient inside the repo
make pull ID=abc-123

# CLI: composable everywhere
noxuslab pull abc-123 -o - | wc -l
noxuslab diff abc-123 examples/NN_myflow.py && noxuslab push examples/NN_myflow.py
```

The CLI is also what a non-developer would `pip install` on a server or
in a CI job — `make` is for humans at keyboards.

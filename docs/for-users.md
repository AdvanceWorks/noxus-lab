# For Users — Talk to Your Team's AI

You don't need to write code. Your team's developer has already set up
AI agents with access to your knowledge bases, workflows, and tools.
You just talk to them.

## Setup (once)

    git clone <your-team-repo-url>
    cd <repo-name>
    make setup

Then edit `.env` — your team lead will give you the API key.

## Chat with an agent

    make chat AGENT=<agent-id>

Your team lead will share the agent ID. Once connected you can ask
questions in plain English:

```
you> What were our Q3 sales results?
ai>  Based on the Q3 report in the knowledge base, total revenue was...

you> Summarize the onboarding workflow
ai>  The onboarding workflow has 5 steps: ...

you> /exit
```

## One-shot question

    make ask Q="What are the top 3 action items from the last meeting?" AGENT=<id>

Prints the answer and exits. Great for quick lookups.

## Commands in chat

| Command  | What it does |
|----------|--------------|
| `/exit`  | End the conversation |
| `/clear` | Start a fresh conversation (forget previous messages) |
| `/quit`  | Same as /exit |

## What can the agent do?

Whatever your builder configured. Common capabilities:

- **Search knowledge bases** — ask about documents your team uploaded
- **Run workflows** — trigger automated processes via natural language
- **Web research** — look up current information online
- **Execute code** — run calculations or data analysis

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "NOXUS_API_KEY not set" | Edit `.env` file, paste your key |
| "not a uuid" | Check the agent ID with your team lead |
| Connection timeout | Check your internet; the Noxus backend may be down |
| Empty responses | The agent might need more context — try rephrasing |

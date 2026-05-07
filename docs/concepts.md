# concepts

Just enough vocabulary to read the SDK without confusion.

## workspace
Tenant boundary. Authenticate with its API key.

## flow (workflow)
Directed graph of `nodes` and `edges`. Built in code with
`WorkflowDefinition`, saved with `client.workflows.save(...)`. Same
object editable in the visual canvas.

## agent (co-worker)
Chat-style runtime: model + system prompt + tools + KBs. Tools include
`WebResearchTool`, `KnowledgeBaseQaTool`, `WorkflowTool`.

## knowledge base
RAG store. Documents are ingested, chunked, embedded, indexed. Hybrid
retrieval (vector + FTS) with optional reranking.

## conversation
Chat session, stateful, can call tools. Optionally bound to an agent.

## run
One execution of a flow. Async; `run.wait()` blocks. Has `.status`, `.output`.

## worker pool
Where runs execute. Platform-level concern; not your problem from the SDK.

## plugin / custom node
Python package registering new node types (CTT-internal: Go Contact,
IOS, Doxenter). Out of scope here.

## entry points

- `client.workflows` — CRUD flows
- `client.agents` — CRUD agents
- `client.knowledge_bases` — CRUD KBs, ingest docs
- `client.conversations` — chat sessions
- `client.runs` — list/inspect runs
- `client.get_nodes()` — introspect node types
- `client.get_models()` — available LLMs

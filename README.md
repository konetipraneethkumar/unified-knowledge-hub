# Unified Knowledge Hub

**Privacy-Aware Hybrid AI Search and Retrieval Platform**

Unified Knowledge Hub helps users discover information across authorized data sources—Gmail, Google Drive, Google Classroom, and Local Storage—without permanently storing the original documents in a central database. It indexes selected metadata, concise summaries, keywords, embeddings, and source locators to support unified keyword and semantic search. When a user needs the original resource, the system can direct them to it or retrieve content through authorized access, subject to the source's availability and permissions.

## Start here

- [Project context and architecture](docs/PROJECT_CONTEXT.md) — vision, scope, privacy, connectors, architecture, and roadmap.
- [Agent instructions](AGENTS.md) — repository rules for Codex and compatible coding agents.
- [Development workflow](docs/DEVELOPMENT_WORKFLOW.md) — small tasks, acceptance criteria, implementation, review, and reporting.
- [Testing strategy](docs/TESTING_STRATEGY.md) — test layers, security/reliability cases, and honest verification.
- [Task template](docs/TASK_TEMPLATE.md) — reusable engineering task and agent prompt.

## Non-negotiable boundaries

1. Exactly four supported connectors: Gmail, Drive, Classroom, Local Storage.
2. Process permitted source content temporarily; do not permanently retain complete source documents, email bodies, attachment contents, or raw extracted text as indexed content.
3. Treat summaries, metadata, and embeddings as potentially sensitive.
4. Support multiple registered local devices with independent authorization, reachability, and sync state.
5. Never claim indexing, opening, testing, or integration succeeded without evidence.
6. The specification describes the target product, not proof of current implementation.

## Recommended first step

Read the project context and agent instructions, inspect the repository, run relevant existing tests, and produce a short evidence-based gap analysis. Do not begin with a large rewrite or attempt all connectors simultaneously.

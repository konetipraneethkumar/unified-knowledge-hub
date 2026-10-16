# Development Workflow: Small Tasks, Verified Changes

This workflow keeps coding-agent work focused, reviewable, and economical while protecting architecture and privacy.

## 1. The cycle

**Understand → Inspect → Specify → Implement → Test → Review → Report → Checkpoint**

Do not ask an agent to “finish the whole project” in one prompt. Large tasks hide assumptions, produce large diffs, make failures hard to localize, and consume context on unrelated work.

## 2. Step-by-step

### Step 1 — Choose one outcome

Good tasks:
- Make local resource upserts idempotent for duplicate events.
- Add a test proving users cannot retrieve another user's resource.
- Show an offline indicator when a local resource's owning device is unreachable.
- Add a validated Gmail message URL builder with unit tests.

Poor tasks:
- Finish all connectors.
- Make the backend production-ready.
- Rewrite the search system.
- Improve the entire application.

### Step 2 — Inspect before coding

Identify relevant files, existing abstractions, models/migrations, tests and commands, current behavior, and whether the feature already exists. Avoid edits before inspection except for explicitly trivial documentation-only changes.

### Step 3 — Define observable acceptance criteria

Example for duplicate local events:
- Reprocessing the same resource identity does not create a duplicate.
- A changed fingerprint refreshes the approved indexed representation.
- A failed refresh preserves the last-known-good representation.
- Tests cover insert, duplicate event, update, and failure.
- Existing relevant tests still pass.

Avoid vague criteria like “works well” or “secure” unless converted into checks.

### Step 4 — Set boundaries

State the intended scope, excluded changes, whether schema changes are allowed, expected tests, dependency constraints, and privacy/auth implications. If inspection reveals the correct implementation belongs elsewhere, explain the deviation rather than forcing a bad file-level plan.

### Step 5 — Implement the smallest coherent change

Reuse existing patterns, avoid hypothetical abstractions, keep contracts consistent, and avoid unrelated refactoring. Update docs only when decisions or behavior change.

### Step 6 — Verify

Run focused tests first, then broader relevant checks. Changes to schema, auth, search, or connector flows need integration coverage when supported. If tests cannot run, report the exact command and blocker.

### Step 7 — Review the diff

Check unrelated changes, security/auth regressions, sensitive data in logs or persistence, failure-path cleanup, idempotency, migration correctness, meaningful assertions, hard-coded secrets, mock-only behavior, and false completion claims.

### Step 8 — Report and checkpoint

Report what changed, files changed, acceptance criteria met/unmet, exact test commands and outcomes, limitations/blockers, and the next smallest task. Preserve a known-good checkpoint before significant follow-up work.

## 3. Task sizing

A task is well-sized when it addresses one behavior or tightly coupled change, has a reviewable diff, has isolatable tests, and can be debugged without understanding the entire system. Split tasks that combine unrelated connectors, large UI/backend redesigns, or multiple independently testable outcomes.

## 4. Priority order

1. Broken behavior blocking the core vertical slice.
2. Security, privacy, and data-integrity defects.
3. Missing tests for critical existing behavior.
4. Reliability and sync correctness.
5. Search relevance and usability.
6. Polish and speculative enhancements.

Do not start another connector while the local indexing/search/routing flow remains unverified unless a deliberate reason is documented.

## 5. Multiple agents

Agents do not automatically share context or agree on architecture. Give each the same repo context and task-specific acceptance criteria. Avoid overlapping edits to the same files. Have one owner integrate and review changes. Do not merge conflicting changes just because both agents report success.

## 6. Cost and context management

- Keep stable rules in repository documents.
- Send only relevant task context, files, constraints, and criteria.
- Request targeted inspection rather than a large repository-wide essay every time.
- Do not repeatedly ask for the whole project summary unless context has been lost.
- Run focused tests first, then broader checks before merging.
- Do not retry without learning from the previous failure.
- Ask for evidence, not speculation.
- Reuse known-good implementation and test patterns.

## 7. Standard implementation prompt

“Read AGENTS.md and relevant sections of docs/PROJECT_CONTEXT.md, docs/DEVELOPMENT_WORKFLOW.md, and docs/TESTING_STRATEGY.md. Task: [one specific outcome].

First inspect the existing implementation and tests. Report relevant files, current behavior, smallest proposed change, and risks.

Acceptance criteria:
- [observable criterion 1]
- [observable criterion 2]
- [observable criterion 3]

Boundaries:
- No unrelated features.
- Do not rewrite working code without evidence.
- Preserve privacy, authorization, and data-retention rules.
- Do not add dependencies without justification.
- Add or update focused tests.

Implement only after inspection. Run relevant tests and report exact commands and actual results. Review the diff and report changed files, limitations, and unmet criteria. Never claim a test ran if it did not.”

## 8. Completion vocabulary

- **Implemented and tested:** criteria met and relevant tests actually passed.
- **Implemented but not fully tested:** code exists, meaningful validation remains.
- **Partially implemented:** criteria remain unmet.
- **Blocked:** a concrete dependency, credential, service, or decision prevents progress.
- **Not implemented:** no working implementation exists.

“Code written” and “feature complete” are not synonyms.
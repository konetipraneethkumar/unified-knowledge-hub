# Engineering Task Template

Copy this template for each implementation task. Keep each task small enough to review and verify independently.

## Task title
[One specific behavior or outcome]

## Context
[Why this task matters; only the relevant project context.]

## Current behavior
[Observed behavior based on repository inspection. If unknown, inspect before implementation.]

## Desired behavior
[Required behavior without prescribing unnecessary implementation details.]

## Acceptance criteria
- [ ] [Observable, testable outcome]
- [ ] [Observable, testable outcome]
- [ ] [Failure or authorization behavior]
- [ ] [Relevant regression tests pass]

## Scope
Included:
- [Relevant component or behavior]

Excluded:
- [Unrelated connectors, refactors, UI changes, or infrastructure]

## Constraints
- Follow AGENTS.md.
- Consult docs/PROJECT_CONTEXT.md and relevant workflow/testing docs.
- Preserve privacy, data-retention, authorization, and multi-device rules.
- Reuse existing abstractions unless evidence supports a change.
- Do not add dependencies without justification.
- Do not claim verification that did not occur.

## Inspection required
Before editing, identify relevant source files, models/schemas/migrations, existing tests and commands, risks, assumptions, and compatibility concerns.

## Verification plan
- [ ] Focused unit/service tests
- [ ] Relevant integration tests, if supported
- [ ] Migration/API/frontend checks, if affected
- [ ] Diff reviewed for unrelated changes and security/privacy issues

## Final report
1. Summary of change.
2. Files changed.
3. Acceptance criteria met and unmet.
4. Exact commands run and actual results.
5. Limitations, blockers, and follow-up work.
6. Status: Implemented and tested / Implemented but not fully tested / Partially implemented / Blocked / Not implemented.

## Suggested agent prompt

Read AGENTS.md and the relevant sections of docs/PROJECT_CONTEXT.md, docs/DEVELOPMENT_WORKFLOW.md, and docs/TESTING_STRATEGY.md.

Inspect the current implementation before editing. Explain the smallest proposed change and any risks. Implement only the task above, add focused tests, run relevant tests, review the diff, and report actual results. Do not make unrelated changes or claim verification that did not occur.
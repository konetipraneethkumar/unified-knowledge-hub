# Testing Strategy

## 1. Purpose

Tests establish that Unified Knowledge Hub behaves correctly, protects private data, handles failures, and routes users to the right source. Passing unit tests alone does not prove an end-to-end connector or production deployment works.

## 2. Principles

- Test observable behavior and public contracts.
- Add regression tests for fixed bugs.
- Cover success, invalid input, authorization failure, and important failure paths.
- Keep unit tests deterministic and independent of external services.
- Use fakes/mocks at provider boundaries in unit tests, and integration tests for real database/framework behavior where practical.
- Use synthetic test data; never commit private email/document content or credentials.
- Do not weaken assertions or delete tests to make a suite pass.
- Report exact commands and actual outcomes.
- Distinguish coverage from correctness and integration readiness.

## 3. Test layers

### A. Unit tests

Test pure functions and validation, resource identity/deduplication, metadata normalization, embedding configuration/dimensions, ranking/RRF, URL validation, local path authorization, retry/state transitions, and privacy cleanup helpers. Tests should be fast and deterministic.

### B. API and service tests

Test authentication/session behavior, user ownership, connector registration/disconnection, device pairing/revocation, resource operations, search filtering, sync/checkpoint transitions, and sanitized errors. Explicitly test that one user cannot read, modify, delete, or open another user's resource.

### C. Database integration tests

Use the database engine/extensions required by the feature. PostgreSQL/pgvector behavior must be tested in a compatible environment; SQLite does not prove vector-query behavior.

Verify clean Alembic migrations, unique constraints, idempotent upserts, rollback, embedding dimension compatibility, ownership filters, checkpoint safety, and preservation of last-known-good indexed data.

### D. Connector contract tests

Use provider fakes or synthetic responses to test pagination, duplicate events, changed/deleted/inaccessible resources, expired credentials, quotas/rate limits, unsupported files, extraction failures, retry/reconciliation, stable IDs, correct routing, and absence of raw content in logs/index records.

Live provider tests may require credentials and should be separated from the default offline suite. Never commit secrets or private fixtures.

### E. Local agent tests

Test authorized-root-only scanning, rejection of outside paths, create/update/move/rename/delete detection, duplicate watcher events, offline behavior, authenticated and expiring open requests, owning-device routing, and safe handling of traversal/symlink cases under the platform policy.

### F. Search quality tests

Maintain a small synthetic evaluation dataset with queries, relevant resource IDs, and expected ranking constraints. Test exact keyword retrieval, semantic paraphrases with real embeddings, user/source filters, duplicate linking, and evidence-grounded explanations.

Mock embeddings can test data flow but must not be used to claim semantic-search quality.

### G. End-to-end tests

Verify at least one complete local vertical slice:
1. Authenticate a user.
2. Register a local device.
3. Authorize a test folder.
4. Index a synthetic supported file.
5. Confirm only approved indexed fields persist.
6. Search by exact keyword.
7. Search a paraphrase using the real configured embedding provider.
8. Verify resource identity and ownership.
9. Open the original through the owning device agent.
10. Simulate an offline device and verify honest availability messaging.
11. Update/delete the source and verify reconciliation.

Add connector-specific end-to-end scenarios as each connector is implemented. Do not claim an untested connector is complete.

## 4. Privacy and security regression tests

Test:
- Cross-user resource access is denied.
- Expired/revoked credentials are denied.
- Unauthorized local roots and path traversal are rejected.
- Unsafe source URLs are rejected.
- Raw extracted content is not persisted as indexed content.
- Temporary files are cleaned after success and failure.
- Secrets and raw private content do not appear in logs.
- Disconnect/deletion policies are applied.
- External AI provider use follows explicit configuration.
- Open requests are authenticated, authorized, scoped, and time-limited.

Assert persisted records and side effects, not only that helper functions were called.

## 5. Synchronization and reliability tests

Test duplicate events, source updates, deletion/revocation, reconciliation after missed notifications, checkpoint safety, last-known-good preservation, bounded retries, freshness/reachability separation, offline cache behavior, and reconnection recovery.

## 6. Discovering and running commands

Inspect the repository's actual configuration before choosing commands. Identify:
- Python test framework/configuration.
- Dependency installation method.
- Required environment variables.
- Database and vector-extension requirements.
- Frontend package manager and scripts.
- CI workflow commands.

Run the narrowest relevant tests first, then broader relevant tests, migration checks, lint/type checks, builds, or integration tests when supported. Do not invent commands or run destructive database operations against user data.

## 7. Reporting results

Every implementation report includes:
- Exact commands executed.
- Passed/failed/skipped counts where available.
- Failures and whether they appear related to the change.
- Tests not run and the reason.
- Missing services or credentials.
- Remaining acceptance criteria.

Never say “all tests pass” if only focused tests ran. Old output is not evidence for the current revision; rerun against the current code.

## 8. Release readiness

Before describing an integrated workflow as release-ready, verify relevant unit/API and database integration tests, privacy/security regressions, the critical end-to-end flow, connector-specific tests for each claimed connector, clean migrations, offline/failure behavior, real frontend/backend integration, and documented configuration/limitations.

If any requirement is unmet, report the exact status without overstating readiness.
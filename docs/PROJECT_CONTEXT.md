# Unified Knowledge Hub — Project Context

**Purpose:** Shared product and engineering reference for the owner, contributors, and coding agents.

**Status:** Target specification, not proof that every feature exists. Verify code, tests, CI, and runtime before reporting implementation status.

## 1. Product definition

Unified Knowledge Hub is a privacy-first personal knowledge discovery and source-routing system. It provides one search interface across exactly four authorized sources:

1. Gmail
2. Google Drive
3. Google Classroom
4. Local Storage

The system indexes approved metadata, concise summaries, keywords, embeddings, stable source identifiers, and routing information. Users search by meaning or exact terms, discover likely relevant resources, understand why a result matched, and open the original when accessible.

It is not a replacement for source applications or a permanent archive of complete personal documents.

### Product promise

“Search once, discover relevant resources across connected sources, and open the original wherever it is accessible.”

### Primary use cases

- Find DBMS notes about normalization or BCNF.
- Locate an assignment or course material.
- Find emails related to a project or submission.
- Discover PDFs about authentication or networking.
- Locate local files using natural-language descriptions.
- Search indexed resources while a source or local device is temporarily unavailable.

### Non-goals unless explicitly approved

- Any connector beyond the four named above.
- Permanent storage of complete source content.
- Guaranteed access to every resource visible in a provider UI.
- Universal paragraph-level or scroll-position deep links.
- Full-document question answering without evidence in an explicitly designed retrieval flow.
- Unnecessary agent frameworks or distributed infrastructure before the core workflow works.

## 2. Product invariants

1. Only the four approved connectors are in scope.
2. Authorization is checked before source access and for relevant search/routing operations.
3. Permitted source content is processed temporarily and discarded after indexing.
4. Summaries and embeddings are potentially sensitive.
5. The index is a derived representation, not a copy of the original.
6. Results do not invent facts or overstate match certainty.
7. Routing accurately represents access, fallback, and offline state.
8. Device reachability, sync health, source permission, and index freshness are distinct.
9. Repeated events are safe and idempotent.
10. Failed refreshes do not silently destroy the last-known-good index.
11. Actual repository behavior and executed tests determine implementation status.
12. Work proceeds as small, verifiable changes.

## 3. Core user workflow

1. User signs in and connects an authorized source or registers a local device.
2. System discovers permitted resources.
3. It retrieves only content needed and permitted for indexing.
4. It extracts and cleans content temporarily.
5. It generates a concise summary and approved search representations.
6. It persists approved metadata, summary, keywords, embedding, stable identity, locator, and sync state.
7. It removes temporary extracted content, including on error paths.
8. User submits a natural-language or keyword query.
9. Backend applies ownership/source filters and performs keyword plus semantic retrieval.
10. UI shows ranked results, source information, match explanation, freshness/availability, and Open Original.
11. Router opens the resource or reports the actual limitation.

### Search versus answering

The primary product is resource discovery and routing. If a summary only says “database notes,” the system cannot claim it verified a document's definition of BCNF. It may show the resource as a likely match, explain available evidence, and open the source. Any future content-answering path requires separate grounding, privacy, retrieval, and evaluation requirements.

## 4. Connector contracts and limitations

### 4.1 Gmail

- Use OAuth with least-privilege scopes.
- Discover permitted messages and threads.
- Index approved metadata and concise summaries.
- Temporarily process permitted message content and supported attachments where needed.
- Store stable source IDs and a valid message/thread locator.
- Use available notifications, polling, and reconciliation.
- Handle revoked permissions, missing messages, quotas, unsupported attachments, and expired checkpoints.

Route to the relevant message/thread when possible. A stored link does not guarantee continued access.

### 4.2 Google Drive

- Discover permitted files and metadata.
- Temporarily process supported file formats.
- Store approved summaries, keywords, embeddings, source identity, and routing link.
- Detect changes with available change feeds/notifications plus reconciliation.
- Handle shared drives, permissions, export formats, quotas, unsupported files, and moved/deleted resources.

Route to the original file when the connected account still has access.

### 4.3 Google Classroom

- Discover accessible courses, announcements, coursework, materials, and supported resource links.
- Process permitted content temporarily.
- Preserve relationships between Classroom items and underlying Drive files.
- Avoid treating the same underlying file as unrelated duplicates.
- Route to the most precise valid resource destination.

API access may not cover every UI-visible resource, and exact deep links may not exist for every resource. Report unsupported/inaccessible items and describe fallbacks honestly.

### 4.4 Local Storage

- Run an agent on each registered device.
- Scan only user-authorized folder roots.
- Process supported files temporarily.
- Persist approved indexed representations, not full extracted text.
- Detect create, update, move, rename, and delete events with watchers where available and periodic reconciliation.
- Open local files only through the authenticated agent on the owning device.
- Support multiple devices with separate credentials, health, and sync state.

The owning device must be reachable, the agent running, and authorization valid to open a file. Cached search metadata may remain available while the device is offline.

## 5. Privacy and data lifecycle

### Persistent data permitted subject to minimization and authorization

- Provider/account/resource IDs.
- Approved metadata such as title, type, permitted sender/course details, and timestamps.
- Concise summaries and approved keywords.
- Embeddings of approved indexed text.
- Source locators and routing metadata.
- Sync checkpoints, timestamps, status, and sanitized error codes.
- Device identity and health state.
- Audit events that avoid raw private content.

### Do not permanently retain as indexed content

- Full email bodies.
- Full original documents.
- Complete attachment content.
- Raw extracted text.
- Temporary processing copies.

### Required handling

- Minimize retrieval and temporary disk writes.
- Use restricted temporary storage when disk is necessary.
- Clean up after success and failure.
- Do not log secrets or raw private content.
- Define deletion behavior for source removal, connector disconnection, user deletion, and device deregistration.
- Treat summaries, embeddings, and metadata as sensitive derived data.
- Do not send private content to external LLM/embedding providers unless the provider and data flow are explicitly configured and approved.

Pattern-based redaction reduces risk but cannot guarantee complete PII removal.

## 6. Architecture

### Frontend
Intended stack: React, TypeScript, Vite. Responsibilities: authentication, connector/device management, unified search, result explanations, freshness/availability indicators, routing, and useful error states. Mock UI data does not count as a finished integration.

### Backend API
Intended stack: Python, FastAPI, Pydantic/Pydantic Settings, SQLAlchemy. Responsibilities: authentication, authorization, connector lifecycle, device registration, ingestion, indexing, search, sync orchestration, routing, audit, and error handling.

### Persistence
Intended stack: PostgreSQL, pgvector, SQLAlchemy, Alembic. SQLite may be suitable for some tests/development, but PostgreSQL/pgvector behavior requires compatible integration tests.

### Local agent
Responsibilities: authenticated registration, authorized-root enforcement, scanning, change detection, temporary extraction, index synchronization, health reporting, and authenticated open requests. A web server alone cannot open arbitrary files on another computer.

### Search
Hybrid retrieval combines keyword and vector results; Reciprocal Rank Fusion (RRF) is a candidate method. Test ranking with realistic queries and relevant/non-relevant examples. Mock embeddings test plumbing, not semantic quality. Real embedding configuration must validate model and dimension compatibility.

## 7. Core data entities

Adapt to existing code rather than creating duplicates:
- User
- ConnectorAccount
- Device
- DeviceCredential
- PairingCode
- IndexedResource
- ResourceSummary
- ResourceEmbedding
- ResourceSyncState
- SyncJob
- SyncCheckpoint
- AuditEvent

Resource identity should be scoped to provider and account, for example provider + account ID + provider resource ID. Keep resource identity, summary, embedding, sync state, and locator logically clear.

Classroom items may point to Drive files. Preserve relationships and deduplicate/link appropriately.

## 8. Multi-device model

Each device should have a stable ID, revocable credentials, authorized roots, agent status, last-seen timestamp, last successful sync, sync health, and time-limited pending open requests where needed.

Keep separate:
- **Reachability:** can the device be contacted now?
- **Agent health:** is the agent functioning?
- **Sync health:** can it synchronize?
- **Index freshness:** how current is the index?
- **Source authorization:** is access still permitted?

An old successful sync does not prove current reachability. When offline, cached indexed information may remain searchable under the retention policy, but the original must be marked unavailable. Never claim it opened.

## 9. Synchronization and integrity

Use notifications/watchers where available, polling, and periodic reconciliation. Events can be delayed, duplicated, missed, or expire.

Required principles:
- Idempotent upserts and stable source identity.
- Bounded retry/backoff.
- Checkpoint advancement only after durable commits.
- Transactions for related persistence.
- Last-known-good index preservation.
- Explicit deletion and revoked-access handling.
- No partial replacement of valid data by a failed refresh.
- Structured errors without private content.

Suggested fields:
- `last_sync_attempt_at`
- `last_successful_sync_at`
- `last_indexed_at`
- `source_modified_at`
- `last_full_reconciliation_at`
- `sync_status`
- `last_error_code`
- `last_error_at`

Freshness and availability must be modeled independently.

## 10. Open Original routing

Each result should carry a typed, validated route:
- Gmail message/thread destination.
- Drive file destination.
- Classroom resource destination or explicit fallback.
- Local resource identity, owning device ID, and authenticated agent routing.

Validate provider URLs; avoid arbitrary URL forwarding. Resolve local paths only inside authorized roots. Local open requests must be authenticated, authorized, scoped to the user/device/resource, and time-limited. Do not claim success before the owning agent confirms it.

Exact paragraph/scroll-position routing cannot be guaranteed across all connectors.

## 11. Security requirements

- User/tenant isolation in APIs, queries, jobs, and routing.
- Least-privilege OAuth.
- Secure credential storage and revocation.
- Authentication consistent with existing project patterns.
- Authorized local roots and safe path resolution.
- URL validation and SSRF protection.
- Safe extraction limits and file validation.
- No secret or raw source-content logging.
- Auditable security-sensitive actions.
- Safe deletion/disconnect semantics.
- Tests for cross-user access, revoked credentials, unauthorized paths, expired requests, and failure paths.

## 12. Roadmap

Recommended order; verify before rebuilding:
1. Audit repository, tests, migrations, and frontend/backend integration.
2. Complete one real local-file indexing → search → open vertical slice.
3. Configure real embeddings and measure semantic retrieval.
4. Harden idempotency, deletion, recovery, freshness, and multi-device behavior.
5. Implement and verify Drive.
6. Implement and verify Gmail.
7. Implement and verify Classroom and resource relationships.
8. Complete UI integration and routing.
9. Test security, privacy, failure, and end-to-end behavior.

If a phase is already complete and verified, record evidence and move on.

## 13. Definition of done

Users can search authorized resources across all four sources, discover useful matches by keyword and meaning, understand why a resource matched, and open originals when accessible. The system accurately displays freshness and availability, supports multiple local devices, recovers from failures without corrupting the index, and enforces authorization and the content-retention policy.

Code existing is not enough: acceptance criteria and appropriate test evidence are required.
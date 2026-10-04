# Connector ingestion

Connector sync is an ingestion stage only. It reads authorized sources, extracts
text, redacts credential-like content, hashes items to avoid unnecessary
reprocessing, stores owner-scoped knowledge items, and updates/removes items on
the next complete sync. LLM-based retrieval and frontend connector controls are
separate follow-up work.

## Sync API

After connecting a source, the backend queues an initial sync. A signed-in
client can request another sync with:

```http
POST /api/v1/connectors/{connector_id}/sync
Authorization: Bearer <access_token>
```

The response reports `processed`, `skipped`, `failed`, and `deleted` counts.
Per-item failures are included in `errors`; a source-level failure returns an
HTTP error and leaves the connector marked as errored. The endpoint is
user-scoped, so a user cannot sync another user's connector.

## Sources

- **Local files:** The backend scans the connector's authorized directory under
  `LOCAL_STORAGE_ROOT`. The backend must be able to read that directory. A
  browser cannot expose arbitrary paths to a remote backend; a hosted deployment
  needs a local desktop/agent upload flow before it can read files from a user's
  device.
- **Google Drive:** Imports supported text, PDF, Office, and Google Docs,
  Sheets, and Slides exports. Individual downloaded files are limited to 25 MB.
- **Gmail:** Imports message subject, sender, date, and text body. Attachments are
  not yet imported.
- **Google Classroom:** Imports coursework, course materials, and announcements
  as text, including linked resource titles/URLs. Linked Drive file contents
  require a separate Drive connector.

For Google sources, configure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and
the matching OAuth callback URLs in `backend/.env`. Enable the Google Drive API,
Gmail API, and Classroom API in the associated Google Cloud project. Classroom
re-authorization is required to grant the coursework/material/announcement
read-only scopes used by ingestion. Set `CONNECTOR_TOKEN_ENCRYPTION_KEY` to a
Fernet key generated with
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
Never commit OAuth secrets or the generated encryption key.

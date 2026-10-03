import unittest

from app.utils.privacy_filter import (
	ALLOWED_FILE_METADATA_FIELDS,
	filter_file_content,
	filter_file_metadata,
)


class PrivacyFilterTests(unittest.TestCase):
	def test_allows_retrieval_metadata_and_drops_unapproved_fields(self):
		metadata = {
			"path": "C:/notes/project.md",
			"filename": "project.md",
			"extension": ".md",
			"size": 128,
			"created_time": "2026-09-30T10:00:00Z",
			"modified_time": "2026-09-30T10:30:00Z",
			"mime_type": "text/markdown",
			"content_hash": "sha256-digest",
			"content": "raw document contents",
			"raw_content": "raw document contents",
			"summary": "content-derived summary",
			"password": "not-allowed",
			"access_token": "not-allowed",
			"arbitrary": "not-allowed",
		}

		filtered = filter_file_metadata(metadata)

		self.assertEqual(
			set(filtered),
			ALLOWED_FILE_METADATA_FIELDS,
		)
		self.assertEqual(filtered["filename"], "project.md")
		self.assertEqual(filtered["content_hash"], "sha256-digest")
		self.assertNotIn("content", filtered)
		self.assertNotIn("password", filtered)
		self.assertNotIn("access_token", filtered)

	def test_rejects_credential_patterns_in_allowed_string_values(self):
		credential_values = (
			"notes_password=hunter2.txt",
			"document_access_token:abc123.txt",
			"notes_token=abc123.txt",
			"Authorization: Bearer abc123",
			"-----BEGIN PRIVATE KEY-----",
		)

		for filename in credential_values:
			with self.subTest(filename=filename):
				self.assertIsNone(
					filter_file_metadata(
						{"path": f"C:/files/{filename}", "filename": filename}
					)
				)

	def test_redacts_quoted_and_multiline_credentials_from_document_text(self):
		filtered = filter_file_content(
			'{"password": "a value with spaces", "api_key": "secret-value"}'
		)

		self.assertNotIn("a value with spaces", filtered)
		self.assertNotIn("secret-value", filtered)
		self.assertEqual(filtered.count("[REDACTED]"), 2)


if __name__ == "__main__":
	unittest.main()
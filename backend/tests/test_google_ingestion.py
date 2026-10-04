import base64
import unittest

from app.sync.google import (
	_classroom_text_document,
	_fetch_drive_documents,
	_gmail_body,
	_gmail_message_document,
)


class GoogleIngestionTests(unittest.TestCase):
	def test_drive_exports_supported_google_docs_and_skips_other_types(self):
		class Api:
			def get_json(self, url, params):
				self.list_url = url
				self.list_params = params
				return {
					"files": [
						{
							"id": "doc-1",
							"name": "Project notes",
							"mimeType": "application/vnd.google-apps.document",
							"webViewLink": "https://drive.google.com/file/d/doc-1",
						},
						{
							"id": "folder-1",
							"name": "Folder",
							"mimeType": "application/vnd.google-apps.shortcut",
						},
					]
				}

			def get_bytes(self, url, params):
				self.export_url = url
				self.export_params = params
				return b"notes from Google Docs"

		api = Api()
		documents = _fetch_drive_documents(api)

		self.assertEqual(len(documents), 1)
		self.assertEqual(documents[0].source_item_id, "doc-1")
		self.assertEqual(documents[0].file_extension, ".txt")
		self.assertEqual(documents[0].content, "notes from Google Docs")
		self.assertEqual(api.export_params, {"mimeType": "text/plain"})
		self.assertEqual(api.list_url, "https://www.googleapis.com/drive/v3/files")

	def test_gmail_extracts_plain_text_and_message_metadata(self):
		body = base64.urlsafe_b64encode(b"Meeting notes for the project").decode().rstrip("=")
		message = {
			"id": "message-1",
			"threadId": "thread-1",
			"sizeEstimate": 96,
			"payload": {
				"headers": [
					{"name": "Subject", "value": "Project meeting"},
					{"name": "From", "value": "member@example.com"},
					{"name": "Date", "value": "Sun, 04 Oct 2026 10:00:00 +0000"},
				],
				"mimeType": "text/plain",
				"body": {"data": body},
			},
		}

		document = _gmail_message_document("message-1", message)

		self.assertEqual(document.source, "gmail")
		self.assertEqual(document.source_item_id, "message-1")
		self.assertEqual(document.title, "Project meeting")
		self.assertIn("Meeting notes for the project", document.content)
		self.assertEqual(document.location, "https://mail.google.com/mail/u/0/#all/thread-1")
		self.assertIsNotNone(document.modified_at)

	def test_gmail_prefers_plain_text_over_html_and_removes_scripts(self):
		plain = base64.urlsafe_b64encode(b"Visible text").decode().rstrip("=")
		html = base64.urlsafe_b64encode(
			b"<p>HTML body</p><script>secret()</script>"
		).decode().rstrip("=")
		body = _gmail_body(
			{
				"mimeType": "multipart/alternative",
				"parts": [
					{"mimeType": "text/plain", "body": {"data": plain}},
					{"mimeType": "text/html", "body": {"data": html}},
				],
			}
		)

		self.assertEqual(body, "Visible text")
		self.assertNotIn("secret", body)

	def test_classroom_document_contains_coursework_and_resource_links(self):
		document = _classroom_text_document(
			"course-1",
			"Biology",
			"courseWorkMaterials",
			{
				"id": "material-1",
				"title": "Cell structure",
				"description": "Read before class",
				"alternateLink": "https://classroom.google.com/c/course-1",
				"materials": [
					{"link": {"title": "Reading list", "url": "https://example.com/read"}}
				],
			},
			"Cell structure",
		)

		self.assertEqual(
			document.source_item_id,
			"course-1:courseWorkMaterials:material-1",
		)
		self.assertIn("Read before class", document.content)
		self.assertIn("Reading list", document.content)
		self.assertEqual(document.location, "https://classroom.google.com/c/course-1")


if __name__ == "__main__":
	unittest.main()

"""Read-only ingestion adapters for Google Drive, Gmail, and Classroom."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import base64
import json
from pathlib import Path
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from typing import NoReturn

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.connectors.google import (
	decrypt_token,
	encrypt_token,
	expiry_from_response,
	refresh_google_token,
)
from app.models import Connector, ConnectorCredential
from app.ingestion.extraction import SUPPORTED_EXTENSIONS, extract_document_text
from app.ingestion.sources import SourceDocument

_GOOGLE_API_TIMEOUT_SECONDS = 30
_MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
_DRIVE_API = "https://www.googleapis.com/drive/v3"
_GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
_CLASSROOM_API = "https://classroom.googleapis.com/v1"
_DRIVE_EXPORTS = {
	"application/vnd.google-apps.document": ("text/plain", ".txt"),
	"application/vnd.google-apps.spreadsheet": ("text/csv", ".csv"),
	"application/vnd.google-apps.presentation": ("text/plain", ".txt"),
}
_DRIVE_EXTENSIONS = {
	"application/pdf": ".pdf",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
	"application/msword": ".doc",
	"application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
	"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
	"text/plain": ".txt",
	"text/markdown": ".md",
	"text/csv": ".csv",
	"application/json": ".json",
}


class GoogleSourceError(RuntimeError):
	def __init__(self, status_code: int, message: str):
		super().__init__(message)
		self.status_code = status_code


def get_connector_access_token(
	db: Session, credential: ConnectorCredential
) -> str:
	if not credential.encrypted_access_token:
		raise GoogleSourceError(401, "Reconnect this Google account to continue syncing.")

	expires_at = credential.token_expires_at
	if expires_at is not None:
		if expires_at.tzinfo is None:
			expires_at = expires_at.replace(tzinfo=timezone.utc)
		if expires_at.timestamp() <= datetime.now(timezone.utc).timestamp() + 60:
			if not credential.encrypted_refresh_token:
				raise GoogleSourceError(
					401, "Reconnect this Google account to renew its expired access."
				)
			try:
				tokens = refresh_google_token(
					decrypt_token(credential.encrypted_refresh_token)
				)
			except HTTPException as error:
				raise GoogleSourceError(
					error.status_code,
					"Google access expired. Reconnect this account and try again.",
				) from error
			except (HTTPError, URLError, TimeoutError, OSError) as error:
				raise GoogleSourceError(
					503, "Google token refresh failed; try syncing again."
				) from error
			access_token = tokens.get("access_token")
			if not access_token:
				raise GoogleSourceError(502, "Google returned no refreshed access token.")
			credential.encrypted_access_token = encrypt_token(access_token)
			credential.token_expires_at = expiry_from_response(tokens)
			db.commit()
			return access_token

	try:
		return decrypt_token(credential.encrypted_access_token)
	except Exception as error:
		raise GoogleSourceError(
			503, "Could not decrypt the saved Google credentials."
		) from error


class GoogleApi:
	def __init__(self, access_token: str):
		self._access_token = access_token

	def get_json(self, url: str, params: dict[str, str] | None = None) -> dict:
		if params:
			url = f"{url}?{urlencode(params)}"
		request = Request(
			url,
			headers={
				"Authorization": f"Bearer {self._access_token}",
				"Accept": "application/json",
			},
		)
		try:
			with urlopen(request, timeout=_GOOGLE_API_TIMEOUT_SECONDS) as response:
				return json.loads(response.read())
		except HTTPError as error:
			self._raise_api_error(error)
		except (URLError, TimeoutError, OSError) as error:
			raise GoogleSourceError(503, "Could not reach the Google API.") from error

	def get_bytes(self, url: str, params: dict[str, str] | None = None) -> bytes:
		if params:
			url = f"{url}?{urlencode(params)}"
		request = Request(
			url,
			headers={"Authorization": f"Bearer {self._access_token}"},
		)
		try:
			with urlopen(request, timeout=_GOOGLE_API_TIMEOUT_SECONDS) as response:
				data = response.read(_MAX_DOWNLOAD_BYTES + 1)
		except HTTPError as error:
			self._raise_api_error(error)
		except (URLError, TimeoutError, OSError) as error:
			raise GoogleSourceError(503, "Could not reach the Google API.") from error
		if len(data) > _MAX_DOWNLOAD_BYTES:
			raise GoogleSourceError(413, "A Google file exceeds the 25 MB sync limit.")
		return data

	@staticmethod
	def _raise_api_error(error: HTTPError) -> NoReturn:
		try:
			payload = json.loads(error.read())
			message = payload.get("error", {}).get("message", "")
		except (json.JSONDecodeError, OSError, AttributeError):
			message = ""
		if error.code == 401:
			detail = "Google authorization expired. Reconnect this account."
		elif error.code == 403:
			detail = (
				"Google denied access. Check that the required API is enabled and "
				"reauthorize the connector with its requested read-only permissions."
			)
		elif error.code == 404:
			detail = "A Google source item no longer exists."
		elif error.code == 429 or error.code >= 500:
			detail = "Google is temporarily unavailable or rate-limiting sync."
		else:
			detail = "Google rejected the source request."
		if message:
			detail = f"{detail} ({message[:300]})"
		raise GoogleSourceError(error.code, detail) from error


def fetch_google_documents(
	connector: Connector, access_token: str
) -> list[SourceDocument]:
	api = GoogleApi(access_token)
	if connector.connector_type == "GOOGLE_DRIVE":
		return _fetch_drive_documents(api)
	if connector.connector_type == "GMAIL":
		return _fetch_gmail_documents(api)
	if connector.connector_type == "GOOGLE_CLASSROOM":
		return _fetch_classroom_documents(api)
	raise GoogleSourceError(422, "This Google connector type is not supported.")


def _fetch_drive_documents(api: GoogleApi) -> list[SourceDocument]:
	documents: list[SourceDocument] = []
	page_token: str | None = None
	while True:
		params = {
			"pageSize": "1000",
			"q": "trashed = false and mimeType != 'application/vnd.google-apps.folder'",
			"orderBy": "modifiedTime desc",
			"fields": (
				"nextPageToken,files(id,name,mimeType,modifiedTime,createdTime,"
				"webViewLink,size,parents)"
			),
		}
		if page_token:
			params["pageToken"] = page_token
		payload = api.get_json(f"{_DRIVE_API}/files", params)
		for file_record in payload.get("files", []):
			try:
				document = _drive_document(api, file_record)
			except GoogleSourceError as error:
				if error.status_code == 404:
					continue
				document = _failed_drive_document(file_record, str(error))
			except Exception as error:
				document = _failed_drive_document(
					file_record, f"{type(error).__name__}: {error}"
				)
			if document is not None:
				documents.append(document)
		page_token = payload.get("nextPageToken")
		if not page_token:
			return documents


def _drive_document(api: GoogleApi, record: dict) -> SourceDocument | None:
	file_id = record.get("id")
	title = record.get("name")
	mime_type = record.get("mimeType")
	if not isinstance(file_id, str) or not isinstance(title, str) or not isinstance(mime_type, str):
		return None

	export = _DRIVE_EXPORTS.get(mime_type)
	extension = export[1] if export else _DRIVE_EXTENSIONS.get(mime_type)
	if extension not in SUPPORTED_EXTENSIONS:
		return None

	encoded_id = quote(file_id, safe="")
	if export:
		content_bytes = api.get_bytes(
			f"{_DRIVE_API}/files/{encoded_id}/export",
			{"mimeType": export[0]},
		)
	else:
		content_bytes = api.get_bytes(f"{_DRIVE_API}/files/{encoded_id}")
	created_at = _parse_google_time(record.get("createdTime"))
	modified_at = _parse_google_time(record.get("modifiedTime"))
	file_size = record.get("size")
	try:
		content = _extract_google_file_content(content_bytes, extension)
	except Exception as error:
		return _failed_drive_document(
			record, f"{type(error).__name__}: file extraction failed"
		)
	if content is None:
		return None
	parent_ids = record.get("parents", [])
	return SourceDocument(
		source_item_id=file_id,
		title=title,
		content=content,
		source="google_drive",
		item_type="file",
		mime_type=mime_type,
		file_extension=extension,
		file_size_bytes=int(file_size) if str(file_size or "").isdigit() else len(content_bytes),
		file_created_at=created_at,
		modified_at=modified_at,
		location=record.get("webViewLink"),
		parent_location=(
			" / ".join(parent_ids)
			if isinstance(parent_ids, list)
			and all(isinstance(parent_id, str) for parent_id in parent_ids)
			else None
		),
		web_url=record.get("webViewLink"),
		source_metadata={
			"drive_file_id": file_id,
			"parent_ids": parent_ids,
		},
	)


def _failed_drive_document(record: dict, error: str) -> SourceDocument:
	file_id = record.get("id")
	mime_type = record.get("mimeType")
	title = record.get("name")
	if not isinstance(file_id, str) or not isinstance(title, str):
		raise GoogleSourceError(502, "Google returned a file without a valid id or name.")
	parent_ids = record.get("parents", [])
	return SourceDocument(
		source_item_id=file_id,
		title=title,
		content="",
		source="google_drive",
		item_type="file",
		mime_type=mime_type if isinstance(mime_type, str) else None,
		file_size_bytes=(
			int(record["size"])
			if str(record.get("size", "")).isdigit()
			else None
		),
		modified_at=_parse_google_time(record.get("modifiedTime")),
		location=record.get("webViewLink"),
		parent_location=(
			" / ".join(parent_ids)
			if isinstance(parent_ids, list)
			and all(isinstance(parent_id, str) for parent_id in parent_ids)
			else None
		),
		web_url=record.get("webViewLink"),
		source_metadata={
			"drive_file_id": file_id,
			"parent_ids": parent_ids,
		},
		processing_error=error,
	)


def _extract_google_file_content(content: bytes, extension: str) -> str | None:
	if extension in {".txt", ".md", ".csv", ".json"}:
		return content.decode("utf-8-sig")
	file_path: str | None = None
	try:
		with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temporary:
			file_path = temporary.name
			temporary.write(content)
		return extract_document_text(file_path)
	finally:
		if file_path is not None:
			Path(file_path).unlink(missing_ok=True)


def _fetch_gmail_documents(api: GoogleApi) -> list[SourceDocument]:
	documents: list[SourceDocument] = []
	page_token: str | None = None
	while True:
		params = {"maxResults": "100"}
		if page_token:
			params["pageToken"] = page_token
		payload = api.get_json(f"{_GMAIL_API}/messages", params)
		for message in payload.get("messages", []):
			message_id = message.get("id")
			if not isinstance(message_id, str):
				continue
			try:
				full_message = api.get_json(
					f"{_GMAIL_API}/messages/{message_id}", {"format": "full"}
				)
			except GoogleSourceError as error:
				if error.status_code == 404:
					continue
				documents.append(
					SourceDocument(
						source_item_id=message_id,
						title="Google message",
						content="",
						source="gmail",
						item_type="email",
						processing_error=str(error),
					)
				)
				continue
			try:
				document = _gmail_message_document(message_id, full_message)
			except Exception as error:
				document = SourceDocument(
					source_item_id=message_id,
					title="Google message",
					content="",
					source="gmail",
					item_type="email",
					processing_error=f"{type(error).__name__}: message extraction failed",
				)
			if document is not None:
				documents.append(document)
		page_token = payload.get("nextPageToken")
		if not page_token:
			return documents


class _TextExtractor(HTMLParser):
	def __init__(self) -> None:
		super().__init__()
		self._hidden_depth = 0
		self.parts: list[str] = []

	def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
		if tag in {"script", "style"}:
			self._hidden_depth += 1
		elif tag in {"br", "p", "div", "li"} and self._hidden_depth == 0:
			self.parts.append("\n")

	def handle_endtag(self, tag: str) -> None:
		if tag in {"script", "style"} and self._hidden_depth:
			self._hidden_depth -= 1
		elif tag in {"p", "div", "li"} and self._hidden_depth == 0:
			self.parts.append("\n")

	def handle_data(self, data: str) -> None:
		if self._hidden_depth == 0:
			self.parts.append(data)


def _gmail_message_document(message_id: str, message: dict) -> SourceDocument | None:
	payload = message.get("payload", {})
	headers = {
		header.get("name", "").lower(): header.get("value", "")
		for header in payload.get("headers", [])
	}
	body = _gmail_body(payload)
	subject = headers.get("subject", "(no subject)")
	sender = headers.get("from", "")
	date = headers.get("date", "")
	content = "\n".join(
		value for value in (f"Subject: {subject}", f"From: {sender}", f"Date: {date}", body)
		if value
	)
	thread_id = message.get("threadId")
	web_url = (
		f"https://mail.google.com/mail/u/0/#all/{thread_id}"
		if isinstance(thread_id, str) and thread_id
		else None
	)
	return SourceDocument(
		source_item_id=message_id,
		title=subject[:500],
		content=content,
		source="gmail",
		item_type="email",
		mime_type="message/rfc822",
		file_size_bytes=message.get("sizeEstimate"),
		modified_at=_parse_email_date(date),
		location=web_url,
		web_url=web_url,
		source_metadata={
			"sender": sender or None,
			"subject": subject,
			"message_id": message_id,
			"thread_id": thread_id,
			"date_header": date or None,
		},
	)


def _gmail_body(part: dict) -> str:
	plain_text: list[str] = []
	html_text: list[str] = []

	def collect(current: dict) -> None:
		mime_type = current.get("mimeType", "")
		data = current.get("body", {}).get("data")
		if data and mime_type in {"text/plain", "text/html"}:
			decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode(
				"utf-8", errors="replace"
			)
			(plain_text if mime_type == "text/plain" else html_text).append(decoded)
		for child in current.get("parts", []):
			collect(child)

	collect(part)
	if plain_text:
		return "\n".join(plain_text)
	if html_text:
		parser = _TextExtractor()
		parser.feed("\n".join(html_text))
		return "".join(parser.parts)
	return ""


def _fetch_classroom_documents(api: GoogleApi) -> list[SourceDocument]:
	documents: list[SourceDocument] = []
	courses = _list_google_pages(api, f"{_CLASSROOM_API}/courses", "courses")
	for course in courses:
		course_id = course.get("id")
		if not isinstance(course_id, str):
			continue
		course_name = course.get("name", "Classroom course")
		coursework = _list_google_pages(
			api,
			f"{_CLASSROOM_API}/courses/{course_id}/courseWork",
			"courseWork",
		)
		materials = _list_google_pages(
			api,
			f"{_CLASSROOM_API}/courses/{course_id}/courseWorkMaterials",
			"courseWorkMaterial",
		)
		announcements = _list_google_pages(
			api,
			f"{_CLASSROOM_API}/courses/{course_id}/announcements",
			"announcements",
		)
		for assignment in coursework:
			documents.append(
				_classroom_text_document(
					course_id,
					course_name,
					"courseWork",
					assignment,
					assignment.get("title", "Class assignment"),
				)
			)
		for material in materials:
			documents.append(
				_classroom_text_document(
					course_id,
					course_name,
					"courseWorkMaterials",
					material,
					material.get("title", "Course material"),
				)
			)
		for announcement in announcements:
			documents.append(
				_classroom_text_document(
					course_id,
					course_name,
					"announcements",
					announcement,
					announcement.get("text", "Class announcement")[:120],
				)
			)
	return documents


def _list_google_pages(api: GoogleApi, url: str, collection: str) -> list[dict]:
	items: list[dict] = []
	page_token: str | None = None
	while True:
		params = {"pageSize": "100"}
		if page_token:
			params["pageToken"] = page_token
		payload = api.get_json(url, params)
		items.extend(payload.get(collection, []))
		page_token = payload.get("nextPageToken")
		if not page_token:
			return items


def _classroom_text_document(
	course_id: str,
	course_name: str,
	collection: str,
	record: dict,
	title: str,
) -> SourceDocument:
	resource_id = record.get("id")
	content_parts = [f"Course: {course_name}", f"Title: {title}"]
	attachments = []
	for field in ("description", "text", "state", "alternateLink"):
		value = record.get(field)
		if isinstance(value, str) and value:
			content_parts.append(f"{field.title()}: {value}")
	for material in record.get("materials", []):
		for key in ("driveFile", "link", "youtubeVideo", "form"):
			resource = material.get(key)
			if isinstance(resource, dict):
				resource = resource.get(key, resource)
				resource_title = resource.get("title") or resource.get("url") or resource.get("formUrl")
				if resource_title:
					content_parts.append(f"Resource: {resource_title}")
					attachments.append(
						{
							"type": key,
							"title": resource.get("title"),
							"id": resource.get("id"),
							"url": resource.get("url")
							or resource.get("alternateLink")
							or resource.get("formUrl"),
						}
					)
	return SourceDocument(
		source_item_id=f"{course_id}:{collection}:{resource_id or title}",
		title=f"{course_name}: {title}"[:500],
		content="\n".join(content_parts),
		source="google_classroom",
		item_type=collection,
		mime_type="text/plain",
		modified_at=_parse_google_time(record.get("updateTime")),
		location=record.get("alternateLink"),
		parent_location=f"Google Classroom course: {course_name}",
		web_url=record.get("alternateLink"),
		source_metadata={
			"course_id": course_id,
			"course_name": course_name,
			"resource_id": resource_id,
			"resource_type": collection,
			"attachments": attachments,
		},
	)


def _parse_google_time(value: object) -> datetime | None:
	if not isinstance(value, str):
		return None
	try:
		parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
	except ValueError:
		return None
	if parsed.tzinfo is None:
		return parsed.replace(tzinfo=timezone.utc)
	return parsed


def _parse_email_date(value: str) -> datetime | None:
	if not value:
		return None
	try:
		parsed = parsedate_to_datetime(value)
	except (TypeError, ValueError, OverflowError):
		return None
	if parsed.tzinfo is None:
		return parsed.replace(tzinfo=timezone.utc)
	return parsed

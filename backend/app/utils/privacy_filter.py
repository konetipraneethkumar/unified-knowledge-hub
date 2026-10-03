import re
from collections.abc import Mapping
from typing import Any


ALLOWED_FILE_METADATA_FIELDS = frozenset(
	{
		"path",
		"filename",
		"extension",
		"size",
		"created_time",
		"modified_time",
		"mime_type",
		"content_hash",
	}
)

_CREDENTIAL_PATTERNS = (
	re.compile(
		r"(?i)(?<![A-Za-z0-9])(?:password|passwd|passphrase|secret|credential|token|"
		r"api[_-]?key|access[_-]?token|refresh[_-]?token|auth(?:entication)?[_-]?token)"
		r"[\"']?\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"
	),
	re.compile(r"(?i)\bauthorization\s*[:=]\s*(?:bearer|basic)\s+[^\s,;]+"),
	re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*"),
	re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
_PRIVATE_KEY_BLOCK = re.compile(
	r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?"
	r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
	re.DOTALL,
)


def filter_file_metadata(
	metadata: Mapping[str, Any],
) -> dict[str, Any] | None:
	"""Allow only retrieval metadata and reject credential-bearing values."""
	filtered_metadata = {}
	for field, value in metadata.items():
		if field not in ALLOWED_FILE_METADATA_FIELDS:
			continue
		if isinstance(value, str) and any(
			pattern.search(value) for pattern in _CREDENTIAL_PATTERNS
		):
			return None
		filtered_metadata[field] = value

	return filtered_metadata


def filter_file_content(content: str) -> str:
	"""Redact credential-like values before document text is indexed."""
	filtered_content = _PRIVATE_KEY_BLOCK.sub("[REDACTED]", content)
	for pattern in _CREDENTIAL_PATTERNS:
		filtered_content = pattern.sub("[REDACTED]", filtered_content)
	return filtered_content
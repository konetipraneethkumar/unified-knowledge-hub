import mimetypes
from pathlib import Path
from typing import Any

from app.connectors.local_filesystem import FileRecord


def normalize_file_metadata(
	record: FileRecord, location: str
) -> dict[str, Any]:
	return {
		"path": location,
		"filename": record.filename,
		"extension": record.extension,
		"size": record.size,
		"created_time": record.created_time,
		"modified_time": record.modified_time,
		"mime_type": mimetypes.guess_type(Path(record.filename).name)[0],
	}

import hashlib
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(
	path: str | os.PathLike[str], chunk_size: int = 1024 * 1024
) -> str:
	"""Return a file's SHA-256 digest while reading it in bounded chunks."""
	if chunk_size <= 0:
		raise ValueError("chunk_size must be positive")

	digest = hashlib.sha256()
	with open(path, "rb") as file:
		while chunk := file.read(chunk_size):
			digest.update(chunk)
	return digest.hexdigest()


@dataclass(frozen=True)
class FileRecord:
	path: str
	filename: str
	extension: str
	size: int
	created_time: datetime
	modified_time: datetime


def scan_directory(directory: str | os.PathLike[str]) -> list[FileRecord]:
	"""Return metadata for regular files below a directory, without reading contents."""
	root = os.fspath(directory)
	records = []

	for current_directory, subdirectories, filenames in os.walk(
		root, onerror=lambda error: None, followlinks=False
	):
		subdirectories.sort()
		for filename in sorted(filenames):
			file_path = Path(current_directory, filename)
			try:
				file_stat = os.stat(file_path, follow_symlinks=False)
			except OSError:
				continue

			if not stat.S_ISREG(file_stat.st_mode):
				continue

			created_timestamp = getattr(
				file_stat, "st_birthtime", file_stat.st_ctime
			)
			records.append(
				FileRecord(
					path=str(file_path),
					filename=file_path.name,
					extension=file_path.suffix,
					size=file_stat.st_size,
					created_time=datetime.fromtimestamp(
						created_timestamp, tz=timezone.utc
					),
					modified_time=datetime.fromtimestamp(
						file_stat.st_mtime, tz=timezone.utc
					),
				)
			)

	return sorted(records, key=lambda record: record.path)
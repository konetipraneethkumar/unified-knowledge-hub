import hashlib
import builtins
import io
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app.connectors.local_filesystem import FileRecord, scan_directory, sha256_file


class LocalFilesystemScannerTests(unittest.TestCase):
	def test_sha256_file_reads_in_bounded_chunks(self):
		content = b"content streamed in small chunks"

		class ChunkTrackingFile(io.BytesIO):
			def __init__(self, data):
				super().__init__(data)
				self.read_sizes = []

			def read(self, size=-1):
				self.read_sizes.append(size)
				return super().read(size)

		stream = ChunkTrackingFile(content)
		with patch("builtins.open", return_value=stream):
			digest = sha256_file("unused-path", chunk_size=5)

		self.assertEqual(digest, hashlib.sha256(content).hexdigest())
		self.assertTrue(stream.read_sizes)
		self.assertTrue(all(size == 5 for size in stream.read_sizes))

	def test_recursively_returns_file_metadata_without_reading_contents(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			root = Path(temporary_directory)
			nested_directory = root / "nested"
			nested_directory.mkdir()
			file_path = nested_directory / "notes.txt"
			file_path.write_bytes(b"metadata only")
			file_stat = file_path.stat()

			with patch.object(
				builtins, "open", side_effect=AssertionError("contents read")
			):
				records = scan_directory(root)

		self.assertEqual(len(records), 1)
		self.assertEqual(
			records[0],
			FileRecord(
				path=str(file_path),
				filename="notes.txt",
				extension=".txt",
				size=len(b"metadata only"),
				created_time=datetime.fromtimestamp(
					getattr(file_stat, "st_birthtime", file_stat.st_ctime),
					tz=timezone.utc,
				),
				modified_time=datetime.fromtimestamp(
					file_stat.st_mtime, tz=timezone.utc
				),
			),
		)

	def test_ignores_directories_and_skips_files_with_inaccessible_metadata(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			root = Path(temporary_directory)
			(root / "folder").mkdir()
			accessible_file = root / "accessible.txt"
			inaccessible_file = root / "inaccessible.txt"
			accessible_file.write_text("ok", encoding="utf-8")
			inaccessible_file.write_text("skip", encoding="utf-8")
			real_stat = os.stat

			def stat_with_inaccessible_file(path, *args, **kwargs):
				if Path(path) == inaccessible_file:
					raise PermissionError("access denied")
				return real_stat(path, *args, **kwargs)

			with patch(
				"app.connectors.local_filesystem.os.stat",
				side_effect=stat_with_inaccessible_file,
			):
				records = scan_directory(root)

		self.assertEqual([record.filename for record in records], ["accessible.txt"])


if __name__ == "__main__":
	unittest.main()
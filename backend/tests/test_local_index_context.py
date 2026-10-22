import unittest
from pathlib import Path

from app.ingestion.local_context import (
	LocalIndexContext,
	LocalIndexContextError,
	require_authorized_path,
)


class LocalIndexContextTests(unittest.TestCase):
	def test_accepts_authorized_root_and_descendants(self):
		root = Path.cwd().resolve()
		context = LocalIndexContext(1, "connector", "device", root)
		self.assertEqual(require_authorized_path(root / "notes.txt", context), root / "notes.txt")

	def test_rejects_paths_outside_authorized_root(self):
		root = Path.cwd().resolve()
		context = LocalIndexContext(1, "connector", "device", root)
		with self.assertRaises(LocalIndexContextError):
			require_authorized_path(root.parent, context)


if __name__ == "__main__":
	unittest.main()

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.main import app
from app.schemas.connectors import ConnectorSyncResult


class ConnectorSyncApiTests(unittest.TestCase):
	def setUp(self):
		self.connector = SimpleNamespace(id="connector-1", owner_id=7)
		self.db = Mock()
		self.db.scalar.return_value = self.connector

		def override_get_db():
			yield self.db

		app.dependency_overrides[get_db] = override_get_db
		app.dependency_overrides[get_current_active_user] = lambda: SimpleNamespace(id=7)
		self.client = TestClient(app)

	def tearDown(self):
		self.client.close()
		app.dependency_overrides.pop(get_db, None)
		app.dependency_overrides.pop(get_current_active_user, None)

	def test_sync_endpoint_requires_connector_owner_and_returns_pipeline_counts(self):
		result = ConnectorSyncResult(
			connector_id="connector-1",
			status="completed",
			processed=3,
			skipped=2,
			failed=0,
			deleted=1,
		)
		with patch(
			"app.api.connector_sync.run_connector_sync", return_value=result
		) as sync:
			response = self.client.post(
				"/api/v1/connectors/connector-1/sync",
				headers={"Authorization": "Bearer test"},
			)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["processed"], 3)
		self.assertEqual(response.json()["skipped"], 2)
		self.assertEqual(response.json()["deleted"], 1)
		self.assertEqual(self.db.scalar.call_count, 1)
		sync.assert_called_once_with(self.db, self.connector)

	def test_sync_endpoint_does_not_run_for_another_users_connector(self):
		self.db.scalar.return_value = None
		with patch("app.api.connector_sync.run_connector_sync") as sync:
			response = self.client.post(
				"/api/v1/connectors/connector-1/sync",
				headers={"Authorization": "Bearer test"},
			)

		self.assertEqual(response.status_code, 404)
		sync.assert_not_called()


if __name__ == "__main__":
	unittest.main()

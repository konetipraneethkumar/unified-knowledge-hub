from types import SimpleNamespace
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.security import get_current_user
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

	def test_connector_list_includes_owner_scoped_index_count(self):
		now = datetime.now(timezone.utc)
		connector = SimpleNamespace(
			id="connector-1",
			owner_id=7,
			connector_type="GOOGLE_DRIVE",
			provider="google",
			name="Google Drive",
			device_id=None,
			status="active",
			authentication_status="authorized",
			authorized_root=None,
			external_account_id=None,
			created_at=now,
			last_sync_at=now,
			revoked_at=None,
		)
		self.db.scalars.return_value.all.return_value = [connector]
		self.db.execute.return_value.all.return_value = [("connector-1", 4)]
		app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=7)
		try:
			response = self.client.get("/connectors")
		finally:
			app.dependency_overrides.pop(get_current_user, None)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()[0]["indexed_item_count"], 4)

	def test_google_connect_url_returns_authenticated_oauth_url(self):
		with (
			patch(
				"app.api.google_connectors.create_oauth_state",
				return_value="state-value",
			) as create_state,
			patch(
				"app.api.google_connectors.authorization_url",
				return_value="https://accounts.google.com/authorize",
			),
		):
			response = self.client.get("/api/v1/connectors/gmail/connect-url")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			response.json(), {"url": "https://accounts.google.com/authorize"}
		)
		self.assertEqual(
			create_state.call_args.kwargs["purpose"], "connector:gmail"
		)
		self.assertEqual(create_state.call_args.kwargs["user_id"], 7)


if __name__ == "__main__":
	unittest.main()

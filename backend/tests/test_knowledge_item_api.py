import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


class KnowledgeItemApiTests(unittest.TestCase):
	def setUp(self):
		self.engine = create_engine(
			"sqlite://",
			connect_args={"check_same_thread": False},
			poolclass=StaticPool,
		)
		Base.metadata.create_all(self.engine)
		self.session_factory = sessionmaker(bind=self.engine)

		def override_get_db():
			db = self.session_factory()
			try:
				yield db
			finally:
				db.close()

		app.dependency_overrides[get_db] = override_get_db
		self.client = TestClient(app)

		# These endpoints are user-scoped. Authenticate the test client rather
		# than bypassing the application's production authentication dependency.
		auth_response = self.client.post(
			"/auth/register",
			json={
				"email": "knowledge-items-test@example.com",
				"password": "test-password-for-api",
			},
		)
		self.assertEqual(auth_response.status_code, 201, auth_response.text)
		self.client.headers.update(
			{"Authorization": f"Bearer {auth_response.json()['access_token']}"}
		)

	def tearDown(self):
		self.client.close()
		app.dependency_overrides.pop(get_db, None)
		Base.metadata.drop_all(self.engine)
		self.engine.dispose()

	def create_item(self, source_item_id: str):
		return self.client.post(
			"/knowledge-items",
			json={
				"source": "local",
				"source_item_id": source_item_id,
				"title": f"Notes {source_item_id}",
			},
		)

	def test_knowledge_items_require_authentication(self):
		unauthenticated_client = TestClient(app)
		try:
			response = unauthenticated_client.get("/knowledge-items")
		finally:
			unauthenticated_client.close()

		self.assertEqual(response.status_code, 401)

	def test_post_creates_and_persists_knowledge_item_across_requests(self):
		response = self.create_item("item-1")

		self.assertEqual(response.status_code, 201)
		payload = response.json()
		self.assertGreater(payload["id"], 0)
		self.assertEqual(payload["source_item_id"], "item-1")
		self.assertEqual(payload["title"], "Notes item-1")
		self.assertIn("created_at", payload)
		self.assertNotIn("content_hash", payload)

		list_response = self.client.get("/knowledge-items")
		item_response = self.client.get(f"/knowledge-items/{payload['id']}")

		self.assertEqual(list_response.status_code, 200)
		self.assertEqual(list_response.json()[0]["id"], payload["id"])
		self.assertEqual(item_response.status_code, 200)
		self.assertEqual(item_response.json()["source_item_id"], "item-1")

	def test_post_rejects_missing_or_empty_required_fields(self):
		invalid_payloads = [
			{"source_item_id": "item-1"},
			{"source": "local"},
			{"source": "", "source_item_id": "item-1"},
			{"source": "local", "source_item_id": ""},
		]

		for payload in invalid_payloads:
			with self.subTest(payload=payload):
				response = self.client.post("/knowledge-items", json=payload)
				self.assertEqual(response.status_code, 422)

		self.assertEqual(self.client.get("/knowledge-items").json(), [])

	def test_get_knowledge_items_returns_list(self):
		self.create_item("item-1")
		self.create_item("item-2")

		response = self.client.get("/knowledge-items")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(
			[item["source_item_id"] for item in response.json()],
			["item-1", "item-2"],
		)

	def test_get_knowledge_item_returns_item_and_404_for_missing_id(self):
		created_response = self.create_item("item-1")
		self.assertEqual(created_response.status_code, 201, created_response.text)
		created = created_response.json()

		response = self.client.get(f"/knowledge-items/{created['id']}")
		missing_response = self.client.get(
			f"/knowledge-items/{created['id'] + 100}"
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["source_item_id"], "item-1")
		self.assertEqual(missing_response.status_code, 404)
		self.assertEqual(
			missing_response.json()["detail"], "Knowledge item not found"
		)


if __name__ == "__main__":
	unittest.main()

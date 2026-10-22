from uuid import uuid4
from collections.abc import Callable

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.database import Base
from app import models as _models


def create_postgres_test_engine() -> tuple[Engine, Callable[[], None]]:
	admin_engine = create_engine(settings.DATABASE_URL)
	schema = f"test_{uuid4().hex}"
	with admin_engine.begin() as connection:
		connection.execute(text(f'CREATE SCHEMA "{schema}"'))

	engine = create_engine(
		settings.DATABASE_URL,
		connect_args={"options": f"-csearch_path={schema},public"},
	)
	metadata = MetaData()
	for table in Base.metadata.sorted_tables:
		table.to_metadata(metadata, schema=schema)
	try:
		metadata.create_all(engine)
	except Exception:
		engine.dispose()
		with admin_engine.begin() as connection:
			connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
		admin_engine.dispose()
		raise

	def cleanup() -> None:
		engine.dispose()
		with admin_engine.begin() as connection:
			connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
		admin_engine.dispose()

	return engine, cleanup

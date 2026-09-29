from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KnowledgeItem(Base):
	__tablename__ = "knowledge_items"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	source: Mapped[str] = mapped_column(String, index=True, nullable=False)
	source_item_id: Mapped[str] = mapped_column(String, nullable=False)
	title: Mapped[str | None] = mapped_column(String, index=True)
	item_type: Mapped[str | None] = mapped_column(String)
	mime_type: Mapped[str | None] = mapped_column(String)
	location: Mapped[str | None] = mapped_column(Text)
	summary: Mapped[str | None] = mapped_column(Text)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	indexed_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	content_hash: Mapped[str | None] = mapped_column(String, index=True)

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuthToken(Base):
    __tablename__ = "auth_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    credential_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Pairing(Base):
    __tablename__ = "pairings"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Connector(Base):
    __tablename__ = "connectors"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[str | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"), index=True)
    connector_type: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)
    authentication_status: Mapped[str] = mapped_column(String, default="not_required", nullable=False)
    authorized_root: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class KnowledgeItem(Base):
	__tablename__ = "knowledge_items"
	__table_args__ = (
		UniqueConstraint("connector_id", "source_item_id", name="uq_knowledge_items_connector_item"),
	)

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
	connector_id: Mapped[str | None] = mapped_column(ForeignKey("connectors.id", ondelete="CASCADE"), index=True)
	device_id: Mapped[str | None] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"), index=True)
	source: Mapped[str] = mapped_column(String, index=True, nullable=False)
	source_item_id: Mapped[str] = mapped_column(String, nullable=False)
	title: Mapped[str | None] = mapped_column(String, index=True)
	item_type: Mapped[str | None] = mapped_column(String)
	mime_type: Mapped[str | None] = mapped_column(String)
	file_extension: Mapped[str | None] = mapped_column(String)
	file_size_bytes: Mapped[int | None]
	file_created_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True)
	)
	location: Mapped[str | None] = mapped_column(Text)
	summary: Mapped[str | None] = mapped_column(Text)
	content: Mapped[str | None] = mapped_column(Text)
	processing_status: Mapped[str] = mapped_column(
		String, default="pending", server_default="pending", nullable=False
	)
	processing_error: Mapped[str | None] = mapped_column(Text)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	indexed_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now(), nullable=False
	)
	content_hash: Mapped[str | None] = mapped_column(String, index=True)
	embedding_model: Mapped[str | None] = mapped_column(String)


class KnowledgeItemEmbedding(Base):
	__tablename__ = "knowledge_item_embeddings"

	item_id: Mapped[int] = mapped_column(
		ForeignKey("knowledge_items.id", ondelete="CASCADE"), primary_key=True
	)
	embedding: Mapped[list[float]] = mapped_column(Vector(), nullable=False)

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column
)

from pgvector.sqlalchemy import Vector

# --------------------------------------------------
# Base
# --------------------------------------------------

class Base(DeclarativeBase):
    pass


# --------------------------------------------------
# User
# --------------------------------------------------
# Added for authentication / per-user data ownership.
# Every other table now scopes its rows to a user via
# a user_id foreign key so one user can never read,
# modify, or delete another user's data.

class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )


# --------------------------------------------------
# Research Query
# --------------------------------------------------

class ResearchQuery(Base):

    __tablename__ = "research_queries"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    # Nullable so rows created before this migration
    # (user_id did not exist yet) do not break. Every
    # new row written by the API always sets this.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Which LangGraph route answered this question
    # (direct / document / web / both / image / ...).
    route: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    key_points: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )


# --------------------------------------------------
# Document
# --------------------------------------------------
# One row per uploaded file. Added so the Document
# Library / Knowledge Base pages have something to
# list, show status/chunk counts on, and delete —
# separate from the individual chunk rows.

class Document(Base):

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    filename: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # "processing" | "ready" | "failed"
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="processing"
    )

    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    upload_date: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )


# --------------------------------------------------
# Document Chunk
# --------------------------------------------------

class DocumentChunk(Base):

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    # Nullable for the same backward-compatibility reason
    # as ResearchQuery.user_id above.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    filename: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    chunk_index: Mapped[int] = mapped_column(
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

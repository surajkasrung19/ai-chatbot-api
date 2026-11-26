
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class ConversationORM(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    messages: Mapped[list["MessageORM"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by=lambda: MessageORM.sequence,
        lazy="selectin"
    )


class MessageORM(Base):
    __tablename__ = "messages"

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name="ck_message_role"
        ),
        UniqueConstraint(
            "conversation_id",
            "sequence",
            name="uq_conversation_message_sequence"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(
            "conversations.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    role: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    conversation: Mapped["ConversationORM"] = relationship(
        back_populates="messages"
    )

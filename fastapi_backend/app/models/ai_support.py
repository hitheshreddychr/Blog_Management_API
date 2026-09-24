from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AISupportChat(Base):
    __tablename__ = "ai_support_chats"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    question = Column(
        Text,
        nullable=False,
    )

    ai_response = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="ai_support_chats",
    )
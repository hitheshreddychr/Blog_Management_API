from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    subscription_plan_id = Column(
        Integer,
        ForeignKey("subscription_plans.id"),
        nullable=True,
    )

    posts = relationship(
        "Post",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    comments = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    likes = relationship(
        "Like",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    subscription_plan = relationship(
        "SubscriptionPlan",
        back_populates="users",
    )

    billing_history = relationship(
        "BillingHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    post_activities = relationship(
        "PostActivity",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    ai_support_chats = relationship(
        "AISupportChat",
        back_populates="user",
        cascade="all, delete-orphan",
    )
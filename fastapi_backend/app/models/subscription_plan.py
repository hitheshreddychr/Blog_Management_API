from sqlalchemy import Column, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    max_posts = Column(Integer, nullable=True)
    max_images_per_post = Column(Integer, nullable=True)
    max_likes = Column(Integer, nullable=True)
    max_comments = Column(Integer, nullable=True)

    users = relationship(
        "User",
        back_populates="subscription_plan",
    )

    billing_history = relationship(
        "BillingHistory",
        back_populates="plan",
    )

    def is_within_limit(
        self,
        limit_name: str,
        current_count: int,
    ) -> bool:
        limit = getattr(self, limit_name)

        if limit is None:
            return True

        return current_count < limit

    def can_create_post(
        self,
        current_count: int,
    ) -> bool:
        return self.is_within_limit(
            "max_posts",
            current_count,
        )

    def can_upload_image(
        self,
        current_count: int,
    ) -> bool:
        limit = self.max_images_per_post

        if limit is None:
            return True

        return current_count < limit

    def can_like(
        self,
        current_count: int,
    ) -> bool:
        return self.is_within_limit(
            "max_likes",
            current_count,
        )

    def can_comment(
        self,
        current_count: int,
    ) -> bool:
        return self.is_within_limit(
            "max_comments",
            current_count,
        )
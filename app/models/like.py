from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "post_id",
            "user_id",
            name="unique_user_post_like",
        ),
    )

    post = relationship(
        "Post",
        back_populates="likes",
    )

    user = relationship(
        "User",
        back_populates="likes",
    )
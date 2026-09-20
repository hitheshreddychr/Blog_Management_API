from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post


PLAN_LIMIT_MESSAGE = "You've reached your plan limit. Kindly upgrade your plan to continue."


def require_active_subscription(current_user):
    if current_user.subscription_plan is None:
        raise HTTPException(
            status_code=403,
            detail="Please subscribe to a plan to continue.",
        )

    return current_user.subscription_plan


def check_plan_limit(
    current_user,
    limit_name: str,
    current_count: int,
):
    plan = require_active_subscription(current_user)

    if not plan.is_within_limit(
        limit_name,
        current_count,
    ):
        raise HTTPException(
            status_code=403,
            detail=PLAN_LIMIT_MESSAGE,
        )

    return plan


def check_post_limit(
    current_user,
    current_count: int,
):
    plan = require_active_subscription(current_user)

    if not plan.can_create_post(current_count):
        raise HTTPException(
            status_code=403,
            detail=PLAN_LIMIT_MESSAGE,
        )

    return plan


def check_image_limit(
    current_user,
    current_count: int,
):
    plan = require_active_subscription(current_user)

    if not plan.can_upload_image(current_count):
        raise HTTPException(
            status_code=403,
            detail=PLAN_LIMIT_MESSAGE,
        )

    return plan


def check_like_limit(
    current_user,
    current_count: int,
):
    plan = require_active_subscription(current_user)

    if not plan.can_like(current_count):
        raise HTTPException(
            status_code=403,
            detail=PLAN_LIMIT_MESSAGE,
        )

    return plan


def check_comment_limit(
    current_user,
    current_count: int,
):
    plan = require_active_subscription(current_user)

    if not plan.can_comment(current_count):
        raise HTTPException(
            status_code=403,
            detail=PLAN_LIMIT_MESSAGE,
        )

    return plan


def count_user_posts(
    db: Session,
    user_id: int,
):
    return (
        db.query(Post)
        .filter(Post.author_id == user_id)
        .count()
    )


def count_user_likes(
    db: Session,
    user_id: int,
):
    return (
        db.query(Like)
        .filter(Like.user_id == user_id)
        .count()
    )


def count_user_comments(
    db: Session,
    user_id: int,
):
    return (
        db.query(Comment)
        .filter(Comment.user_id == user_id)
        .count()
    )
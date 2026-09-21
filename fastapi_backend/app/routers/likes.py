from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.schemas.like import LikeResponse
from app.services.notification_service import (
    send_post_activity_notification,
)
from app.services.subscription import (
    check_plan_limit,
    count_user_likes,
)


router = APIRouter(
    prefix="/posts/{post_id}/likes",
    tags=["Likes"],
)


@router.post(
    "/",
    response_model=LikeResponse,
    status_code=status.HTTP_201_CREATED,
)
def like_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = (
        db.query(Post)
        .filter(Post.id == post_id)
        .first()
    )

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    existing_like = (
        db.query(Like)
        .filter(
            Like.post_id == post_id,
            Like.user_id == current_user.id,
        )
        .first()
    )

    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already liked this post",
        )

    current_like_count = count_user_likes(
        db,
        current_user.id,
    )

    check_plan_limit(
        current_user,
        "max_likes",
        current_like_count,
    )

    like = Like(
        post_id=post_id,
        user_id=current_user.id,
    )

    db.add(like)

    try:
        db.commit()
        db.refresh(like)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already liked this post",
        )

    background_tasks.add_task(
        send_post_activity_notification,
        to_email=post.author.email,
        post_owner_name=post.author.username,
        post_title=post.title,
        activity_user_name=current_user.username,
        activity_type="Like",
        activity_time=datetime.now(timezone.utc),
    )

    return {
        "message": "Post liked successfully",
        "post_id": post_id,
    }


@router.delete(
    "/",
    response_model=LikeResponse,
)
def unlike_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    like = (
        db.query(Like)
        .filter(
            Like.post_id == post_id,
            Like.user_id == current_user.id,
        )
        .first()
    )

    if like is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not liked this post",
        )

    db.delete(like)
    db.commit()

    return {
        "message": "Post unliked successfully",
        "post_id": post_id,
    }
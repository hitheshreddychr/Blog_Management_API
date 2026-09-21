from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse
from app.services.notification_service import (
    send_post_activity_notification,
)
from app.services.subscription import (
    check_plan_limit,
    count_user_comments,
)


router = APIRouter(
    prefix="/posts/{post_id}/comments",
    tags=["Comments"],
)


@router.post(
    "/",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
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

    current_comment_count = count_user_comments(
        db,
        current_user.id,
    )

    check_plan_limit(
        current_user,
        "max_comments",
        current_comment_count,
    )

    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        text=comment_data.text,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    background_tasks.add_task(
        send_post_activity_notification,
        to_email=post.author.email,
        post_owner_name=post.author.username,
        post_title=post.title,
        activity_user_name=current_user.username,
        activity_type="Comment",
        activity_time=comment.created_at,
    )

    return comment


@router.get(
    "/",
    response_model=list[CommentResponse],
)
def get_comments(
    post_id: int,
    db: Session = Depends(get_db),
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

    return (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
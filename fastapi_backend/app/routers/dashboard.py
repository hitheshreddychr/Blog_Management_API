from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.models.post_activity import PostActivity
from app.models.user import User
from app.schemas.dashboard import (
    ActivityData,
    DashboardResponse,
    PostAnalytics,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/",
    response_model=DashboardResponse,
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id

    posts = (
        db.query(Post)
        .filter(Post.author_id == user_id)
        .order_by(Post.created_at.asc())
        .all()
    )

    post_ids = [post.id for post in posts]

    total_posts = len(posts)

    total_comments_given = (
        db.query(Comment)
        .filter(Comment.user_id == user_id)
        .count()
    )

    total_comments_received = (
        db.query(Comment)
        .join(
            Post,
            Comment.post_id == Post.id,
        )
        .filter(
            Post.author_id == user_id
        )
        .count()
    )

    total_likes_received = (
        db.query(Like)
        .join(
            Post,
            Like.post_id == Post.id,
        )
        .filter(
            Post.author_id == user_id
        )
        .count()
    )

    total_likes_given = (
        db.query(Like)
        .filter(
            Like.user_id == user_id
        )
        .count()
    )

    total_unlikes_received = (
        db.query(PostActivity)
        .join(
            Post,
            PostActivity.post_id == Post.id,
        )
        .filter(
            Post.author_id == user_id,
            PostActivity.activity_type == "unlike",
        )
        .count()
    )

    total_unlikes_given = (
        db.query(PostActivity)
        .filter(
            PostActivity.user_id == user_id,
            PostActivity.activity_type == "unlike",
        )
        .count()
    )

    post_analytics = []

    for post in posts:
        like_count = (
            db.query(Like)
            .filter(
                Like.post_id == post.id
            )
            .count()
        )

        comment_count = (
            db.query(Comment)
            .filter(
                Comment.post_id == post.id
            )
            .count()
        )

        unlike_count = (
            db.query(PostActivity)
            .filter(
                PostActivity.post_id == post.id,
                PostActivity.activity_type == "unlike",
            )
            .count()
        )

        post_analytics.append(
            PostAnalytics(
                post_id=post.id,
                title=post.title,
                likes=like_count,
                comments=comment_count,
                unlikes=unlike_count,
            )
        )

    activity_data = defaultdict(
        lambda: {
            "posts": 0,
            "comments_given": 0,
            "comments_received": 0,
            "likes_given": 0,
            "likes_received": 0,
            "unlikes_given": 0,
            "unlikes_received": 0,
        }
    )

    for post in posts:
        activity_date = post.created_at.date().isoformat()

        activity_data[activity_date]["posts"] += 1

    user_comments = (
        db.query(Comment)
        .filter(
            Comment.user_id == user_id
        )
        .all()
    )

    for comment in user_comments:
        activity_date = comment.created_at.date().isoformat()

        activity_data[activity_date]["comments_given"] += 1

    received_comments = (
        db.query(Comment)
        .join(
            Post,
            Comment.post_id == Post.id,
        )
        .filter(
            Post.author_id == user_id
        )
        .all()
    )

    for comment in received_comments:
        activity_date = comment.created_at.date().isoformat()

        activity_data[activity_date]["comments_received"] += 1

    user_likes = (
        db.query(PostActivity)
        .filter(
            PostActivity.user_id == user_id,
            PostActivity.activity_type == "like",
        )
        .all()
    )

    for activity in user_likes:
        activity_date = activity.created_at.date().isoformat()

        activity_data[activity_date]["likes_given"] += 1

    received_like_activities = (
        db.query(PostActivity)
        .join(
            Post,
            PostActivity.post_id == Post.id,
        )
        .filter(
            Post.author_id == user_id,
            PostActivity.activity_type == "like",
        )
        .all()
    )

    for activity in received_like_activities:
        activity_date = activity.created_at.date().isoformat()

        activity_data[activity_date]["likes_received"] += 1

    user_unlikes = (
        db.query(PostActivity)
        .filter(
            PostActivity.user_id == user_id,
            PostActivity.activity_type == "unlike",
        )
        .all()
    )

    for activity in user_unlikes:
        activity_date = activity.created_at.date().isoformat()

        activity_data[activity_date]["unlikes_given"] += 1

    received_unlike_activities = (
        db.query(PostActivity)
        .join(
            Post,
            PostActivity.post_id == Post.id,
        )
        .filter(
            Post.author_id == user_id,
            PostActivity.activity_type == "unlike",
        )
        .all()
    )

    for activity in received_unlike_activities:
        activity_date = activity.created_at.date().isoformat()

        activity_data[activity_date]["unlikes_received"] += 1

    activity = [
        ActivityData(
            date=date,
            posts=data["posts"],
            comments_given=data["comments_given"],
            comments_received=data["comments_received"],
            likes_given=data["likes_given"],
            likes_received=data["likes_received"],
            unlikes_given=data["unlikes_given"],
            unlikes_received=data["unlikes_received"],
        )
        for date, data in sorted(
            activity_data.items()
        )
    ]

    return DashboardResponse(
        user_id=user_id,
        username=current_user.username,
        total_posts=total_posts,
        total_comments=total_comments_given,
        total_comments_received=total_comments_received,
        total_likes_received=total_likes_received,
        total_likes_given=total_likes_given,
        total_unlikes_received=total_unlikes_received,
        total_unlikes_given=total_unlikes_given,
        post_analytics=post_analytics,
        activity=activity,
    )
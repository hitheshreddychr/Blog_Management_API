import os
import shutil
import uuid
from math import ceil

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.post import Post
from app.models.user import User
from app.schemas.post import (
    PaginatedPostResponse,
    PostCreate,
    PostResponse,
    PostUpdate,
)


router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
)


MEDIA_DIR = "media/posts"

os.makedirs(MEDIA_DIR, exist_ok=True)


@router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(
    title: str = Form(...),
    content: str = Form(...),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    image_url = None

    if image is not None:
        file_extension = os.path.splitext(image.filename or "")[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        image_path = os.path.join(
            MEDIA_DIR,
            unique_filename,
        )

        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        image_url = f"/media/posts/{unique_filename}"

    post = Post(
        title=title,
        content=content,
        image=image_url,
        author_id=current_user.id,
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return post


@router.get(
    "/",
    response_model=PaginatedPostResponse,
)
def get_posts(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of posts per page",
    ),
    search: str | None = Query(
        default=None,
        description="Search posts by title or content",
    ),
    db: Session = Depends(get_db),
):
    query = db.query(Post)

    if search:
        search_term = f"%{search}%"

        query = query.filter(
            or_(
                Post.title.ilike(search_term),
                Post.content.ilike(search_term),
            )
        )

    total_count = query.count()

    total_pages = (
        ceil(total_count / limit)
        if total_count > 0
        else 0
    )

    posts = (
        query
        .order_by(Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "posts": posts,
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "limit": limit,
    }


@router.get(
    "/mine",
    response_model=list[PostResponse],
)
def get_my_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Post)
        .filter(Post.author_id == current_user.id)
        .order_by(Post.created_at.desc())
        .all()
    )


@router.get(
    "/{post_id}",
    response_model=PostResponse,
)
def get_post(
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

    return post


@router.put(
    "/{post_id}",
    response_model=PostResponse,
)
def update_post(
    post_id: int,
    title: str | None = Form(default=None),
    content: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
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

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own posts",
        )

    if title is not None:
        post.title = title

    if content is not None:
        post.content = content

    if image is not None:
        if post.image:
            old_image_path = post.image.lstrip("/").replace("/", os.sep)

            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        file_extension = os.path.splitext(image.filename or "")[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        image_path = os.path.join(
            MEDIA_DIR,
            unique_filename,
        )

        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        post.image = f"/media/posts/{unique_filename}"

    db.commit()
    db.refresh(post)

    return post


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_post(
    post_id: int,
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

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts",
        )

    if post.image:
        image_path = post.image.lstrip("/").replace("/", os.sep)

        if os.path.exists(image_path):
            os.remove(image_path)

    db.delete(post)
    db.commit()

    return None
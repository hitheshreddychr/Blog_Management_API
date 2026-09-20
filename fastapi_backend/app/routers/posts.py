import os
import shutil
import uuid
from math import ceil

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.post import Post
from app.models.post_image import PostImage
from app.models.user import User
from app.schemas.post import PaginatedPostResponse, PostResponse
from app.services.subscription import (
    check_image_limit,
    check_plan_limit,
    count_user_posts,
)

router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
)

MEDIA_DIR = "media/posts"

os.makedirs(
    MEDIA_DIR,
    exist_ok=True,
)


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
    current_post_count = count_user_posts(
        db,
        current_user.id,
    )

    check_plan_limit(
        current_user,
        "max_posts",
        current_post_count,
    )

    if image:
        check_image_limit(
            current_user,
            0,
        )

    post = Post(
        title=title,
        content=content,
        image=None,
        author_id=current_user.id,
    )

    db.add(post)
    db.flush()

    if image:
        file_extension = os.path.splitext(
            image.filename or ""
        )[1]

        unique_filename = (
            f"{uuid.uuid4()}{file_extension}"
        )

        image_path = os.path.join(
            MEDIA_DIR,
            unique_filename,
        )

        with open(
            image_path,
            "wb",
        ) as buffer:
            shutil.copyfileobj(
                image.file,
                buffer,
            )

        image_url = (
            f"/media/posts/{unique_filename}"
        )

        post.image = image_url

        db.add(
            PostImage(
                post_id=post.id,
                image_path=image_url,
            )
        )

    db.commit()
    db.refresh(post)

    return post


@router.post(
    "/{post_id}/images",
    response_model=PostResponse,
)
def add_post_image(
    post_id: int,
    image: UploadFile = File(...),
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
            status_code=404,
            detail="Post not found",
        )

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only add images to your own posts",
        )

    current_image_count = (
        db.query(PostImage)
        .filter(
            PostImage.post_id == post.id
        )
        .count()
    )

    check_image_limit(
        current_user,
        current_image_count,
    )

    file_extension = os.path.splitext(
        image.filename or ""
    )[1]

    unique_filename = (
        f"{uuid.uuid4()}{file_extension}"
    )

    image_path = os.path.join(
        MEDIA_DIR,
        unique_filename,
    )

    with open(
        image_path,
        "wb",
    ) as buffer:
        shutil.copyfileobj(
            image.file,
            buffer,
        )

    image_url = (
        f"/media/posts/{unique_filename}"
    )

    db.add(
        PostImage(
            post_id=post.id,
            image_path=image_url,
        )
    )

    db.commit()
    db.refresh(post)

    return post


@router.get(
    "/",
    response_model=PaginatedPostResponse,
)
def get_posts(
    page: int = Query(
        1,
        ge=1,
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
    ),
    search: str | None = Query(None),
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

    total = query.count()

    total_pages = (
        ceil(total / limit)
        if total > 0
        else 0
    )

    posts = (
        query
        .order_by(
            Post.created_at.desc()
        )
        .offset(
            (page - 1) * limit
        )
        .limit(limit)
        .all()
    )

    return {
        "items": posts,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
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
        .filter(
            Post.author_id == current_user.id
        )
        .order_by(
            Post.created_at.desc()
        )
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
            status_code=404,
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
            status_code=404,
            detail="Post not found",
        )

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own posts",
        )

    if title is not None:
        post.title = title

    if content is not None:
        post.content = content

    if image:
        file_extension = os.path.splitext(
            image.filename or ""
        )[1]

        unique_filename = (
            f"{uuid.uuid4()}{file_extension}"
        )

        image_path = os.path.join(
            MEDIA_DIR,
            unique_filename,
        )

        with open(
            image_path,
            "wb",
        ) as buffer:
            shutil.copyfileobj(
                image.file,
                buffer,
            )

        image_url = (
            f"/media/posts/{unique_filename}"
        )

        first_post_image = (
            db.query(PostImage)
            .filter(
                PostImage.post_id == post.id
            )
            .order_by(
                PostImage.id.asc()
            )
            .first()
        )

        if first_post_image:
            old_image_name = (
                first_post_image.image_path.replace(
                    "/media/posts/",
                    "",
                )
            )

            old_image_file = os.path.join(
                MEDIA_DIR,
                old_image_name,
            )

            if os.path.exists(old_image_file):
                os.remove(old_image_file)

            first_post_image.image_path = image_url

        else:
            check_image_limit(
                current_user,
                0,
            )

            db.add(
                PostImage(
                    post_id=post.id,
                    image_path=image_url,
                )
            )

        post.image = image_url

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
            status_code=404,
            detail="Post not found",
        )

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own posts",
        )

    post_images = (
        db.query(PostImage)
        .filter(
            PostImage.post_id == post.id
        )
        .all()
    )

    deleted_files = set()

    if post.image:
        image_name = post.image.replace(
            "/media/posts/",
            "",
        )

        image_file = os.path.join(
            MEDIA_DIR,
            image_name,
        )

        if os.path.exists(image_file):
            os.remove(image_file)

        deleted_files.add(image_name)

    for post_image in post_images:
        image_name = post_image.image_path.replace(
            "/media/posts/",
            "",
        )

        image_file = os.path.join(
            MEDIA_DIR,
            image_name,
        )

        if (
            image_name not in deleted_files
            and os.path.exists(image_file)
        ):
            os.remove(image_file)

        deleted_files.add(image_name)

    db.delete(post)
    db.commit()

    return None
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

os.makedirs(MEDIA_DIR, exist_ok=True)


def get_uploaded_images(
    image: UploadFile | None,
    images: list[UploadFile] | None,
):
    uploaded_images = []

    if image is not None:
        uploaded_images.append(image)

    if images:
        uploaded_images.extend(images)

    return uploaded_images


def validate_image_count(
    current_user: User,
    image_count: int,
):
    for index in range(image_count):
        check_image_limit(current_user, index)


def save_uploaded_image(image: UploadFile):
    file_extension = os.path.splitext(image.filename or "")[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    image_path = os.path.join(
        MEDIA_DIR,
        unique_filename,
    )

    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    return f"/media/posts/{unique_filename}"


def delete_image_file(image_path: str):
    image_name = image_path.replace(
        "/media/posts/",
        "",
    )

    image_file = os.path.join(
        MEDIA_DIR,
        image_name,
    )

    if os.path.exists(image_file):
        os.remove(image_file)


@router.get(
    "/limits",
)
def get_upload_limits(
    current_user: User = Depends(get_current_user),
):
    plan = current_user.subscription_plan

    if plan is None:
        raise HTTPException(
            status_code=400,
            detail="No active subscription plan found",
        )

    return {
        "plan_name": plan.name,
        "max_images_per_post": plan.max_images_per_post,
    }


@router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(
    title: str = Form(...),
    content: str = Form(...),
    image: UploadFile | None = File(default=None),
    images: list[UploadFile] | None = File(default=None),
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

    uploaded_images = get_uploaded_images(
        image,
        images,
    )

    validate_image_count(
        current_user,
        len(uploaded_images),
    )

    post = Post(
        title=title,
        content=content,
        image=None,
        author_id=current_user.id,
    )

    db.add(post)
    db.flush()

    saved_paths = []

    try:
        for uploaded_image in uploaded_images:
            image_url = save_uploaded_image(
                uploaded_image
            )

            saved_paths.append(image_url)

            db.add(
                PostImage(
                    post_id=post.id,
                    image_path=image_url,
                )
            )

        if saved_paths:
            post.image = saved_paths[0]

        db.commit()
        db.refresh(post)

    except Exception:
        db.rollback()

        for image_path in saved_paths:
            delete_image_file(image_path)

        raise

    return post


@router.post(
    "/{post_id}/images",
    response_model=PostResponse,
)
def add_post_images(
    post_id: int,
    image: UploadFile | None = File(default=None),
    images: list[UploadFile] | None = File(default=None),
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

    uploaded_images = get_uploaded_images(
        image,
        images,
    )

    if not uploaded_images:
        raise HTTPException(
            status_code=400,
            detail="At least one image is required",
        )

    current_image_count = (
        db.query(PostImage)
        .filter(PostImage.post_id == post.id)
        .count()
    )

    legacy_image = None

    if post.image:
        legacy_image = (
            db.query(PostImage)
            .filter(
                PostImage.post_id == post.id,
                PostImage.image_path == post.image,
            )
            .first()
        )

        if legacy_image is None:
            current_image_count += 1

    for index in range(len(uploaded_images)):
        check_image_limit(
            current_user,
            current_image_count + index,
        )

    saved_paths = []

    try:
        for uploaded_image in uploaded_images:
            image_url = save_uploaded_image(
                uploaded_image
            )

            saved_paths.append(image_url)

            db.add(
                PostImage(
                    post_id=post.id,
                    image_path=image_url,
                )
            )

        if not post.image and saved_paths:
            post.image = saved_paths[0]

        db.commit()
        db.refresh(post)

    except Exception:
        db.rollback()

        for image_path in saved_paths:
            delete_image_file(image_path)

        raise

    return post


@router.delete(
    "/{post_id}/images/{image_id}",
    response_model=PostResponse,
)
def delete_post_image(
    post_id: int,
    image_id: int,
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
            detail="You can only delete images from your own posts",
        )

    if image_id == 0:
        legacy_image = None

        if post.image:
            legacy_image = (
                db.query(PostImage)
                .filter(
                    PostImage.post_id == post_id,
                    PostImage.image_path == post.image,
                )
                .first()
            )

        if legacy_image is not None:
            image_id = legacy_image.id
        else:
            if not post.image:
                raise HTTPException(
                    status_code=404,
                    detail="Post image not found",
                )

            image_path = post.image
            post.image = None
            delete_image_file(image_path)

            db.commit()
            db.refresh(post)

            return post

    post_image = (
        db.query(PostImage)
        .filter(
            PostImage.id == image_id,
            PostImage.post_id == post_id,
        )
        .first()
    )

    if post_image is None:
        raise HTTPException(
            status_code=404,
            detail="Post image not found",
        )

    image_path = post_image.image_path

    db.delete(post_image)

    remaining_images = (
        db.query(PostImage)
        .filter(
            PostImage.post_id == post_id,
            PostImage.id != image_id,
        )
        .order_by(PostImage.id.asc())
        .all()
    )

    if remaining_images:
        post.image = remaining_images[0].image_path
    else:
        post.image = None

    delete_image_file(image_path)

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
        .order_by(Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "posts": posts,
        "total_count": total,
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
        .filter(PostImage.post_id == post.id)
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

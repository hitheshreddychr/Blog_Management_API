from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )
    content: str = Field(
        ...,
        min_length=1,
    )


class PostUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    content: str | None = Field(
        default=None,
        min_length=1,
    )


class PostImageResponse(BaseModel):
    id: int
    image_path: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    image: str | None = None
    images: list[PostImageResponse] = []
    author_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class PaginatedPostResponse(BaseModel):
    posts: list[PostResponse]
    total_count: int
    total_pages: int
    page: int
    limit: int
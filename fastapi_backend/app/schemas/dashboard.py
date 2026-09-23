from pydantic import BaseModel


class PostAnalytics(BaseModel):
    post_id: int
    title: str
    likes: int
    comments: int
    unlikes: int


class ActivityData(BaseModel):
    date: str
    posts: int
    comments_given: int
    comments_received: int
    likes_given: int
    likes_received: int
    unlikes_given: int
    unlikes_received: int


class DashboardResponse(BaseModel):
    user_id: int
    username: str

    total_posts: int

    total_comments: int
    total_comments_received: int

    total_likes_received: int
    total_likes_given: int

    total_unlikes_received: int
    total_unlikes_given: int

    post_analytics: list[PostAnalytics]
    activity: list[ActivityData]
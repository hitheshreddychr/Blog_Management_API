from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    max_posts: int | None
    max_images_per_post: int | None
    max_likes: int | None
    max_comments: int | None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionResponse(BaseModel):
    message: str
    plan: SubscriptionPlanResponse
    start_date: datetime
    end_date: datetime


class BillingHistoryResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    price: Decimal
    start_date: datetime
    end_date: datetime
    transaction_id: str
    invoice_path: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
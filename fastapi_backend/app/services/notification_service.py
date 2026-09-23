from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.email_service import send_email


INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")


def send_post_activity_notification(
    to_email: str,
    post_owner_name: str,
    post_title: str,
    activity_user_name: str,
    activity_type: str,
    activity_time: datetime,
) -> None:
    if activity_time.tzinfo is None:
        activity_time = activity_time.replace(
            tzinfo=timezone.utc
        )

    local_activity_time = activity_time.astimezone(
        INDIA_TIMEZONE
    )

    formatted_time = local_activity_time.strftime(
        "%Y-%m-%d %I:%M %p"
    )

    if activity_type == "Comment":
        activity_message = "commented on your post"
        subject = "New Comment on Your Blog Post"
    else:
        activity_message = "liked your post"
        subject = "New Like on Your Blog Post"

    body = (
        f"Hello {post_owner_name},\n\n"
        f"Post: {post_title}\n"
        f"User: {activity_user_name}\n"
        f"Activity: {activity_message}\n"
        f"Time: {formatted_time}\n\n"
        "Blog Management API"
    )

    try:
        send_email(
            to_email=to_email,
            subject=subject,
            body=body,
        )
    except Exception as exc:
        print(
            f"Notification service failed: {exc}"
        )


def create_in_app_notification(
    db: Session,
    user_id: int,
    message: str,
    notification_type: str,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        message=message,
        notification_type=notification_type,
        is_read=False,
    )

    db.add(notification)

    return notification
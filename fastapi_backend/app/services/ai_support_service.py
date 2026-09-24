def generate_ai_response(message: str) -> str:
    message_lower = message.lower().strip()

    if any(
        keyword in message_lower
        for keyword in [
            "create post",
            "create a post",
            "new post",
            "add post",
            "write post",
        ]
    ):
        return (
            "To create a post, log in to your account and use the Create Post "
            "option. Enter the required post details and submit the form."
        )

    if any(
        keyword in message_lower
        for keyword in [
            "update post",
            "edit post",
            "modify post",
        ]
    ):
        return (
            "To update a post, open one of your posts, select the Edit option, "
            "modify the required details, and save the changes."
        )

    if any(
        keyword in message_lower
        for keyword in [
            "delete post",
            "remove post",
        ]
    ):
        return (
            "To delete a post, open the post you own and use the Delete option. "
            "The post will be removed after the deletion request is processed."
        )

    if any(
        keyword in message_lower
        for keyword in [
            "subscription",
            "plan",
            "premium",
            "basic",
            "pro",
        ]
    ):
        return (
            "The blog application supports Basic, Premium, and Pro subscription "
            "plans. Each plan provides different limits and features."
        )

    if any(
        keyword in message_lower
        for keyword in [
            "billing",
            "invoice",
            "payment",
        ]
    ):
        return (
            "Billing information and invoice records are maintained for "
            "subscription transactions. You can view your billing details "
            "through the available subscription and billing features."
        )

    if any(
        keyword in message_lower
        for keyword in [
            "profile",
            "account",
            "password",
        ]
    ):
        return (
            "You can manage your account information and password through the "
            "profile and authentication features of the application."
        )

    if any(
        keyword in message_lower
        for keyword in [
            "dashboard",
            "analytics",
            "statistics",
            "stats",
        ]
    ):
        return (
            "The dashboard provides information about your blog activity, "
            "including relevant statistics and activity data."
        )

    if any(
        keyword in message_lower
        for keyword in [
            "like",
            "likes",
        ]
    ):
        return (
            "You can like blog posts using the Like feature. The application "
            "prevents duplicate likes from the same user on the same post."
        )

    if any(
        keyword in message_lower
        for keyword in [
            "comment",
            "comments",
        ]
    ):
        return (
            "You can add comments to blog posts using the Comments feature. "
            "Comments are associated with the corresponding post and user."
        )

    if any(
        keyword in message_lower
        for keyword in [
            "notification",
            "notifications",
        ]
    ):
        return (
            "Notifications keep you informed about activities such as likes "
            "and comments on your posts."
        )

    return (
        "I'm here to help with the Blog Management application. "
        "You can ask me about posts, subscriptions, billing, profiles, "
        "dashboard features, comments, likes, or notifications."
    )
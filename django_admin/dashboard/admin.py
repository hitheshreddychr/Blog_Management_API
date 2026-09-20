from django.contrib import admin

from .models import BillingHistory, BlogUser, SubscriptionPlan


@admin.register(BlogUser)
class BlogUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "subscription_plan_id",
    )

    search_fields = (
        "username",
        "email",
    )

    list_filter = (
        "subscription_plan_id",
    )

    ordering = (
        "id",
    )

    readonly_fields = (
        "id",
        "username",
        "email",
        "hashed_password",
        "subscription_plan_id",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "max_posts",
        "max_images_per_post",
        "max_likes",
        "max_comments",
    )

    search_fields = (
        "name",
    )

    list_filter = (
        "name",
    )

    ordering = (
        "id",
    )


@admin.register(BillingHistory)
class BillingHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_id",
        "plan_id",
        "price",
        "start_date",
        "end_date",
        "transaction_id",
        "invoice_path",
        "created_at",
    )

    search_fields = (
        "transaction_id",
        "invoice_path",
    )

    list_filter = (
        "plan_id",
        "start_date",
        "end_date",
        "created_at",
    )

    ordering = (
        "-id",
    )

    readonly_fields = (
        "id",
        "created_at",
    )
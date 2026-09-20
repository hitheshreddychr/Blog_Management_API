from django.db import models


class BlogUser(models.Model):
    id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=100)
    email = models.EmailField(max_length=255)
    hashed_password = models.CharField(max_length=255)
    subscription_plan_id = models.IntegerField(
        null=True,
        blank=True,
    )

    class Meta:
        managed = False
        db_table = "users"
        verbose_name = "Blog User"
        verbose_name_plural = "Blog Users"

    def __str__(self):
        return self.username


class SubscriptionPlan(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    max_posts = models.IntegerField(
        null=True,
        blank=True,
    )
    max_images_per_post = models.IntegerField(
        null=True,
        blank=True,
    )
    max_likes = models.IntegerField(
        null=True,
        blank=True,
    )
    max_comments = models.IntegerField(
        null=True,
        blank=True,
    )

    class Meta:
        managed = False
        db_table = "subscription_plans"
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return self.name


class BillingHistory(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    plan_id = models.IntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    transaction_id = models.CharField(
        max_length=100,
    )
    invoice_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "billing_history"
        verbose_name = "Billing History"
        verbose_name_plural = "Billing Histories"

    def __str__(self):
        return f"Billing #{self.id}"
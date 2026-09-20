from sqlalchemy import inspect, text

from app.database import Base, engine
from app.models import BillingHistory, SubscriptionPlan, User


def setup_database():
    print("Creating Assessment 14 tables...")

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    users_columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    if "subscription_plan_id" not in users_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN subscription_plan_id "
                    "INTEGER REFERENCES subscription_plans(id)"
                )
            )

        print("Added subscription_plan_id to users table.")
    else:
        print("subscription_plan_id already exists.")

    inspector = inspect(engine)

    existing_plans = inspector.get_table_names()

    if "subscription_plans" in existing_plans:
        print("subscription_plans table is ready.")

    if "billing_history" in existing_plans:
        print("billing_history table is ready.")

    from sqlalchemy.orm import Session

    with Session(engine) as db:
        plans = [
            {
                "name": "Basic",
                "price": 99.00,
                "max_posts": 1,
                "max_images_per_post": 1,
                "max_likes": 5,
                "max_comments": 5,
            },
            {
                "name": "Premium",
                "price": 299.00,
                "max_posts": 2,
                "max_images_per_post": 2,
                "max_likes": 20,
                "max_comments": 20,
            },
            {
                "name": "Pro",
                "price": 599.00,
                "max_posts": None,
                "max_images_per_post": None,
                "max_likes": None,
                "max_comments": None,
            },
        ]

        for plan_data in plans:
            existing_plan = (
                db.query(SubscriptionPlan)
                .filter(
                    SubscriptionPlan.name == plan_data["name"]
                )
                .first()
            )

            if existing_plan is None:
                plan = SubscriptionPlan(**plan_data)
                db.add(plan)
                print(
                    f"Created {plan_data['name']} subscription plan."
                )
            else:
                print(
                    f"{plan_data['name']} subscription plan already exists."
                )

        db.commit()

    print("Assessment 14 database setup completed successfully.")


if __name__ == "__main__":
    setup_database()
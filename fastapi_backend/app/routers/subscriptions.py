from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.billing_history import BillingHistory
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.schemas.subscription import (
    BillingHistoryResponse,
    SubscriptionPlanResponse,
    SubscriptionResponse,
)
from app.services.invoice import generate_invoice


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)


@router.get(
    "/plans",
    response_model=list[SubscriptionPlanResponse],
)
def get_subscription_plans(
    db: Session = Depends(get_db),
):
    return (
        db.query(SubscriptionPlan)
        .order_by(SubscriptionPlan.id.asc())
        .all()
    )


@router.post(
    "/{plan_id}",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def subscribe_to_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.id == plan_id)
        .first()
    )

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found",
        )

    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=30)

    transaction_id = f"TXN-{uuid4().hex[:12].upper()}"

    current_user.subscription_plan_id = plan.id

    billing_history = BillingHistory(
        user_id=current_user.id,
        plan_id=plan.id,
        price=plan.price,
        start_date=start_date,
        end_date=end_date,
        transaction_id=transaction_id,
    )

    db.add(billing_history)
    db.flush()

    invoice_path = generate_invoice(
        billing_id=billing_history.id,
        username=current_user.username,
        plan_name=plan.name,
        price=plan.price,
        start_date=start_date,
        end_date=end_date,
        transaction_id=transaction_id,
    )

    billing_history.invoice_path = invoice_path

    db.commit()

    db.refresh(current_user)
    db.refresh(billing_history)

    return {
        "message": "Subscription activated successfully",
        "plan": plan,
        "start_date": start_date,
        "end_date": end_date,
    }


@router.get(
    "/current",
    response_model=SubscriptionPlanResponse,
)
def get_current_subscription(
    current_user: User = Depends(get_current_user),
):
    if current_user.subscription_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You do not have an active subscription",
        )

    return current_user.subscription_plan


@router.get(
    "/billing",
    response_model=list[BillingHistoryResponse],
)
def get_billing_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(BillingHistory)
        .filter(
            BillingHistory.user_id == current_user.id
        )
        .order_by(
            BillingHistory.created_at.desc()
        )
        .all()
    )
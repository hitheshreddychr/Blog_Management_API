from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.ai_support import AISupportChat
from app.models.user import User
from app.schemas.ai_support import AISupportRequest, AISupportResponse, AISupportHistoryResponse
from app.services.ai_support_service import generate_ai_response


router = APIRouter(
    prefix="/api/ai-support",
    tags=["AI Support"],
)


@router.post(
    "/",
    response_model=AISupportResponse,
)
def ai_support(
    request: AISupportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    response = generate_ai_response(request.message)

    chat = AISupportChat(
        user_id=current_user.id,
        question=request.message,
        ai_response=response,
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return AISupportResponse(
        question=request.message,
        response=response,
    )

@router.get(
    "/history",
    response_model=list[AISupportHistoryResponse],
)
def get_ai_support_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chats = (
        db.query(AISupportChat)
        .filter(
            AISupportChat.user_id == current_user.id
        )
        .order_by(
            AISupportChat.created_at.desc()
        )
        .limit(50)
        .all()
    )

    return [
        AISupportHistoryResponse(
            id=chat.id,
            question=chat.question,
            response=chat.ai_response,
            created_at=chat.created_at,
        )
        for chat in chats
    ]
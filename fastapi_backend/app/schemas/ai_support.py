from datetime import datetime

from pydantic import BaseModel, Field


class AISupportRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )


class AISupportResponse(BaseModel):
    question: str
    response: str


class AISupportHistoryResponse(BaseModel):
    id: int
    question: str
    response: str
    created_at: datetime
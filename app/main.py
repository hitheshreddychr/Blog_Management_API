from fastapi import FastAPI

from app import models
from app.database import Base, engine
from app.routers import auth, comments, likes, posts


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Blog Management API",
    description="A Blog Management API built with FastAPI, SQLAlchemy, SQLite, and JWT authentication.",
    version="1.0.0",
)


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to the Blog Management API"
    }
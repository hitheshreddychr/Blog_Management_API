from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import models
from app.database import Base, engine
from app.routers import auth, comments, likes, posts


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Blog Management API",
    description="A Blog Management API built with FastAPI, SQLAlchemy, SQLite, and JWT authentication.",
    version="1.0.0",
)


# Allow the frontend to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve uploaded media files.
app.mount(
    "/media",
    StaticFiles(directory="media"),
    name="media",
)


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)


@app.get("/")
def root():
    return {"message": "Welcome to the Blog Management API"}
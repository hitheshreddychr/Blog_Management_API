from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from app import models
from app.database import Base, engine
from app.routers import (
    auth,
    comments,
    likes,
    posts,
    dashboard,
    subscriptions,
    notifications,
    ai_support,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Blog Management API",
    description="A Blog Management API built with FastAPI, SQLAlchemy, SQLite, and JWT authentication.",
    version="1.0.0",
)

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

app.mount(
    "/media",
    StaticFiles(directory="media"),
    name="media",
)

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)
app.include_router(subscriptions.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(ai_support.router)


@app.get("/")
def root():
    return {"message": "Welcome to the Blog Management API"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    schema["openapi"] = "3.0.3"

    components = schema.get("components", {})
    component_schemas = components.get("schemas", {})

    def resolve_schema(schema_object):
        if not isinstance(schema_object, dict):
            return schema_object

        reference = schema_object.get("$ref")

        if reference and reference.startswith("#/components/schemas/"):
            schema_name = reference.split("/")[-1]
            return component_schemas.get(schema_name, schema_object)

        return schema_object

    for path_data in schema.get("paths", {}).values():
        if not isinstance(path_data, dict):
            continue

        for operation in path_data.values():
            if not isinstance(operation, dict):
                continue

            request_body = operation.get("requestBody")

            if not isinstance(request_body, dict):
                continue

            content = request_body.get("content", {})

            multipart = content.get("multipart/form-data")

            if not isinstance(multipart, dict):
                continue

            body_schema = multipart.get("schema")

            if not isinstance(body_schema, dict):
                continue

            body_schema = resolve_schema(body_schema)

            properties = body_schema.get("properties", {})

            if not isinstance(properties, dict):
                continue

            if "image" in properties:
                properties["image"] = {
                    "type": "string",
                    "format": "binary",
                }

            if "images" in properties:
                images_schema = properties["images"]

                if isinstance(images_schema, dict):
                    if images_schema.get("type") == "array":
                        images_schema["items"] = {
                            "type": "string",
                            "format": "binary",
                        }
                    else:
                        properties["images"] = {
                            "type": "string",
                            "format": "binary",
                        }

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
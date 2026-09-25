import re
import secrets
from datetime import timedelta
from urllib.parse import quote

import httpx
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.auth0 import (
    AUTH0_CLIENT_ID,
    AUTH0_CLIENT_SECRET,
    AUTH0_CALLBACK_URL,
    AUTH0_TOKEN_URL,
    AUTH0_USERINFO_URL,
    FRONTEND_URL,
    build_authorization_url,
    create_state,
    verify_state,
)
from app.auth.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    Token,
    UserCreate,
    UserResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def generate_username(
    db: Session,
    name: str,
    email: str,
) -> str:
    base_name = name.strip() if name else ""

    if not base_name:
        base_name = email.split("@")[0]

    username = re.sub(
        r"[^a-zA-Z0-9_]+",
        "_",
        base_name,
    ).strip("_")

    if not username:
        username = "user"

    username = username[:50]

    original_username = username
    counter = 1

    while (
        db.query(User)
        .filter(User.username == username)
        .first()
        is not None
    ):
        counter += 1
        suffix = f"_{counter}"
        username = (
            original_username[: 50 - len(suffix)]
            + suffix
        )

    return username


def redirect_with_error(
    message: str,
) -> RedirectResponse:
    encoded_message = quote(
        message,
        safe="",
    )

    return RedirectResponse(
        url=(
            f"{FRONTEND_URL.rstrip('/')}"
            f"/#auth_error={encoded_message}"
        ),
        status_code=status.HTTP_302_FOUND,
    )


@router.post(
    "/signup/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    existing_username = (
        db.query(User)
        .filter(
            User.username == user_data.username
        )
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    existing_email = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(
            user_data.password
        ),
        auth_provider="local",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=Token,
)
def login(
    user_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if user is None or not verify_password(
        user_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
        },
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/google")
def google_login(
    response: Response,
):
    state = create_state("google")

    authorization_url = build_authorization_url(
        provider="google",
        state=state,
    )

    redirect_response = RedirectResponse(
        url=authorization_url,
        status_code=status.HTTP_302_FOUND,
    )

    redirect_response.set_cookie(
        key="auth0_state",
        value=state,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )

    return redirect_response


@router.get("/facebook")
def facebook_login(
    response: Response,
):
    state = create_state("facebook")

    authorization_url = build_authorization_url(
        provider="facebook",
        state=state,
    )

    redirect_response = RedirectResponse(
        url=authorization_url,
        status_code=status.HTTP_302_FOUND,
    )

    redirect_response.set_cookie(
        key="auth0_state",
        value=state,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )

    return redirect_response


@router.get("/callback/")
async def auth0_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        message = (
            error_description
            or "Auth0 authentication failed"
        )

        redirect_response = redirect_with_error(
            message
        )

        redirect_response.delete_cookie(
            key="auth0_state",
            path="/",
        )

        return redirect_response

    if not code:
        return redirect_with_error(
            "Missing Auth0 authorization code"
        )

    if not state:
        return redirect_with_error(
            "Missing Auth0 state parameter"
        )

    stored_state = request.cookies.get(
        "auth0_state"
    )

    if not stored_state:
        return redirect_with_error(
            "Auth0 session state is missing or expired"
        )

    if not secrets.compare_digest(
        state,
        stored_state,
    ):
        return redirect_with_error(
            "Invalid Auth0 authentication state"
        )

    state_data = verify_state(state)

    if state_data is None:
        return redirect_with_error(
            "Invalid or expired Auth0 state"
        )

    provider = state_data["provider"]

    token_payload = {
        "grant_type": "authorization_code",
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "code": code,
        "redirect_uri": AUTH0_CALLBACK_URL,
    }

    try:
        async with httpx.AsyncClient(
            timeout=15.0
        ) as client:
            token_response = await client.post(
                AUTH0_TOKEN_URL,
                data=token_payload,
            )

            if token_response.status_code != 200:
                redirect_response = redirect_with_error(
                    "Unable to complete Auth0 authentication"
                )

                redirect_response.delete_cookie(
                    key="auth0_state",
                    path="/",
                )

                return redirect_response

            token_data = token_response.json()

            access_token = token_data.get(
                "access_token"
            )

            if not access_token:
                redirect_response = redirect_with_error(
                    "Auth0 did not return an access token"
                )

                redirect_response.delete_cookie(
                    key="auth0_state",
                    path="/",
                )

                return redirect_response

            userinfo_response = await client.get(
                AUTH0_USERINFO_URL,
                headers={
                    "Authorization": (
                        f"Bearer {access_token}"
                    )
                },
            )

            if userinfo_response.status_code != 200:
                redirect_response = redirect_with_error(
                    "Unable to retrieve Auth0 user information"
                )

                redirect_response.delete_cookie(
                    key="auth0_state",
                    path="/",
                )

                return redirect_response

            userinfo = userinfo_response.json()

    except httpx.RequestError:
        redirect_response = redirect_with_error(
            "Unable to connect to Auth0"
        )

        redirect_response.delete_cookie(
            key="auth0_state",
            path="/",
        )

        return redirect_response

    auth0_user_id = userinfo.get("sub")
    email = userinfo.get("email")
    name = (
        userinfo.get("name")
        or userinfo.get("nickname")
        or ""
    )

    if not auth0_user_id:
        redirect_response = redirect_with_error(
            "Auth0 user identity is missing"
        )

        redirect_response.delete_cookie(
            key="auth0_state",
            path="/",
        )

        return redirect_response

    if not email:
        if provider == "facebook":
            facebook_user_id = (
                auth0_user_id
                .replace("|", "_")
                .replace(" ", "_")
            )
            email = (
                f"{facebook_user_id}"
                "@facebook.local"
            )
        else:
            redirect_response = redirect_with_error(
                "Email address was not provided by the social account"
            )

            redirect_response.delete_cookie(
                key="auth0_state",
                path="/",
            )

            return redirect_response

    expected_prefix = {
        "google": "google-oauth2|",
        "facebook": "facebook|",
    }[provider]

    if not auth0_user_id.startswith(
        expected_prefix
    ):
        redirect_response = redirect_with_error(
            "Auth0 provider verification failed"
        )

        redirect_response.delete_cookie(
            key="auth0_state",
            path="/",
        )

        return redirect_response

    user = (
        db.query(User)
        .filter(
            User.auth0_user_id
            == auth0_user_id
        )
        .first()
    )

    if user is None:
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if user is not None:
            email_verified = userinfo.get(
                "email_verified",
                False,
            )

            if (
                provider != "facebook"
                and email_verified is not True
            ):
                redirect_response = redirect_with_error(
                    "An account with this email already exists. Please use your existing login method."
                )

                redirect_response.delete_cookie(
                    key="auth0_state",
                    path="/",
                )

                return redirect_response

            user.auth_provider = provider
            user.auth0_user_id = auth0_user_id

        else:
            username = generate_username(
                db,
                name,
                email,
            )

            user = User(
                username=username,
                email=email,
                hashed_password=hash_password(
                    secrets.token_urlsafe(32)
                ),
                auth_provider=provider,
                auth0_user_id=auth0_user_id,
            )

            db.add(user)

    else:
        user.auth_provider = provider

        if user.email != email:
            email_owner = (
                db.query(User)
                .filter(
                    User.email == email,
                    User.id != user.id,
                )
                .first()
            )

            if email_owner is not None:
                redirect_response = redirect_with_error(
                    "This email address is already linked to another account."
                )

                redirect_response.delete_cookie(
                    key="auth0_state",
                    path="/",
                )

                return redirect_response

            user.email = email

    db.commit()
    db.refresh(user)

    application_token = create_access_token(
        data={
            "sub": str(user.id),
        },
        expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )

    redirect_response = RedirectResponse(
        url=(
            f"{FRONTEND_URL.rstrip('/')}"
            f"/#auth_token={quote(application_token, safe='')}"
        ),
        status_code=status.HTTP_302_FOUND,
    )

    redirect_response.delete_cookie(
        key="auth0_state",
        path="/",
    )

    return redirect_response
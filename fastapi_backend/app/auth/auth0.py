import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from urllib.parse import urlencode

from dotenv import load_dotenv


load_dotenv()


AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_CALLBACK_URL = os.getenv(
    "AUTH0_CALLBACK_URL",
    "http://127.0.0.1:8000/auth/callback/",
)

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://127.0.0.1:5500",
)

AUTH0_STATE_MAX_AGE = 600


if not AUTH0_DOMAIN:
    raise RuntimeError("AUTH0_DOMAIN is not configured")

if not AUTH0_CLIENT_ID:
    raise RuntimeError("AUTH0_CLIENT_ID is not configured")

if not AUTH0_CLIENT_SECRET:
    raise RuntimeError(
        "AUTH0_CLIENT_SECRET is not configured"
    )

if not os.getenv("SECRET_KEY"):
    raise RuntimeError("SECRET_KEY is not configured")


AUTH0_DOMAIN = AUTH0_DOMAIN.rstrip("/")

AUTH0_AUTHORIZE_URL = (
    f"https://{AUTH0_DOMAIN}/authorize"
)

AUTH0_TOKEN_URL = (
    f"https://{AUTH0_DOMAIN}/oauth/token"
)

AUTH0_USERINFO_URL = (
    f"https://{AUTH0_DOMAIN}/userinfo"
)


def create_state(provider: str) -> str:
    payload = {
        "provider": provider,
        "timestamp": int(time.time()),
        "nonce": secrets.token_urlsafe(32),
    }

    payload_json = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    payload_encoded = base64.urlsafe_b64encode(
        payload_json
    ).decode().rstrip("=")

    signature = hmac.new(
        os.environ["SECRET_KEY"].encode(),
        payload_encoded.encode(),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_encoded}.{signature}"


def verify_state(state: str) -> dict | None:
    try:
        payload_encoded, signature = state.split(
            ".",
            1,
        )

        expected_signature = hmac.new(
            os.environ["SECRET_KEY"].encode(),
            payload_encoded.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            signature,
            expected_signature,
        ):
            return None

        padding = "=" * (
            4 - len(payload_encoded) % 4
        )

        payload_json = base64.urlsafe_b64decode(
            payload_encoded + padding
        )

        payload = json.loads(
            payload_json.decode()
        )

        timestamp = int(
            payload.get("timestamp", 0)
        )

        if time.time() - timestamp > AUTH0_STATE_MAX_AGE:
            return None

        provider = payload.get("provider")

        if provider not in {
            "google",
            "facebook",
        }:
            return None

        return payload

    except (
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
    ):
        return None


def build_authorization_url(
    provider: str,
    state: str,
) -> str:
    connections = {
        "google": "google-oauth2",
        "facebook": "facebook",
    }

    connection = connections.get(provider)

    if connection is None:
        raise ValueError(
            "Unsupported Auth0 provider"
        )

    params = {
        "response_type": "code",
        "client_id": AUTH0_CLIENT_ID,
        "redirect_uri": AUTH0_CALLBACK_URL,
        "scope": "openid profile email",
        "connection": connection,
        "state": state,
        "prompt": "consent",
    }

    return (
        f"{AUTH0_AUTHORIZE_URL}?"
        f"{urlencode(params)}"
    )
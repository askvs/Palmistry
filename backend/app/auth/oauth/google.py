# Google OAuth2 adapter.
from authlib.integrations.starlette_client import OAuth
from fastapi import Request

from app.auth.errors import OAuthNotConfigured
from app.config import settings

PROVIDER = "google"

_oauth: OAuth | None = None


def _build_oauth() -> OAuth:
    global _oauth
    if _oauth is None:
        _oauth = OAuth()
        _oauth.register(
            name=PROVIDER,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    return _oauth


def is_configured() -> bool:
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def get_client():
    if not is_configured():
        raise OAuthNotConfigured("Google login is not configured on this server")
    return _build_oauth().create_client(PROVIDER)


async def authorize_redirect(request: Request, redirect_uri: str):
    client = get_client()
    return await client.authorize_redirect(request, redirect_uri)


async def authorize_access_token(request: Request):
    client = get_client()
    return await client.authorize_access_token(request)


def extract_profile(token: dict) -> dict:
    # Normalize provider userinfo into email, name, and google_id.
    userinfo = token.get("userinfo") or {}
    email = userinfo.get("email")
    if email is None:
        raise OAuthNotConfigured("Google did not return an email address for this account")
    return {
        "email": email,
        "full_name": userinfo.get("name") or userinfo.get("email", "").split("@")[0],
        "google_id": userinfo.get("sub") or str(token.get("id_token", "")),
    }

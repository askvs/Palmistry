from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.errors import AuthError, OAuthNotConfigured
from app.auth.oauth import google as google_oauth
from app.auth.rbac import get_current_user
from app.config import settings
from app.db.session import get_db
from app.middleware.rate_limit import rate_limit
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshResponse,
    RegisterRequest,
    UserOut,
)
from app.utils.logging import logger

router = APIRouter()

REFRESH_COOKIE = "palmistry_refresh"


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        # SameSite=None (needed when frontend and API are on different
        # sites, e.g. Vercel + Render) is only accepted by browsers
        # together with Secure. Local HTTP dev keeps Lax.
        samesite="none" if settings.REFRESH_COOKIE_SECURE else "lax",
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE, path="/api/v1/auth")


def _auth_response(db: Session, user: User, response: Response) -> AuthResponse:
    from app.auth.tokens import create_access_token

    access_token = create_access_token(user.id, user.role)
    refresh_token = service.issue_refresh_token(db, user)
    _set_refresh_cookie(response, refresh_token)
    return AuthResponse(
        user=UserOut.model_validate(user),
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/auth/register",
    response_model=AuthResponse,
    status_code=201,
    dependencies=[Depends(rate_limit("register"))],
)
async def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    user = service.register_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        admin_invite_code=payload.admin_invite_code,
    )
    return _auth_response(db, user, response)


@router.post(
    "/auth/login",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit("login"))],
)
async def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = service.authenticate(db, email=payload.email, password=payload.password)
    logger.info("user login user_id=%s", user.id)
    return _auth_response(db, user, response)


@router.post(
    "/auth/refresh",
    response_model=RefreshResponse,
    dependencies=[Depends(rate_limit("refresh"))],
)
async def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE, "")
    if not raw_token:
        raise _missing_refresh()
    user, new_raw = service.rotate_refresh_token(db, raw_token)
    _set_refresh_cookie(response, new_raw)
    from app.auth.tokens import create_access_token

    return RefreshResponse(
        user=UserOut.model_validate(user),
        access_token=create_access_token(user.id, user.role),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _missing_refresh():
    from fastapi import HTTPException, status

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


@router.post("/auth/logout", status_code=204)
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(REFRESH_COOKIE, "")
    if raw_token:
        service.revoke_refresh_token(db, raw_token)
    _clear_refresh_cookie(response)
    return None


@router.get("/auth/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.get("/auth/google/authorize")
async def google_authorize(request: Request):
    if not google_oauth.is_configured():
        raise OAuthNotConfigured("Google login is not configured on this server")
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await google_oauth.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def google_callback(request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        token = await google_oauth.authorize_access_token(request)
        profile = google_oauth.extract_profile(token)
    except AuthError:
        logger.warning("google oauth callback failed")
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?oauth=error")
    user = service.upsert_oauth_user(
        db,
        email=profile["email"],
        full_name=profile["full_name"],
        google_id=profile["google_id"],
    )
    refresh_token = service.issue_refresh_token(db, user)
    _set_refresh_cookie(response, refresh_token)
    logger.info("google oauth login user_id=%s", user.id)
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?oauth=success")

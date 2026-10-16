from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.cookies import REFRESH_COOKIE, clear_refresh_cookie, set_refresh_cookie
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

# The refresh cookie is written by app.auth.cookies.set_refresh_cookie, which
# couples Secure to SameSite (Secure + None behind an HTTPS origin such as
# the deployed Vercel frontend; Lax for plain-HTTP local development).


def _auth_response(
    db: Session, user: User, response: Response, request: Request
) -> AuthResponse:
    from app.auth.tokens import create_access_token

    access_token = create_access_token(user.id, user.role)
    refresh_token = service.issue_refresh_token(db, user)
    set_refresh_cookie(response, refresh_token, request)
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
async def register(
    request: Request, payload: RegisterRequest, response: Response, db: Session = Depends(get_db)
):
    user = service.register_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        admin_invite_code=payload.admin_invite_code,
    )
    return _auth_response(db, user, response, request)


@router.post(
    "/auth/login",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit("login"))],
)
async def login(
    request: Request, payload: LoginRequest, response: Response, db: Session = Depends(get_db)
):
    user = service.authenticate(db, email=payload.email, password=payload.password)
    logger.info("user login user_id=%s", user.id)
    return _auth_response(db, user, response, request)


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
    set_refresh_cookie(response, new_raw, request)
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
    clear_refresh_cookie(response)
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
    set_refresh_cookie(response, refresh_token, request)
    logger.info("google oauth login user_id=%s", user.id)
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?oauth=success")

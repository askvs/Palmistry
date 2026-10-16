"""Per-role signup/login portals (D-014): /auth/{role}/register and /auth/{role}/login."""
import enum

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.cookies import set_refresh_cookie
from app.auth.errors import AuthError
from app.auth.rbac import get_current_user
from app.config import settings
from app.db.session import get_db
from app.middleware.rate_limit import rate_limit
from app.models.user import User, UserRole
from app.schemas.auth import AuthResponse, RoleLoginRequest, RoleRegisterRequest, UserOut
from app.utils.logging import logger

router = APIRouter()


class Portal(str, enum.Enum):
    user = "user"
    tarot_reader = "tarot-reader"
    spiritual_consultant = "spiritual-consultant"
    admin = "admin"


PORTAL_TO_ROLE: dict[Portal, UserRole] = {
    Portal.user: UserRole.user,
    Portal.tarot_reader: UserRole.tarot_reader,
    Portal.spiritual_consultant: UserRole.spiritual_consultant,
    Portal.admin: UserRole.admin,
}


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
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _resolve_role(portal: Portal) -> UserRole:
    return PORTAL_TO_ROLE[portal]


@router.post(
    "/auth/{portal}/register",
    response_model=AuthResponse,
    status_code=201,
    dependencies=[Depends(rate_limit("register"))],
)
async def portal_register(
    portal: Portal,
    request: Request,
    payload: RoleRegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    role = _resolve_role(portal)
    user = service.register_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=role,
        admin_invite_code=payload.admin_invite_code,
    )
    return _auth_response(db, user, response, request)


@router.post(
    "/auth/{portal}/login",
    response_model=AuthResponse,
    dependencies=[Depends(rate_limit("login"))],
)
async def portal_login(
    portal: Portal,
    request: Request,
    payload: RoleLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    role = _resolve_role(portal)
    user = service.authenticate(
        db, email=payload.email, password=payload.password, expected_role=role
    )
    logger.info("portal login user_id=%s portal=%s", user.id, portal.value)
    return _auth_response(db, user, response, request)

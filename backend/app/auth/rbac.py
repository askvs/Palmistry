# RBAC dependencies for permission checks.
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import tokens
from app.db.session import get_db
from app.models.user import User, UserRole

_bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def _load_user(db: Session, user_id: str) -> User | None:
    try:
        parsed = uuid.UUID(user_id)
    except ValueError:
        return None
    user = db.get(User, parsed)
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise CREDENTIALS_EXCEPTION
    try:
        payload = tokens.decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise CREDENTIALS_EXCEPTION
    if payload.get("type") != tokens.TOKEN_TYPE_ACCESS:
        raise CREDENTIALS_EXCEPTION
    user = _load_user(db, payload.get("sub", ""))
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    # Return user if token valid, else None.
    if credentials is None:
        return None
    try:
        payload = tokens.decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        return None
    if payload.get("type") != tokens.TOKEN_TYPE_ACCESS:
        return None
    return _load_user(db, payload.get("sub", ""))


def require_roles(*allowed: UserRole):
    # Build dependency enforcing one of the allowed roles.

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return user

    return _checker


# Common role bundles.
require_user = require_roles(UserRole.user, UserRole.tarot_reader, UserRole.spiritual_consultant, UserRole.admin)
require_tarot_reader = require_roles(UserRole.tarot_reader, UserRole.admin)
require_spiritual_consultant = require_roles(UserRole.spiritual_consultant, UserRole.admin)
require_admin = require_roles(UserRole.admin)

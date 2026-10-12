# Auth service: registration, login, tokens, and OAuth linking.
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth import tokens
from app.auth.errors import (
    AdminSignupForbidden,
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidRefreshToken,
    WrongPortalError,
)
from app.auth.password import hash_password, verify_password
from app.models.user import User, UserRole
from app.utils.logging import logger


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email.lower())).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def register_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: UserRole = UserRole.user,
    admin_invite_code: str | None = None,
) -> User:
    normalized = email.lower()
    existing = get_user_by_email(db, normalized)
    if existing is not None:
        raise EmailAlreadyRegistered("An account with this email already exists")
    if role == UserRole.admin:
        _verify_admin_signup_code(admin_invite_code)
    user = User(
        email=normalized,
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("user registered user_id=%s email=%s role=%s", user.id, user.email, role.value)

    # Notify admins of new account; never blocks signup.
    try:
        from app.services.notifications import notify_new_user

        notify_new_user(
            new_user_id=user.id,
            new_user_email=user.email,
            new_user_role=user.role,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to notify admins of new user %s: %s", user.id, exc)

    return user


def _verify_admin_signup_code(code: str | None) -> None:
    from app.config import settings

    if not settings.ADMIN_SIGNUP_CODE:
        raise AdminSignupForbidden("Admin self-signup is disabled on this server")
    if code != settings.ADMIN_SIGNUP_CODE:
        raise AdminSignupForbidden("Invalid admin invite code")


def authenticate(
    db: Session, *, email: str, password: str, expected_role: UserRole | None = None
) -> User:
    user = get_user_by_email(db, email)
    if user is None or user.password_hash is None or not verify_password(password, user.password_hash):
        raise InvalidCredentials("Invalid email or password")
    if not user.is_active:
        raise InvalidCredentials("Account is disabled")
    if expected_role is not None and user.role != expected_role:
        raise WrongPortalError(
            f"This account is registered as a {user.role.value.replace('_', ' ')}. "
            f"Use the {user.role.value.replace('_', ' ')} portal."
        )
    return user


def issue_refresh_token(db: Session, user: User, *, rotated_from: uuid.UUID | None = None) -> str:
    from app.models.refresh_token import RefreshToken

    raw = tokens.generate_refresh_token()
    token = RefreshToken(
        user_id=user.id,
        token_hash=tokens.hash_refresh_token(raw),
        expires_at=tokens.refresh_token_expiry(),
        rotated_from=rotated_from,
    )
    db.add(token)
    db.commit()
    return raw


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[User, str]:
    # Validate refresh token and issue replacement; revoked reuse revokes all.
    from app.models.refresh_token import RefreshToken

    token_hash = tokens.hash_refresh_token(raw_token)
    record = db.scalars(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).first()

    if record is None:
        raise InvalidRefreshToken("Invalid refresh token")

    now = datetime.now(timezone.utc)
    if record.revoked_at is not None:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == record.user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
        logger.warning(
            "refresh token reuse detected user_id=%s token_id=%s — all sessions revoked",
            record.user_id,
            record.id,
        )
        raise InvalidRefreshToken("Refresh token no longer valid")

    if record.expires_at < now:
        raise InvalidRefreshToken("Refresh token expired")

    user = get_user_by_id(db, record.user_id)
    if user is None or not user.is_active:
        raise InvalidRefreshToken("Account is disabled")

    record.revoked_at = now
    new_raw = issue_refresh_token(db, user, rotated_from=record.id)
    return user, new_raw


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    from app.models.refresh_token import RefreshToken

    token_hash = tokens.hash_refresh_token(raw_token)
    record = db.scalars(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).first()
    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        db.commit()


def upsert_oauth_user(
    db: Session, *, email: str, full_name: str, google_id: str
) -> User:
    # Create or link Google-authenticated account by email.
    normalized = email.lower()
    user = get_user_by_email(db, normalized)
    if user is not None:
        if user.google_id is None:
            user.google_id = google_id
            db.commit()
            db.refresh(user)
        elif user.google_id != google_id:
            raise InvalidCredentials("This email is already linked to a different Google account")
        return user
    user = User(
        email=normalized,
        full_name=full_name,
        google_id=google_id,
        role=UserRole.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("oauth user upserted user_id=%s email=%s", user.id, user.email)
    return user

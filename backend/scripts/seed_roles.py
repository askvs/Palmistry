"""Seed one demo account per role (§49.3) so role-based logins can be tested.

Usage (from backend/ with the project venv):
    python -m scripts.seed_roles [--password Palmistry123!]

Idempotent: existing accounts are left untouched; only missing ones are created.
Promote existing accounts to their target role if they already exist and differ.
"""
import argparse
import sys

from sqlalchemy import select, update

from app.auth.password import hash_password
from app.db.session import get_db
from app.models.user import User, UserRole
from app.utils.logging import configure_logging

DEMO_ACCOUNTS = [
    ("user@palmistry.example.com", "Sample User", UserRole.user),
    ("reader@palmistry.example.com", "Sample Reader", UserRole.tarot_reader),
    ("consultant@palmistry.example.com", "Sample Consultant", UserRole.spiritual_consultant),
    ("admin@palmistry.example.com", "Platform Admin", UserRole.admin),
]


def seed(password: str) -> None:
    db = next(get_db())
    try:
        for email, full_name, role in DEMO_ACCOUNTS:
            existing = db.scalars(select(User).where(User.email == email)).first()
            if existing is None:
                db.add(
                    User(
                        email=email,
                        full_name=full_name,
                        role=role,
                        password_hash=hash_password(password),
                    )
                )
                print(f"created {email} ({role.value})")
            elif existing.role != role:
                db.execute(update(User).where(User.id == existing.id).values(role=role))
                print(f"promoted {email} -> {role.value}")
            else:
                print(f"ok {email} ({role.value})")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    configure_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--password", default="Palmistry123!")
    args = parser.parse_args()
    try:
        seed(args.password)
    except Exception as exc:  # pragma: no cover
        print(f"seed failed: {exc}", file=sys.stderr)
        sys.exit(1)

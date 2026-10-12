"""Seed an administrator account (run from backend/).

Usage:
    python -m scripts.create_admin --email admin@example.com --password <pw> [--name "Admin"]

Prompts for the password interactively when not provided.
"""

import argparse
import getpass
import sys

from sqlalchemy import select

from app.auth.password import hash_password
from app.db.session import get_engine
from app.models.user import User, UserRole


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or promote an admin user")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--password", help="Password (prompted if omitted)")
    parser.add_argument("--name", default=None, help="Display name (defaults to email prefix)")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Admin password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters", file=sys.stderr)
        return 1

    from sqlalchemy.orm import Session

    email = args.email.lower()
    engine = get_engine()
    with Session(engine) as db:
        existing = db.scalars(select(User).where(User.email == email)).first()
        if existing is not None:
            existing.role = UserRole.admin
            existing.is_active = True
            db.commit()
            print(f"Existing user promoted to admin: {email}")
        else:
            user = User(
                email=email,
                full_name=args.name or email.split("@")[0],
                password_hash=hash_password(password),
                role=UserRole.admin,
            )
            db.add(user)
            db.commit()
            print(f"Admin user created: {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

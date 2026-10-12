# Password hashing helpers.
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2 hasher instance.
_hasher = PasswordHasher()  # Argon2id is the default algorithm


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    except Exception:
        return False

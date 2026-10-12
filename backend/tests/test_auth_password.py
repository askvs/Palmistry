from argon2 import PasswordHasher

from app.auth.password import hash_password, verify_password

PHC_ARGON2ID_PREFIX = "$argon2id$"


def test_hash_is_argon2id():
    hashed = hash_password("correct horse battery staple")
    assert hashed.startswith(PHC_ARGON2ID_PREFIX), "spec §49.3 requires Argon2id"


def test_verify_accepts_correct_password():
    hashed = hash_password("s3cret-passphrase")
    assert verify_password("s3cret-passphrase", hashed) is True


def test_verify_rejects_wrong_password():
    hashed = hash_password("s3cret-passphrase")
    assert verify_password("wrong-passphrase", hashed) is False


def test_verify_rejects_garbage_hash():
    assert verify_password("anything", "not-a-valid-hash") is False


def test_hash_is_salted_per_call():
    a = hash_password("same-password")
    b = hash_password("same-password")
    assert a != b


def test_argon2_default_parameters():
    hashed = hash_password("parameters-check")
    assert hashed.startswith(PHC_ARGON2ID_PREFIX)
    parts = hashed.split("$")
    assert parts[2].startswith("v="), "PHC format must carry the argon2 version"

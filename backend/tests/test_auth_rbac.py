# RBAC dependencies against the permission matrix.

import uuid

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import rbac
from app.models.user import User, UserRole


def _make_user(role: UserRole) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{role.value}@example.com",
        full_name=role.value.title(),
        role=role,
    )


def _guarded_app(role_dependency):
    test_app = FastAPI()

    @test_app.get("/guarded")
    async def guarded(user: User = Depends(role_dependency)):
        return {"role": user.role.value}

    return test_app


def _client_as(test_app: FastAPI, role: UserRole) -> TestClient:
    user = _make_user(role)

    async def _override():
        return user

    test_app.dependency_overrides[rbac.get_current_user] = _override
    return TestClient(test_app)


MATRIX = [
    (rbac.require_admin, [UserRole.admin]),
    (rbac.require_tarot_reader, [UserRole.tarot_reader, UserRole.admin]),
    (
        rbac.require_spiritual_consultant,
        [UserRole.spiritual_consultant, UserRole.admin],
    ),
    (
        rbac.require_user,
        [UserRole.user, UserRole.tarot_reader, UserRole.spiritual_consultant, UserRole.admin],
    ),
    (
        rbac.require_roles(UserRole.user),
        [UserRole.user],
    ),
]


class TestPermissionMatrix:
    @pytest.mark.parametrize(
        "dependency,allowed_roles",
        MATRIX,
        ids=["admin", "tarot_reader", "spiritual_consultant", "any_user", "only_user"],
    )
    def test_matrix(self, dependency, allowed_roles):
        test_app = _guarded_app(dependency)
        for role in UserRole:
            resp = _client_as(test_app, role).get("/guarded")
            if role in allowed_roles:
                assert resp.status_code == 200, f"{role.value} should be allowed"
                assert resp.json()["role"] == role.value
            else:
                assert resp.status_code == 403, f"{role.value} should be forbidden"
        test_app.dependency_overrides.clear()


class TestUnauthenticated:
    def test_no_token_401(self, client):
        """Hitting the real app without a token yields 401 with the error envelope."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        assert resp.json()["code"] == "HTTP_401"

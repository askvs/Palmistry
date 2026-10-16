import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

TEST_DB_URL = os.environ.setdefault(
    "DATABASE_TEST_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/palmistry_test",
)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_migrations(db_url: str) -> None:
    alembic_cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
def test_engine():
    # Test database engine with migrations applied once per session.
    from sqlalchemy import create_engine

    from app.db import session as db_session

    assert TEST_DB_URL in (
        db_session.settings.DATABASE_TEST_URL,
        os.environ.get("DATABASE_TEST_URL", ""),
    ) or "palmistry_test" in TEST_DB_URL, "refusing to run tests against a non-test database"

    db_session.settings.DATABASE_URL = TEST_DB_URL
    db_session._engine = None
    db_session._SessionLocal = None

    _run_migrations(TEST_DB_URL)

    engine = db_session.get_engine()
    yield engine

    engine.dispose()
    db_session._engine = None
    db_session._SessionLocal = None


@pytest.fixture(autouse=True)
def _clean_tables(request, test_engine):
    # Reset auth tables and rate-limit buckets before each test.
    from app.middleware import rate_limit

    rate_limit._buckets.clear()

    if "without_db" in request.keywords:
        yield
        return

    # Requests whose endpoints crashed can leave pooled sessions idle-in-transaction;
    # those open transactions block TRUNCATE and serve stale snapshots to later tests.
    # Recycle every pooled connection first so the truncate starts from a clean slate.
    test_engine.dispose()
    with test_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.exec_driver_sql(
            "TRUNCATE TABLE audit_logs, error_logs, custom_spreads, recommendation_events, recommendation_records, "
            "consultation_messages, consultations, readings, performance_samples, refresh_tokens, users, "
            "profiles, profile_interests, profile_goals, "
            "session_feedbacks, session_notes, booking_events, booking_messages, bookings, "
            "availability_slots, availability_rules, "
            "consultant_profiles CASCADE"
        )
    yield


@pytest.fixture()
def client(test_engine):
    from app.main import app

    with TestClient(app) as c:
        yield c

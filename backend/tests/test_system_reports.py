# System Reports module: overview, health, error reports, and performance reports.
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.error_log import ErrorKind, ErrorLevel, ErrorLog
from app.models.reading import Reading, ReadingStatus, ReadingType
from app.models.user import User, UserRole
from app.services.palm_analysis.preprocessor import PalmValidationError

PASSWORD = "TestPass123!"

REPORT_PATHS = (
    "/api/v1/admin/reports/overview",
    "/api/v1/admin/reports/health",
    "/api/v1/admin/reports/errors",
    "/api/v1/admin/reports/performance",
)

# Minimal payload with a valid PNG signature (content is never decoded in unit tests).
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"palmistry-test-image"


def _register(client, email, full_name, role="user"):
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "full_name": full_name,
            "role": role,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp


def _login(client, email):
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _promote(test_engine, email, role):
    with Session(test_engine) as db:
        db.execute(update(User).where(User.email == email).values(role=role))
        db.commit()


@pytest.fixture()
def admin_headers(client, test_engine):
    email = f"reports-admin-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Reports Admin")
    _promote(test_engine, email, UserRole.admin)
    return _login(client, email)


@pytest.fixture()
def plain_headers(client):
    email = f"reports-user-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, "Reports User")
    return _login(client, email)


def _seed_user(test_engine, *, role=UserRole.user, created_at=None, email=None):
    with Session(test_engine) as db:
        user = User(
            id=uuid.uuid4(),
            email=email or f"seed-{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hash",
            full_name="Seeded User",
            role=role,
            is_active=True,
        )
        if created_at is not None:
            user.created_at = created_at
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def _seed_reading(test_engine, *, user_id, reading_type=ReadingType.tarot, created_at=None, duration_ms=None):
    with Session(test_engine) as db:
        reading = Reading(
            id=uuid.uuid4(),
            user_id=user_id,
            type=reading_type,
            status=ReadingStatus.completed,
            title="Seeded Reading",
            summary="Seeded for reports.",
            result={},
        )
        if created_at is not None:
            reading.created_at = created_at
        if duration_ms is not None:
            reading.duration_ms = duration_ms
        db.add(reading)
        db.commit()
        db.refresh(reading)
        return reading


def _seed_error(
    test_engine,
    *,
    kind=ErrorKind.server_error,
    level=ErrorLevel.error,
    message="An unexpected error occurred",
    path="/api/v1/readings/tarot",
    method="POST",
    status_code=500,
    occurrences=1,
    last_seen_at=None,
):
    with Session(test_engine) as db:
        row = ErrorLog(
            id=uuid.uuid4(),
            level=level,
            kind=kind,
            status_code=status_code,
            method=method,
            path=path,
            message=message,
            occurrences=occurrences,
            last_seen_at=last_seen_at or datetime.now(timezone.utc),
        )
        if last_seen_at is not None:
            row.created_at = last_seen_at
        db.add(row)
        db.commit()
        db.refresh(row)
        return row


def _error_rows(test_engine, kind=None):
    with Session(test_engine) as db:
        query = db.query(ErrorLog)
        if kind is not None:
            query = query.where(ErrorLog.kind == kind)
        return query.order_by(ErrorLog.last_seen_at.desc()).all()


def _seed_sample(test_engine, *, duration_ms, status_code=200, sampled_at=None, path="/api/v1/readings/tarot", method="POST"):
    from app.models.performance_sample import PerformanceSample

    with Session(test_engine) as db:
        row = PerformanceSample(
            id=uuid.uuid4(),
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
        )
        if sampled_at is not None:
            row.sampled_at = sampled_at
        db.add(row)
        db.commit()
        db.refresh(row)
        return row


class TestFailedAnalysisTracking:
    """Failed palm/tarot analyses are recorded with kind=analysis_failed."""

    def test_tarot_generation_failure_is_recorded(self, client, plain_headers, test_engine):
        resp = client.post(
            "/api/v1/readings/tarot",
            json={"spread": "three_card", "cards": ["Not A Real Card"]},
            headers=plain_headers,
        )
        assert resp.status_code == 400, resp.text

        rows = _error_rows(test_engine, ErrorKind.analysis_failed)
        assert len(rows) == 1
        row = rows[0]
        assert row.status_code == 400
        assert row.path == "/api/v1/readings/tarot"
        assert row.method == "POST"
        assert row.message.startswith("tarot analysis failed:")
        assert "TarotInterpretationError" in row.message
        assert row.occurrences == 1
        assert row.actor_id is not None

    def test_repeated_failure_deduplicates_into_occurrences(self, client, plain_headers, test_engine):
        payload = {"spread": "three_card", "cards": ["Not A Real Card"]}
        for _ in range(2):
            resp = client.post("/api/v1/readings/tarot", json=payload, headers=plain_headers)
            assert resp.status_code == 400, resp.text

        rows = _error_rows(test_engine, ErrorKind.analysis_failed)
        assert len(rows) == 1
        assert rows[0].occurrences == 2

    def test_palm_generation_failure_is_recorded(self, client, plain_headers, test_engine, monkeypatch):
        def boom(**_kwargs):
            raise PalmValidationError(
                "NO_PALM_DETECTED", "No palm was detected in the image.", 422
            )

        monkeypatch.setattr("app.services.palm_analysis.pipeline.analyze_palm_image", boom)

        resp = client.post(
            "/api/v1/readings/palm",
            files={"image": ("palm.png", PNG_BYTES, "image/png")},
            headers=plain_headers,
        )
        assert resp.status_code == 422, resp.text

        rows = _error_rows(test_engine, ErrorKind.analysis_failed)
        assert len(rows) == 1
        row = rows[0]
        assert row.status_code == 422
        assert row.path == "/api/v1/readings/palm"
        assert row.message.startswith("palm analysis failed:")
        assert "PalmValidationError" in row.message

    def test_analysis_recording_never_breaks_the_request(self, client, plain_headers, test_engine, monkeypatch):
        """A monitoring failure must not change the API response."""

        def boom(**_kwargs):
            raise RuntimeError("monitoring exploded")

        monkeypatch.setattr("app.middleware.monitoring._upsert_error_row", boom)

        resp = client.post(
            "/api/v1/readings/tarot",
            json={"spread": "three_card", "cards": ["Not A Real Card"]},
            headers=plain_headers,
        )
        assert resp.status_code == 400, resp.text
        assert resp.json()["code"] == "TAROT_UNKNOWN_CARD"


class TestAnalysisDuration:
    """Analysis-generation duration is persisted on created readings."""

    def test_tarot_reading_records_duration(self, client, plain_headers, test_engine, monkeypatch):
        monkeypatch.setattr(
            "app.services.reading.service.generate_tarot_interpretation",
            lambda **_kwargs: {"narrative": {"summary": "stub"}, "spread_name": "Three Card"},
        )
        resp = client.post(
            "/api/v1/readings/tarot",
            json={"spread": "three_card", "cards": ["The Fool"]},
            headers=plain_headers,
        )
        assert resp.status_code == 201, resp.text

        with Session(test_engine) as db:
            reading = db.query(Reading).order_by(Reading.created_at.desc()).first()
        assert reading is not None
        assert reading.duration_ms is not None
        assert reading.duration_ms >= 0


class TestPerformanceSamples:
    """API latency samples are buffered in-process and flushed on demand."""

    def test_flush_persists_buffered_samples_once(self, client, test_engine):
        from app.middleware import monitoring
        from app.models.performance_sample import PerformanceSample

        monitoring.reset_metrics()
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200, resp.text

        written = monitoring.flush_samples()
        assert written == 1

        # Nothing new was buffered since; a second flush is a no-op.
        assert monitoring.flush_samples() == 0

        with Session(test_engine) as db:
            samples = db.query(PerformanceSample).all()
        assert len(samples) == 1
        sample = samples[0]
        assert sample.method == "GET"
        assert sample.path == "/api/v1/health"
        assert sample.status_code == 200
        assert sample.duration_ms >= 0
        assert sample.sampled_at is not None

    def test_noisy_paths_are_not_buffered(self, client):
        from app.middleware import monitoring

        monitoring.reset_metrics()
        assert client.get("/health").status_code == 200
        assert client.get("/api/docs").status_code == 200

        assert monitoring.flush_samples() == 0

    def test_flush_failure_does_not_raise_and_keeps_buffer(self, client, monkeypatch):
        from app.middleware import monitoring

        monitoring.reset_metrics()
        assert client.get("/api/v1/health").status_code == 200

        def boom():
            raise RuntimeError("engine exploded")

        monkeypatch.setattr("app.db.session.get_engine", boom)
        assert monitoring.flush_samples() == 0

        # The samples were put back, so a later flush persists them.
        monkeypatch.undo()
        assert monitoring.flush_samples() == 1


class TestReportsAccess:
    """Report endpoints are admin-only, enforced by the router."""

    def test_reports_require_admin(self, client, plain_headers, admin_headers):
        for path in REPORT_PATHS:
            assert client.get(path).status_code == 401, path
            assert client.get(path, headers=plain_headers).status_code == 403, path
            assert client.get(path, headers=admin_headers).status_code == 200, path


class TestSystemOverviewReport:
    def test_overview_counts_and_period_window(self, client, admin_headers, test_engine):
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=30)

        recent_user = _seed_user(test_engine)
        old_user = _seed_user(test_engine, created_at=old)

        _seed_reading(test_engine, user_id=recent_user.id, reading_type=ReadingType.tarot)
        _seed_reading(test_engine, user_id=recent_user.id, reading_type=ReadingType.palm)
        _seed_reading(test_engine, user_id=old_user.id, reading_type=ReadingType.tarot, created_at=old)

        _seed_error(
            test_engine,
            kind=ErrorKind.analysis_failed,
            message="tarot analysis failed: Boom: bad card",
            path="/api/v1/readings/tarot",
            status_code=400,
            occurrences=2,
        )
        _seed_error(
            test_engine,
            kind=ErrorKind.analysis_failed,
            message="palm analysis failed: Boom: bad image",
            path="/api/v1/readings/palm",
            status_code=422,
            occurrences=1,
            last_seen_at=old,
        )
        _seed_error(test_engine, kind=ErrorKind.server_error, message="HTTP 500", status_code=500)

        resp = client.get("/api/v1/admin/reports/overview?days=7", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        assert body["days"] == 7
        # Two seeded users plus the admin registered by the fixture.
        assert body["users"]["total"] == 3
        assert body["users"]["new_in_period"] == 2

        analyses = body["analyses"]
        assert analyses["successful"] == 2
        assert analyses["failed"] == 2
        assert analyses["total"] == 4
        assert analyses["successful_all_time"] == 3
        assert analyses["failed_all_time"] == 3
        assert analyses["total_all_time"] == 6

        by_type = {row["type"]: row["count"] for row in analyses["success_by_type"]}
        assert by_type["tarot"] == 1
        assert by_type["palm"] == 1
        failed_by_type = {row["type"]: row["count"] for row in analyses["failed_by_type"]}
        assert failed_by_type["tarot"] == 2
        assert failed_by_type["palm"] == 0
        assert analyses["failed_tracking_since"] is not None

    def test_overview_days_is_validated(self, client, admin_headers):
        resp = client.get("/api/v1/admin/reports/overview?days=0", headers=admin_headers)
        assert resp.status_code == 422


class TestSystemHealthReport:
    def test_health_reports_real_checks(self, client, admin_headers):
        resp = client.get("/api/v1/admin/reports/health", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        assert body["backend"]["status"] == "ok"
        assert body["database"]["status"] == "ok"
        assert body["database"]["latency_ms"] is not None
        assert body["database"]["latency_ms"] >= 0
        # AI availability is a configuration check, reported honestly.
        assert body["ai_service"]["status"] in {"configured", "not_configured"}
        assert body["ai_provider"]
        assert body["ai_model"]
        assert body["environment"]
        assert body["version"]
        assert body["uptime_seconds"] >= 0
        assert body["started_at"]
        assert body["notes"]
        for block in ("backend", "database", "ai_service"):
            assert body[block]["detail"]


class TestErrorReport:
    def test_error_report_filters_categories_and_sanitizes(self, client, admin_headers, test_engine):
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=30)
        long_message = "Something   exploded\n" + "x" * 300

        _seed_error(
            test_engine,
            kind=ErrorKind.server_error,
            message=long_message,
            path="/api/v1/readings/tarot",
            status_code=500,
        )
        _seed_error(
            test_engine,
            kind=ErrorKind.analysis_failed,
            message="tarot analysis failed: Boom: bad card",
            path="/api/v1/readings/tarot",
            status_code=400,
            occurrences=3,
            last_seen_at=now - timedelta(hours=1),
        )
        acked = _seed_error(
            test_engine,
            kind=ErrorKind.forbidden,
            message="HTTP 403",
            status_code=403,
            last_seen_at=now - timedelta(hours=2),
        )
        _seed_error(
            test_engine,
            kind=ErrorKind.auth_failure,
            message="HTTP 401",
            status_code=401,
            occurrences=5,
            last_seen_at=old,
        )

        with Session(test_engine) as db:
            db.query(ErrorLog).filter(ErrorLog.id == acked.id).update(
                {"acknowledged_at": now}
            )
            db.commit()

        resp = client.get("/api/v1/admin/reports/errors?days=7&limit=50", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        # The auth_failure row last seen 30 days ago is out of the window.
        assert body["counts"]["rows"] == 3
        assert body["counts"]["total"] == 5
        assert body["counts"]["failed_analyses"] == 3
        assert body["counts"]["server_errors"] == 1
        by_category = {row["category"]: row["occurrences"] for row in body["counts"]["by_category"]}
        assert by_category == {"server_error": 1, "analysis_failed": 3, "forbidden": 1}

        times = [item["last_seen_at"] for item in body["items"]]
        assert times == sorted(times, reverse=True)

        items_by_cat = {item["category"]: item for item in body["items"]}
        server_item = items_by_cat["server_error"]
        assert "\n" not in server_item["description"]
        assert len(server_item["description"]) <= 200
        assert server_item["method"] == "POST"
        assert server_item["path"] == "/api/v1/readings/tarot"
        assert server_item["status_code"] == 500
        assert server_item["first_seen_at"] is not None
        assert items_by_cat["forbidden"]["acknowledged_at"] is not None
        assert items_by_cat["analysis_failed"]["acknowledged_at"] is None
        assert body["notes"]

    def test_error_report_days_and_limit(self, client, admin_headers, test_engine):
        now = datetime.now(timezone.utc)
        for index in range(4):
            _seed_error(
                test_engine,
                message=f"seeded error {index}",
                path="/api/v1/seeded",
                status_code=500,
                last_seen_at=now - timedelta(minutes=index),
            )
        _seed_error(
            test_engine,
            message="ancient error",
            path="/api/v1/seeded",
            status_code=500,
            last_seen_at=now - timedelta(days=15),
        )

        resp = client.get("/api/v1/admin/reports/errors?days=7&limit=2", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["counts"]["rows"] == 4

        resp30 = client.get("/api/v1/admin/reports/errors?days=30&limit=50", headers=admin_headers)
        assert resp30.status_code == 200, resp30.text
        assert resp30.json()["counts"]["rows"] == 5


class TestPerformanceReport:
    def test_performance_math_and_period_filter(self, test_engine):
        from app.middleware import monitoring
        from app.services.admin import reports as reports_service

        monitoring.reset_metrics()
        now = datetime.now(timezone.utc)

        for duration, status in ((10.0, 200), (20.0, 200), (30.0, 500), (40.0, 200), (50.0, 200)):
            _seed_sample(test_engine, duration_ms=duration, status_code=status)
        _seed_sample(test_engine, duration_ms=1000.0, sampled_at=now - timedelta(days=15))

        recent_user = _seed_user(test_engine)
        _seed_reading(test_engine, user_id=recent_user.id, reading_type=ReadingType.tarot, duration_ms=100.0)
        _seed_reading(test_engine, user_id=recent_user.id, reading_type=ReadingType.tarot, duration_ms=200.0)
        _seed_reading(test_engine, user_id=recent_user.id, reading_type=ReadingType.palm, duration_ms=300.0)

        with Session(test_engine) as db:
            result = reports_service.performance_report(db, days=7)

        api = result["api"]
        assert api["status"] == "ok"
        assert api["requests"] == 5
        assert api["avg_ms"] == 30.0
        assert api["p50_ms"] == 30.0
        assert api["p95_ms"] == 50.0
        assert api["max_ms"] == 50.0
        assert api["error_rate"] == 0.2
        assert api["first_sample_at"] is not None
        assert api["last_sample_at"] is not None

        analysis = result["analysis_generation"]
        assert analysis["status"] == "ok"
        assert analysis["samples"] == 3
        assert analysis["avg_ms"] == 200.0
        assert analysis["p95_ms"] == 300.0
        assert analysis["max_ms"] == 300.0
        by_type = {row["type"]: row for row in analysis["by_type"]}
        assert by_type["tarot"]["samples"] == 2
        assert by_type["tarot"]["avg_ms"] == 150.0
        assert by_type["palm"]["samples"] == 1
        assert by_type["palm"]["avg_ms"] == 300.0

        with Session(test_engine) as db:
            wider = reports_service.performance_report(db, days=30)
        assert wider["api"]["requests"] == 6
        assert wider["api"]["max_ms"] == 1000.0
        assert wider["api"]["avg_ms"] == 191.7

    def test_analysis_no_data_is_honest(self, test_engine):
        from app.middleware import monitoring
        from app.services.admin import reports as reports_service

        monitoring.reset_metrics()
        with Session(test_engine) as db:
            result = reports_service.performance_report(db, days=7)

        assert result["api"]["status"] == "no_data"
        assert result["api"]["requests"] == 0
        assert result["api"]["avg_ms"] is None
        assert result["api"]["error_rate"] is None
        assert result["analysis_generation"]["status"] == "no_data"
        assert result["analysis_generation"]["avg_ms"] is None
        assert result["analysis_generation"]["by_type"] == []
        assert result["notes"]

    def test_performance_endpoint_flushes_pending_samples(self, client, admin_headers, test_engine):
        from app.middleware import monitoring
        from app.models.performance_sample import PerformanceSample

        monitoring.reset_metrics()
        assert client.get("/api/v1/health").status_code == 200

        resp = client.get("/api/v1/admin/reports/performance?days=7", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["api"]["status"] == "ok"
        # Only the health request was pending; it was flushed by the report read.
        assert body["api"]["requests"] == 1

        with Session(test_engine) as db:
            paths = {path for (path,) in db.query(PerformanceSample.path).all()}
        assert paths == {"/api/v1/health"}

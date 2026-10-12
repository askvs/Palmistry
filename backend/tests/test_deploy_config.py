import os
from app.config import Settings


def test_production_debug_defaults_false(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "false")
    s = Settings(_env_file=None)
    assert s.ENVIRONMENT == "production"
    assert s.DEBUG is False


def test_cookie_secure_flag_parses(monkeypatch):
    monkeypatch.setenv("REFRESH_COOKIE_SECURE", "true")
    s = Settings(_env_file=None)
    assert s.REFRESH_COOKIE_SECURE is True


def test_cors_origins_parses(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://app.example.com"]')
    s = Settings(_env_file=None)
    assert s.CORS_ORIGINS == ["https://app.example.com"]


def test_health_paths_unchanged():
    from app.main import create_app

    app = create_app()
    paths = [r.path for r in app.routes]
    assert "/health" in paths


def test_api_prefix_default():
    s = Settings(_env_file=None)
    assert s.API_V1_PREFIX == "/api/v1"


def test_upload_dir_default():
    s = Settings(_env_file=None)
    assert s.UPLOAD_DIR == "uploads"

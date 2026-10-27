# LLM adapter provider selection.
import groq
import json

from app.services.interpretation.llm_adapter import LLMAdapter, reset_llm_adapter


def _fake_response(content, total_tokens=12):
    class Message:
        def __init__(self, content):
            self.content = content

    class Choice:
        def __init__(self, content):
            self.message = Message(content)

    class Usage:
        def __init__(self, total_tokens):
            self.total_tokens = total_tokens

    class Response:
        def __init__(self, content, total_tokens):
            self.choices = [Choice(content)]
            self.usage = Usage(total_tokens)

    return Response(content, total_tokens)


class _FakeCompletions:
    def __init__(self, content, total_tokens):
        self._response = _fake_response(content, total_tokens)

    def create(self, **kwargs):
        return self._response


class _FakeChat:
    def __init__(self, content, total_tokens):
        self.completions = _FakeCompletions(content, total_tokens)


class _FakeGroqClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.chat = _FakeChat('{"summary":"ok"}', 12)


class _FakeOpenAIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.chat = _FakeChat('{"summary":"ok"}', 12)


class TestLLMAdapter:
    def test_groq_provider_initializes_when_openai_key_absent(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.interpretation.llm_adapter.settings.OPENAI_API_KEY", ""
        )
        monkeypatch.setattr(
            "app.services.interpretation.llm_adapter.settings.GROQ_API_KEY", "test-groq-key"
        )
        monkeypatch.setattr(
            "app.services.interpretation.llm_adapter.settings.GROQ_MODEL", "llama3-70b-8192"
        )

        monkeypatch.setattr(groq, "Groq", _FakeGroqClient, raising=False)

        adapter = LLMAdapter()
        assert adapter.provider == "groq"
        assert adapter.model == "llama3-70b-8192"
        assert adapter.is_online is True

        response = adapter.complete(prompt="hello", json_mode=True)
        assert response.rule_based is False
        assert response.provider == "groq"
        assert response.content == '{"summary":"ok"}'
        assert response.tokens == 12

        reset_llm_adapter()

    def test_rule_based_fallback_when_no_key(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.interpretation.llm_adapter.settings.OPENAI_API_KEY", ""
        )
        monkeypatch.setattr(
            "app.services.interpretation.llm_adapter.settings.GROQ_API_KEY", ""
        )

        adapter = LLMAdapter()
        assert adapter.provider == "rule_based"
        assert adapter.is_online is False

        response = adapter.complete(prompt="hello", json_mode=True)
        assert response.rule_based is True
        assert response.provider == "rule_based"
        payload = json.loads(response.content)
        assert payload["rule_based"] is True

        reset_llm_adapter()


class _RateLimit429Error(Exception):
    """Stands in for groq.RateLimitError (status_code 429)."""

    def __init__(self, message="Error code: 429 - Rate limit reached for model `qwen/qwen3.8-27b`"):
        super().__init__(message)
        self.status_code = 429


class _ScriptedCompletions:
    """Chat completions stub driven by a script of exceptions/results."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        step = self.script[min(self.calls, len(self.script)) - 1]
        if isinstance(step, Exception):
            raise step
        return _fake_response(step)


class _ScriptedChat:
    def __init__(self, script):
        self.completions = _ScriptedCompletions(script)


class _ScriptedGroqClient:
    def __init__(self, api_key, script=None):
        self.api_key = api_key
        self.chat = _ScriptedChat(script or [])


def _make_scripted_adapter(monkeypatch, script):
    """Build a Groq-backed adapter whose completions follow `script` (no real sleeps)."""
    monkeypatch.setattr(
        "app.services.interpretation.llm_adapter.settings.OPENAI_API_KEY", ""
    )
    monkeypatch.setattr(
        "app.services.interpretation.llm_adapter.settings.GROQ_API_KEY", "test-groq-key"
    )
    monkeypatch.setattr(
        "app.services.interpretation.llm_adapter.time.sleep", lambda _seconds: None
    )
    monkeypatch.setattr(
        groq, "Groq", lambda api_key: _ScriptedGroqClient(api_key, script), raising=False
    )
    adapter = LLMAdapter()
    assert adapter.provider == "groq"
    return adapter


class TestRateLimitRetry:
    def test_rate_limit_is_retried_then_succeeds(self, monkeypatch):
        adapter = _make_scripted_adapter(monkeypatch, [_RateLimit429Error(), '{"summary":"ok"}'])

        response = adapter.complete(prompt="hello", json_mode=True)

        assert response.rule_based is False
        assert response.content == '{"summary":"ok"}'
        assert adapter._client.chat.completions.calls == 2

    def test_rate_limit_exhausts_retries_then_falls_back(self, monkeypatch):
        adapter = _make_scripted_adapter(monkeypatch, [_RateLimit429Error()] * 5)

        response = adapter.complete(prompt="hello", json_mode=True)

        assert response.rule_based is True
        assert adapter._client.chat.completions.calls == 3  # 1 attempt + 2 retries

    def test_rate_limit_fallback_narrative_reports_rate_limit(self, monkeypatch):
        adapter = _make_scripted_adapter(monkeypatch, [_RateLimit429Error()] * 5)

        response = adapter.complete(prompt="hello", json_mode=True)

        payload = json.loads(response.content)
        narrative = payload["narrative"].lower()
        assert "rate limit" in narrative
        assert "no external language model credentials" not in narrative

    def test_non_rate_limit_error_is_not_retried(self, monkeypatch):
        adapter = _make_scripted_adapter(monkeypatch, [ValueError("connection reset by peer")])

        response = adapter.complete(prompt="hello", json_mode=True)

        assert response.rule_based is True
        assert adapter._client.chat.completions.calls == 1
        payload = json.loads(response.content)
        assert "provider request failed" in payload["narrative"].lower()

    def test_offline_fallback_narrative_mentions_missing_credentials(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.interpretation.llm_adapter.settings.OPENAI_API_KEY", ""
        )
        monkeypatch.setattr(
            "app.services.interpretation.llm_adapter.settings.GROQ_API_KEY", ""
        )
        adapter = LLMAdapter()

        response = adapter.complete(prompt="hello", json_mode=True)

        payload = json.loads(response.content)
        assert "no external language model credentials" in payload["narrative"]
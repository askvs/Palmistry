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
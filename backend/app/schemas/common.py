from pydantic import BaseModel


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    request_id: str
    fields: list | None = None


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str
    # Optional health fields default to unknown.
    database: str = "unknown"
    ai_provider: str = "unknown"

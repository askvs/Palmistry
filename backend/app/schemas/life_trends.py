"""Life trend analysis schemas (TASK-008 / FR-017, Milestone 3)."""
from pydantic import BaseModel, ConfigDict, Field


class TrendItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Life domain / trend name")
    domain: str = Field(..., description="Domain key")
    score: float = Field(..., ge=0.0, le=1.0, description="Current trend score (0-1)")
    direction: str = Field(..., description="rising | stable | declining")
    momentum: float = Field(..., ge=-1.0, le=1.0, description="Recent-vs-baseline momentum")
    strength: float = Field(..., ge=0.0, le=1.0, description="Evidence strength (0-1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence from data coverage")
    explanation: str = Field(..., description="Plain-language explanation")
    signals: list[str] = Field(default_factory=list, description="Contributing signals (evidence)")


class InsightItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., description="Opportunity / challenge title")
    explanation: str = Field(..., description="Why this was identified")
    signals: list[str] = Field(default_factory=list, description="Supporting signals")
    confidence: float = Field(..., ge=0.0, le=1.0)


class HistoryPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str = Field(..., description="Reading timestamp (ISO)")
    type: str | None = Field(None, description="palm | tarot")
    overall_signal: float = Field(..., ge=0.0, le=1.0)
    domains: dict[str, float] = Field(default_factory=dict)


class DataCoverageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    readings_analyzed: int = Field(..., ge=0)
    palm_readings: int = Field(..., ge=0)
    tarot_readings: int = Field(..., ge=0)
    completeness: float = Field(..., ge=0.0, le=1.0)
    goals_used: int = Field(..., ge=0)


class LifeTrendOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    life_path: str = Field(..., description="User's current life path summary")
    current_trends: list[TrendItemOut] = Field(default_factory=list, description="Active life trends")
    opportunities: list[InsightItemOut] = Field(default_factory=list, description="Identified opportunities")
    challenges: list[InsightItemOut] = Field(default_factory=list, description="Identified challenges")
    growth_potential: float = Field(..., ge=0.0, le=1.0, description="Growth potential score (0-1)")
    explanation: str = Field(..., description="Detailed explanation of the analysis")
    history: list[HistoryPointOut] = Field(default_factory=list, description="Per-reading trend history")
    data_coverage: DataCoverageOut = Field(..., description="How much user data backed this analysis")
    engine: str = Field(..., description="Analysis engine name")
    engine_version: str = Field(...)
    method: str = Field(..., description="Analysis method (feature_based_trend_scoring)")
    generated_at: str | None = Field(None)
    disclaimer: str = Field(..., description="Safety disclaimer")
    feature_vector: dict = Field(
        default_factory=dict,
        description=(
            "Flattened signal/feature export — the training input shape for a future "
            "supervised forecasting model once historical snapshots accumulate. "
            "Not used for display."
        ),
    )

from datetime import datetime

from pydantic import BaseModel, Field


class EnvironmentSource(BaseModel):
    title: str
    source_type: str = "stub"
    content: str
    url: str | None = None
    published_at: datetime | None = None
    trust_score: float | None = None
    metadata: dict = Field(default_factory=dict)


class EnvScenarioItem(BaseModel):
    shock_class: str
    description: str
    severity: int = Field(default=3, ge=1, le=5)
    likelihood: float = Field(default=0.5, ge=0, le=1)
    source_refs: list[dict] = Field(default_factory=list)


class EnvironmentOutput(BaseModel):
    scenarios: list[EnvScenarioItem]

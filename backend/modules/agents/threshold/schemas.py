from decimal import Decimal

from pydantic import Field, BaseModel


class ThresholdDecisionOutput(BaseModel):
    reversibility: str = Field(default="cheap_reversible")
    verdict: str = Field(default="probe")
    recommended_step: str | None = None
    step_budget: Decimal | None = None
    trust_level: Decimal | None = None
    rationale: str | None = None

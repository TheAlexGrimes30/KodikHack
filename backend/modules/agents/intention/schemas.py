from decimal import Decimal
from typing import Any

from pydantic import Field, BaseModel


class AssumptionItem(BaseModel):
    statement: str
    is_explicit: bool = False
    criticality: int = Field(default=3, ge=1, le=5)

class IntentOutput(BaseModel):
    title: str
    description: str | None = None
    invest_money: Decimal | None = None
    invest_effort: Decimal | None = None
    horizon_months: Decimal | None = None
    expected_result: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[AssumptionItem] = Field(default_factory=list)
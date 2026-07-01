from dataclasses import Field
from decimal import Decimal

from pydantic import BaseModel


class AttackItem(BaseModel):
    assumption_index: int | None = None
    scenario_index: int | None = None
    narrative: str
    failure_point: str | None = None
    est_loss_money: Decimal | None = None
    survivable: bool | None = None


class DestructorOutput(BaseModel):
    attacks: list[AttackItem] = Field(default_factory=list)

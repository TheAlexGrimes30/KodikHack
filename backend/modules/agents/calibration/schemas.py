from decimal import Decimal

from pydantic import BaseModel


class CalibrationOutput(BaseModel):
    predicted_value: Decimal | None = None
    actual_value: Decimal | None = None
    error_abs: Decimal | None = None
    error_rel: Decimal | None = None
    optimism_bias: Decimal | None = None
    trust_delta: Decimal | None = None
    updated_trust_score: Decimal | None = None

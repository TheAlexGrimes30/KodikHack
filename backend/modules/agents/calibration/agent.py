from decimal import Decimal
from typing import Any

from backend.modules.agents.calibration.schemas import CalibrationOutput
from backend.modules.agents.common.state import AgentState
from backend.modules.agents.common.utils import add_audit_log, decimal_or_none, clamp


class CalibrationAgent:
    """Калибровка.

    Связь с БД:
    - calibration_record -> таблица calibration_records

    Временная заглушка:
    - если fact не передан, берётся симулированное actual_value = predicted_value * 0.8.
    """

    actor = "calibration"

    def run(self, state: AgentState) -> dict[str, Any]:
        bet = state.get("bet") or {}
        trust = float(state.get("trust_score") or 0.0)

        predicted = decimal_or_none(bet.get("predicted_value"))
        actual = decimal_or_none(bet.get("actual_value"))

        if predicted is None:
            predicted = Decimal("100")
        if actual is None:
            actual = predicted * Decimal("0.8")

        error_abs = abs(predicted - actual)
        error_rel = Decimal("0") if predicted == 0 else error_abs / abs(predicted)
        optimism_bias = Decimal("0") if actual >= predicted else (predicted - actual) / abs(predicted)

        if error_rel <= Decimal("0.15"):
            trust_delta = Decimal("0.10")
        elif error_rel <= Decimal("0.35"):
            trust_delta = Decimal("0.00")
        else:
            trust_delta = Decimal("-0.10")

        updated_trust = Decimal(str(clamp(trust + float(trust_delta))))
        output = CalibrationOutput(
            predicted_value=predicted,
            actual_value=actual,
            error_abs=error_abs,
            error_rel=error_rel,
            optimism_bias=optimism_bias,
            trust_delta=trust_delta,
            updated_trust_score=updated_trust,
        )
        record = output.model_dump(mode="python")

        return {
            "calibration_record": record,
            "trust_score": float(updated_trust),
            "audit_log": add_audit_log(
                state,
                actor=self.actor,
                event_type="calibration_record_created",
                payload=output.model_dump(mode="json"),
            ),
        }

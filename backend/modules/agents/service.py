import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import SessionLog, Bet, CalibrationRecord, ThresholdDecision, Attack, EnvScenario, Assumption, Intent, \
    Session
from backend.db.enums import AgentKind, SessionStatus
from backend.modules.agents.common.state import AgentState
from backend.modules.agents.common.utils import extract_json_object
from backend.modules.agents.graph import AgentGraphBuilder


class AgentWorkflowService:
    """Сервис соединяет LangGraph с таблицами.

    Агенты не знают про SQLAlchemy. Они возвращают словари под таблицы.
    Этот service сохраняет результат в БД.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.builder = AgentGraphBuilder()
        self.analysis_graph = self.builder.build_analysis_graph()
        self.calibration_graph = self.builder.build_calibration_graph()

    async def run_analysis(
        self,
        *,
        session: Session,
        raw_intent: str,
        project_context: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> AgentState:
        state: AgentState = {
            "session_id": str(session.id),
            "project_id": str(session.project_id),
            "raw_intent": raw_intent,
            "project_context": project_context or {},
            "trust_score": float((project_context or {}).get("trust_score", 0.0)),
            "iteration": int((project_context or {}).get("iteration", 0)),
            "audit_log": [],
        }
        result: AgentState = await self.analysis_graph.ainvoke(state)
        await self._persist_analysis_result(session=session, result=result)

        session.status = SessionStatus.ANALYZED
        if commit:
            await self.db.commit()
        return result

    async def run_calibration(
        self,
        *,
        bet: Bet,
        actual_value: float | int | str | None = None,
        actual_spent: float | int | str | None = None,
        commit: bool = True,
    ) -> AgentState:
        state: AgentState = {
            "session_id": str(bet.session_id),
            "project_id": str(bet.project_id),
            "bet": {
                "id": str(bet.id),
                "predicted_value": bet.predicted_value,
                "actual_value": actual_value if actual_value is not None else bet.actual_value,
                "actual_spent": actual_spent if actual_spent is not None else bet.actual_spent,
            },
            "trust_score": 0.0,
            "audit_log": [],
        }
        result: AgentState = await self.calibration_graph.ainvoke(state)
        await self._persist_calibration_result(bet=bet, result=result)
        if commit:
            await self.db.commit()
        return result

    async def _persist_analysis_result(self, *, session: Session, result: AgentState) -> None:
        intent_data = result.get("intent") or {}
        intent = Intent(
            session_id=session.id,
            title=intent_data.get("title") or "Новая продуктовая ставка",
            description=intent_data.get("description"),
            invest_money=intent_data.get("invest_money"),
            invest_effort=intent_data.get("invest_effort"),
            horizon_months=intent_data.get("horizon_months"),
            expected_result=intent_data.get("expected_result"),
            metrics=extract_json_object(intent_data.get("metrics") or {}),
        )
        self.db.add(intent)
        await self.db.flush()

        assumption_models: list[Assumption] = []
        for item in result.get("assumptions") or []:
            model = Assumption(
                intent_id=intent.id,
                statement=item.get("statement") or "Неназванное допущение",
                is_explicit=bool(item.get("is_explicit", False)),
                criticality=item.get("criticality") or 3,
            )
            self.db.add(model)
            assumption_models.append(model)
        await self.db.flush()

        scenario_models: list[EnvScenario] = []
        for item in result.get("env_scenarios") or []:
            model = EnvScenario(
                session_id=session.id,
                shock_class=item.get("shock_class") or "unknown",
                description=item.get("description") or "Сценарий среды",
                severity=item.get("severity"),
                likelihood=item.get("likelihood"),
                source_refs=extract_json_object(item.get("source_refs") or []),
            )
            self.db.add(model)
            scenario_models.append(model)
        await self.db.flush()

        for item in result.get("attacks") or []:
            assumption_id = self._by_index(assumption_models, item.get("assumption_index"))
            scenario_id = self._by_index(scenario_models, item.get("scenario_index"))
            self.db.add(
                Attack(
                    session_id=session.id,
                    assumption_id=assumption_id,
                    scenario_id=scenario_id,
                    narrative=item.get("narrative") or "Сценарий провала",
                    failure_point=item.get("failure_point"),
                    est_loss_money=item.get("est_loss_money"),
                    survivable=item.get("survivable"),
                )
            )

        decision = result.get("threshold_decision") or {}
        self.db.add(
            ThresholdDecision(
                session_id=session.id,
                reversibility=decision.get("reversibility") or "cheap_reversible",
                verdict=decision.get("verdict") or "probe",
                recommended_step=decision.get("recommended_step"),
                step_budget=decision.get("step_budget"),
                trust_level=decision.get("trust_level"),
                rationale=decision.get("rationale"),
            )
        )

        for log in result.get("audit_log") or []:
            self.db.add(
                SessionLog(
                    session_id=session.id,
                    actor=self._actor_or_none(log.get("actor")),
                    event_type=log.get("event_type") or "agent_event",
                    payload=extract_json_object(log.get("payload") or {}),
                )
            )

    async def _persist_calibration_result(self, *, bet: Bet, result: AgentState) -> None:
        record = result.get("calibration_record") or {}
        self.db.add(
            CalibrationRecord(
                bet_id=bet.id,
                project_id=bet.project_id,
                predicted_value=record.get("predicted_value"),
                actual_value=record.get("actual_value"),
                error_abs=record.get("error_abs"),
                error_rel=record.get("error_rel"),
                optimism_bias=record.get("optimism_bias"),
                trust_delta=record.get("trust_delta"),
            )
        )
        for log in result.get("audit_log") or []:
            self.db.add(
                SessionLog(
                    session_id=bet.session_id,
                    actor=self._actor_or_none(log.get("actor")),
                    event_type=log.get("event_type") or "agent_event",
                    payload=extract_json_object(log.get("payload") or {}),
                )
            )

    def _by_index(self, items: list[Any], index: Any) -> uuid.UUID | None:
        try:
            idx = int(index)
            return items[idx].id if 0 <= idx < len(items) else None
        except Exception:
            return None

    def _actor_or_none(self, value: Any) -> AgentKind | None:
        try:
            return AgentKind(value)
        except Exception:
            return None

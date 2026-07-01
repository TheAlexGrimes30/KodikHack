from pathlib import Path
from typing import Any

from pydantic import ValidationError

from backend.modules.agents.common.llm import LLMClient
from backend.modules.agents.common.prompt_utils import load_prompt
from backend.modules.agents.common.state import AgentState
from backend.modules.agents.common.utils import extract_json_object, add_audit_log, decimal_or_none
from backend.modules.agents.desctructor.schemas import DestructorOutput, AttackItem


class DestructorAgent:
    """Деструктор.

    Связь с БД:
    - attacks -> таблица attacks
    - assumption_index/scenario_index позже в service мапятся на реальные UUID
    """

    actor = "destructor"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()
        self.system_prompt = load_prompt(Path(__file__).with_name("prompts.md"))

    def run(self, state: AgentState) -> dict[str, Any]:
        fallback = self._fallback_output(state).model_dump(mode="json")
        fallback_text = str(fallback).replace("'", '"')
        user_prompt = f"""
        Intent:
        {state.get('intent', {})}
        
        Assumptions:
        {state.get('assumptions', [])}
        
        Environment scenarios:
        {state.get('env_scenarios', [])}
        """

        llm_text = self.llm.generate(self.system_prompt, user_prompt, fallback=fallback_text)
        parsed = extract_json_object(llm_text)
        output = self._fallback_output(state)
        if parsed:
            try:
                output = DestructorOutput.model_validate(parsed)
            except ValidationError:
                pass

        attacks = []
        for item in output.attacks:
            attacks.append(
                {
                    "assumption_index": item.assumption_index,
                    "scenario_index": item.scenario_index,
                    "narrative": item.narrative,
                    "failure_point": item.failure_point,
                    "est_loss_money": decimal_or_none(item.est_loss_money),
                    "survivable": item.survivable,
                }
            )

        return {
            "attacks": attacks,
            "audit_log": add_audit_log(
                state,
                actor=self.actor,
                event_type="attacks_generated",
                payload={"attacks_count": len(attacks)},
            ),
        }

    def _fallback_output(self, state: AgentState) -> DestructorOutput:
        invest_money = state.get("intent", {}).get("invest_money") or state.get("project_context", {}).get("invest_money") or 0
        return DestructorOutput(
            attacks=[
                AttackItem(
                    assumption_index=0,
                    scenario_index=0,
                    narrative="Команда делает полноценный продукт, но после запуска видит слабый спрос. Потрачены деньги и время, а ключевая гипотеза о боли не подтверждена.",
                    failure_point="Неподтверждённая сила боли и готовность платить.",
                    est_loss_money=decimal_or_none(invest_money),
                    survivable=False,
                ),
                AttackItem(
                    assumption_index=1,
                    scenario_index=2,
                    narrative="Первые пользователи приходят слишком дорого, поэтому даже при интересе unit-экономика не сходится.",
                    failure_point="Стоимость привлечения выше допустимой.",
                    est_loss_money=decimal_or_none(100000),
                    survivable=True,
                ),
            ]
        )

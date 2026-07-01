from pathlib import Path
from typing import Any

from pydantic import ValidationError

from backend.modules.agents.common.llm import LLMClient
from backend.modules.agents.common.prompt_utils import load_prompt
from backend.modules.agents.common.state import AgentState
from backend.modules.agents.common.utils import decimal_or_none, add_audit_log, clamp, extract_json_object
from backend.modules.agents.threshold.schemas import ThresholdDecisionOutput


class ThresholdAgent:
    """Агент Порог.

    Связь с БД:
    - threshold_decision -> таблица threshold_decisions

    Временная заглушка:
    - основная маршрутизация rule-based, как в исходном Kodik-прототипе.
    - LLM генерирует/уточняет rationale и recommended_step.
    """

    actor = "threshold"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()
        self.system_prompt = load_prompt(Path(__file__).with_name("prompts.md"))

    def run(self, state: AgentState) -> dict[str, Any]:
        fallback_output = self._rule_based_decision(state)
        fallback_text = str(fallback_output.model_dump(mode="json")).replace("'", '"')
        user_prompt = f"""
        Intent:
        {state.get('intent', {})}
        
        Assumptions:
        {state.get('assumptions', [])}
        
        Environment scenarios:
        {state.get('env_scenarios', [])}
        
        Attacks:
        {state.get('attacks', [])}
        
        Trust score:
        {state.get('trust_score', 0.0)}
        
        Iteration:
        {state.get('iteration', 0)}
        """
        llm_text = self.llm.generate(self.system_prompt, user_prompt, fallback=fallback_text)
        parsed = extract_json_object(llm_text)
        output = fallback_output
        if parsed:
            try:
                output = ThresholdDecisionOutput.model_validate(parsed)
            except ValidationError:
                pass

        trust_level = clamp(float(output.trust_level or fallback_output.trust_level or 0.0))
        decision = {
            "reversibility": output.reversibility,
            "verdict": output.verdict,
            "recommended_step": output.recommended_step,
            "step_budget": decimal_or_none(output.step_budget),
            "trust_level": decimal_or_none(trust_level),
            "rationale": output.rationale,
        }

        return {
            "threshold_decision": decision,
            "final_decision": output.verdict,
            "audit_log": add_audit_log(
                state,
                actor=self.actor,
                event_type="threshold_decision_created",
                payload=decision,
            ),
        }

    def _rule_based_decision(self, state: AgentState) -> ThresholdDecisionOutput:
        trust = float(state.get("trust_score") or 0.0)
        iteration = int(state.get("iteration") or 0)
        attacks = state.get("attacks") or []
        intent = state.get("intent") or {}
        invest_money = float(intent.get("invest_money") or 0)

        has_unsurvivable_attack = any(a.get("survivable") is False for a in attacks)
        max_loss = max([float(a.get("est_loss_money") or 0) for a in attacks] or [0])

        if trust >= 0.75 and not has_unsurvivable_attack:
            verdict = "scale"
            step_budget = max(invest_money * 0.5, 100000) if invest_money else 200000
            rationale = "Доверие достаточно высокое, критичных непереживаемых атак не найдено. Можно масштабировать осторожно."
        elif has_unsurvivable_attack and iteration >= 2:
            verdict = "exit"
            step_budget = 0
            rationale = "Повторные проверки показывают непереживаемые риски. Лучше выйти из ставки."
        elif iteration == 0 or trust < 0.5:
            verdict = "probe"
            step_budget = min(max(invest_money * 0.1, 30000), 150000) if invest_money else 50000
            rationale = "Данных мало или доверие низкое. Нужен дешёвый обратимый эксперимент."
        else:
            verdict = "hold"
            step_budget = min(max(invest_money * 0.15, 50000), 250000) if invest_money else 75000
            rationale = "Идея не убита, но уверенности недостаточно для масштабирования. Нужно держать размер ставки."

        reversibility = "costly_irreversible" if max_loss >= max(invest_money * 0.7, 300000) else "cheap_reversible"
        return ThresholdDecisionOutput(
            reversibility=reversibility,
            verdict=verdict,
            recommended_step="Провести интервью/лендинг/ручной MVP до полноценной разработки.",
            step_budget=decimal_or_none(step_budget),
            trust_level=decimal_or_none(trust),
            rationale=rationale,
        )

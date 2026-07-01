from pathlib import Path
from typing import Any

from backend.modules.agents.common.llm import LLMClient
from backend.modules.agents.common.prompt_utils import load_prompt
from backend.modules.agents.common.state import AgentState
from backend.modules.agents.intention.schemas import AssumptionItem, IntentOutput


class IntentionAgent:
    """Агент Намерения.

    Связь с БД:
    - intent -> таблица intents
    - assumptions -> таблица assumptions
    """

    actor = "intention"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()
        self.system_prompt = load_prompt(Path(__file__).with_name("prompts.md"))

    def run(self, state: AgentState) -> dict[str, Any]:
        raw_intent = state.get("raw_intent", "")
        project_context = state.get("project_context", {})

    def _fallback_output(self, raw_intent: str, project_context: dict[str, Any]) -> IntentOutput:
        return IntentOutput(
            title=project_context.get("title") or "Новая продуктовая ставка",
            description=raw_intent or "Пользователь хочет проверить продуктовую идею.",
            invest_money=decimal_or_none(project_context.get("invest_money")),
            invest_effort=decimal_or_none(project_context.get("invest_effort")),
            horizon_months=decimal_or_none(project_context.get("horizon_months")),
            expected_result=project_context.get("expected_result") or "Проверить спрос и снизить неопределённость",
            metrics={
                "target_signal": project_context.get("target_signal", "первые платежи / заявки / интервью"),
                "risk_appetite": project_context.get("risk_appetite", "balanced"),
            },
            assumptions=[
                AssumptionItem(
                    statement="У целевой аудитории действительно есть боль, которую продукт решает.",
                    is_explicit=False,
                    criticality=5,
                ),
                AssumptionItem(
                    statement="Пользователи готовы заплатить или оставить сильный сигнал интереса.",
                    is_explicit=False,
                    criticality=5,
                ),
                AssumptionItem(
                    statement="Команда сможет проверить гипотезу в заданный горизонт без полного запуска.",
                    is_explicit=False,
                    criticality=4,
                ),
            ],
        )

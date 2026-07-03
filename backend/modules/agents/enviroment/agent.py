from pathlib import Path
from typing import Any

from pydantic import ValidationError

from backend.modules.agents.common.llm import LLMClient
from backend.modules.agents.common.prompt_utils import load_prompt
from backend.modules.agents.common.state import AgentState
from backend.modules.agents.common.utils import add_audit_log, extract_json_object
from backend.modules.agents.enviroment.retriever import DefaultEnvironmentRetriever, EnvironmentRetriever
from backend.modules.agents.enviroment.schemas import EnvScenarioItem, EnvironmentOutput


class EnvironmentAgent:
    """
    Агент Среды.

    Сейчас использует StubEnvironmentRetriever.
    Потом можно заменить на QdrantEnvironmentRetriever.

    Связь с БД:
    - scenarios -> таблица env_scenarios
    """

    actor = "environment"

    def __init__(
        self,
        llm: LLMClient | None = None,
        retriever: EnvironmentRetriever | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.retriever = retriever or DefaultEnvironmentRetriever()
        self.system_prompt = load_prompt(Path(__file__).with_name("prompts.md"))

    async def run(self, state: AgentState) -> dict[str, Any]:
        intent = state.get("intent", {})
        assumptions = state.get("assumptions", [])
        project_context = state.get("project_context", {})

        query = self._build_query(intent, assumptions, project_context)

        sources = await self.retriever.retrieve(
            query=query,
            project_context=project_context,
            assumptions=assumptions,
            limit=5,
        )

        fallback_output = self._fallback_output(sources)
        fallback_text = fallback_output.model_dump_json()

        user_prompt = f"""
        Намерение:
        {intent}
        
        Допущения:
        {assumptions}
        
        Контекст проекта:
        {project_context}
        
        Найденные источники среды:
        {[source.model_dump(mode="json") for source in sources]}
        
        Верни строго JSON формата:
        {{
          "scenarios": [
            {{
              "shock_class": "string",
              "description": "string",
              "severity": 1-5,
              "likelihood": 0-1,
              "source_refs": []
            }}
          ]
        }}
        """

        llm_text = self.llm.generate(
            self.system_prompt,
            user_prompt,
            fallback=fallback_text,
        )

        parsed = extract_json_object(llm_text)
        output = fallback_output

        if parsed:
            try:
                output = EnvironmentOutput.model_validate(parsed)
            except ValidationError:
                pass

        env_scenarios = [
            item.model_dump(mode="json")
            for item in output.scenarios
        ]

        return {
            "env_scenarios": env_scenarios,
            "environment_sources": [
                source.model_dump(mode="json")
                for source in sources
            ],
            "audit_log": add_audit_log(
                state,
                actor=self.actor,
                event_type="environment_scenarios_generated",
                payload={
                    "scenarios_count": len(env_scenarios),
                    "sources_count": len(sources),
                },
            ),
        }

    def _build_query(
        self,
        intent: dict[str, Any],
        assumptions: list[dict[str, Any]],
        project_context: dict[str, Any],
    ) -> str:
        assumption_text = "; ".join(
            item.get("statement", "")
            for item in assumptions
        )

        return (
            f"{intent.get('title', '')}. "
            f"{intent.get('description', '')}. "
            f"География: {project_context.get('geography', 'РФ')}. "
            f"Стадия: {project_context.get('stage', 'idea')}. "
            f"Допущения: {assumption_text}"
        )

    def _fallback_output(
        self,
        sources: list,
    ) -> EnvironmentOutput:
        return EnvironmentOutput(
            scenarios=[
                EnvScenarioItem(
                    shock_class="weak_demand",
                    description=(
                        "Спрос может оказаться слабее ожидаемого: "
                        "пользователи проявляют интерес, но не дают "
                        "денежный или поведенческий сигнал."
                    ),
                    severity=5,
                    likelihood=0.65,
                    source_refs=[
                        source.model_dump(mode="json")
                        for source in sources
                        if source.metadata.get("risk_type") == "weak_demand"
                    ],
                ),
                EnvScenarioItem(
                    shock_class="cac_growth",
                    description=(
                        "Стоимость привлечения может вырасти, "
                        "из-за чего проверка гипотезы станет дороже, "
                        "а экономика MVP ухудшится."
                    ),
                    severity=4,
                    likelihood=0.55,
                    source_refs=[
                        source.model_dump(mode="json")
                        for source in sources
                        if source.metadata.get("risk_type") == "cac_growth"
                    ],
                ),
                EnvScenarioItem(
                    shock_class="runway_pressure",
                    description=(
                        "Команда может не успеть проверить гипотезу "
                        "до исчерпания бюджета или доступного времени."
                    ),
                    severity=4,
                    likelihood=0.5,
                    source_refs=[
                        source.model_dump(mode="json")
                        for source in sources
                        if source.metadata.get("risk_type") == "runway"
                    ],
                ),
            ]
        )
    

from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    """Общее состояние LangGraph.

    Все агенты читают и обновляют один общий state. Это ближе всего к текущему
    прототипу Kodik: LLM генерирует содержимое узлов, а маршрутизация остаётся
    в Python/LangGraph.
    """

    user_id: str
    project_id: str
    session_id: str

    raw_intent: str
    project_context: dict[str, Any]

    # Данные под таблицы intents / assumptions
    intent: dict[str, Any]
    assumptions: list[dict[str, Any]]

    # Данные под таблицы env_scenarios / attacks
    environment_sources: list[dict[str, Any]]
    env_scenarios: list[dict[str, Any]]
    attacks: list[dict[str, Any]]

    # Данные под threshold_decisions
    threshold_decision: dict[str, Any]

    # Данные под bets / calibration_records
    bet: dict[str, Any]
    calibration_record: dict[str, Any]

    # Управляющие поля
    trust_score: float
    iteration: int
    final_decision: str
    audit_log: list[dict[str, Any]]

import asyncio
import json

from backend.modules.agents.graph import build_calibration_graph, build_analysis_graph


async def run_analysis_demo() -> dict:
    graph = build_analysis_graph()

    initial_state = {
        "user_id": "demo-user",
        "project_id": "demo-project",
        "session_id": "demo-session",
        "raw_intent": (
            "Хочу запустить B2B SaaS для автоматизации проверки договоров. "
            "Есть бюджет 500000 рублей и 3 месяца. "
            "Хочу проверить, готовы ли малые компании платить за такой сервис."
        ),
        "project_context": {
            "title": "B2B SaaS для проверки договоров",
            "invest_money": 500000,
            "horizon_months": 3,
            "risk_appetite": "balanced",
            "geography": "РФ",
            "stage": "idea",
            "target_signal": "10 платных заявок или 30 интервью",
        },
        "trust_score": 0.5,
        "iteration": 1,
        "audit_log": [],
    }

    result = await graph.ainvoke(initial_state)

    print("\n=== ANALYSIS RESULT ===")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    return result


async def run_calibration_demo(analysis_result: dict) -> dict:
    graph = build_calibration_graph()

    state = {
        **analysis_result,
        "bet": {
            "description": "Запустить лендинг и собрать платные заявки",
            "predicted_metric": "paid_leads",
            "predicted_value": 10,
            "actual_value": 7,
            "actual_spent": 35000,
        },
    }

    result = await graph.ainvoke(state)

    print("\n=== CALIBRATION RESULT ===")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    return result


async def main() -> None:
    analysis_result = await run_analysis_demo()
    await run_calibration_demo(analysis_result)


if __name__ == "__main__":
    asyncio.run(main())
from typing import Any, Callable, Awaitable, cast

from langgraph.constants import END, START
from langgraph.graph import StateGraph

from backend.modules.agents.calibration.agent import CalibrationAgent
from backend.modules.agents.common.llm import LLMClient
from backend.modules.agents.common.state import AgentState
from backend.modules.agents.desctructor.agent import DestructorAgent
from backend.modules.agents.enviroment.agent import EnvironmentAgent
from backend.modules.agents.intention.agent import IntentionAgent
from backend.modules.agents.threshold.agent import ThresholdAgent


SyncNode = Callable[[AgentState], dict[str, Any]]
AsyncNode = Callable[[AgentState], Awaitable[dict[str, Any]]]

class AgentGraphBuilder:
    def __init__(self, llm: LLMClient | None = None) -> None:
        shared_llm = llm or LLMClient()

        self.intention = IntentionAgent(shared_llm)
        self.environment = EnvironmentAgent(shared_llm)
        self.destructor = DestructorAgent(shared_llm)
        self.threshold = ThresholdAgent(shared_llm)
        self.calibration = CalibrationAgent()

    def build_analysis_graph(self):
        graph = StateGraph(AgentState)

        graph.add_node("intention", cast(SyncNode, self._intention_node))
        graph.add_node("supervisor", cast(SyncNode, self._supervisor_node))
        graph.add_node("environment", cast(AsyncNode, self._environment_node))
        graph.add_node("destructor", cast(SyncNode, self._destructor_node))
        graph.add_node("threshold", cast(SyncNode, self._threshold_node))

        graph.add_edge(START, "intention")
        graph.add_edge("intention", "supervisor")

        graph.add_conditional_edges(
            "supervisor",
            self._route_from_supervisor,
            {
                "environment": "environment",
                "destructor": "destructor",
                "threshold": "threshold",
                "end": END,
            },
        )

        graph.add_edge("environment", "supervisor")
        graph.add_edge("destructor", "supervisor")
        graph.add_edge("threshold", "supervisor")

        return graph.compile()

    def build_calibration_graph(self):
        graph = StateGraph(AgentState)

        graph.add_node("calibration", cast(SyncNode, self._calibration_node))
        graph.add_edge(START, "calibration")
        graph.add_edge("calibration", END)

        return graph.compile()

    def _intention_node(self, state: AgentState) -> dict[str, Any]:
        return self.intention.run(state)

    async def _environment_node(self, state: AgentState) -> dict[str, Any]:
        return await self.environment.run(state)

    def _destructor_node(self, state: AgentState) -> dict[str, Any]:
        return self.destructor.run(state)

    def _threshold_node(self, state: AgentState) -> dict[str, Any]:
        return self.threshold.run(state)

    def _calibration_node(self, state: AgentState) -> dict[str, Any]:
        return self.calibration.run(state)

    def _supervisor_node(self, state: AgentState) -> dict[str, Any]:
        if not state.get("env_scenarios"):
            next_agent = "environment"
        elif not state.get("attacks"):
            next_agent = "destructor"
        elif not state.get("threshold_decision"):
            next_agent = "threshold"
        else:
            next_agent = "end"

        return {"next_agent": next_agent}

    def _route_from_supervisor(self, state: AgentState) -> str:
        return state.get("next_agent", "end")


def build_analysis_graph():
    return AgentGraphBuilder().build_analysis_graph()


def build_calibration_graph():
    return AgentGraphBuilder().build_calibration_graph()

from backend.modules.agents.calibration.agent import CalibrationAgent
from backend.modules.agents.common.llm import LLMClient
from backend.modules.agents.desctructor.agent import DestructorAgent
from backend.modules.agents.enviroment.agent import EnvironmentAgent
from backend.modules.agents.intention.agent import IntentionAgent


class AgentGraphBuilder:
    """
    Иерархическая мультиагентная система.

    Supervisor управляет маршрутом:
    intention -> supervisor
    supervisor -> environment
    supervisor -> destructor
    supervisor -> threshold
    supervisor -> END
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        shared_llm = llm or LLMClient()

        self.intention = IntentionAgent(shared_llm)
        self.environment = EnvironmentAgent(shared_llm)
        self.destructor = DestructorAgent(shared_llm)
        self.threshold = ThresholdAgent(shared_llm)
        self.calibration = CalibrationAgent()

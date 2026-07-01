from pathlib import Path

from backend.modules.agents.common.llm import LLMClient
from backend.modules.agents.common.prompt_utils import load_prompt


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


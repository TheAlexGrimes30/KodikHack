from abc import abstractmethod, ABC

from backend.modules.agents.enviroment.schemas import EnvironmentSource
from backend.modules.rag.retriever import HybridEnvironmentRetriever


class EnvironmentRetriever(ABC):
    @abstractmethod
    async def retrieve(
        self,
        *,
        query: str,
        project_context: dict,
        assumptions: list[dict],
        limit: int = 5,
    ) -> list[EnvironmentSource]:
        pass


class StubEnvironmentRetriever(EnvironmentRetriever):
    async def retrieve(
        self,
        *,
        query: str,
        project_context: dict,
        assumptions: list[dict],
        limit: int = 5,
    ) -> list[EnvironmentSource]:
        return [
            EnvironmentSource(
                title="Рост стоимости привлечения",
                source_type="stub",
                content=(
                    "Для IT-продуктов часто критичен рост CAC: "
                    "каналы рекламы дорожают, конверсия падает, "
                    "а юнит-экономика ломается."
                ),
                metadata={"risk_type": "cac_growth"},
            ),
            EnvironmentSource(
                title="Недостаточный спрос",
                source_type="stub",
                content=(
                    "Одна из частых причин провала продукта — "
                    "пользователи подтверждают интерес словами, "
                    "но не совершают оплату."
                ),
                metadata={"risk_type": "weak_demand"},
            ),
            EnvironmentSource(
                title="Сжатый runway",
                source_type="stub",
                content=(
                    "Если runway проекта мал, команда не успевает "
                    "провести несколько итераций проверки гипотез."
                ),
                metadata={"risk_type": "runway"},
            ),
        ][:limit]


class DefaultEnvironmentRetriever(EnvironmentRetriever):
    def __init__(self) -> None:
        self.hybrid = HybridEnvironmentRetriever()
        self.stub = StubEnvironmentRetriever()

    async def retrieve(
        self,
        *,
        query: str,
        project_context: dict,
        assumptions: list[dict],
        limit: int = 5,
    ) -> list[EnvironmentSource]:
        sources = await self.hybrid.retrieve(
            query=query,
            project_context=project_context,
            assumptions=assumptions,
            limit=limit,
        )
        if sources:
            return sources
        return await self.stub.retrieve(
            query=query,
            project_context=project_context,
            assumptions=assumptions,
            limit=limit,
        )

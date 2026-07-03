from backend.modules.rag.schemas import RetrievedChunk


class HeuristicReranker:
    def rerank(self, query: str, items: list[RetrievedChunk], limit: int) -> list[RetrievedChunk]:
        query_terms = {term.lower() for term in query.split() if len(term) > 2}
        scored: list[tuple[float, RetrievedChunk]] = []

        for item in items:
            overlap = sum(1 for term in query_terms if term in item.text.lower())
            trust = float(item.trust_score or 0.0)
            total = float(item.score) + (overlap * 0.02) + (trust * 0.05)
            scored.append((total, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

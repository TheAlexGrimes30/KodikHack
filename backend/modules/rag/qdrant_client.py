import json
from typing import Any
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from backend.app.config import settings
from backend.modules.rag.schemas import RetrievedChunk


class QdrantClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        collection_name: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.QDRANT_URL).rstrip("/")
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.timeout = timeout or settings.QDRANT_TIMEOUT

    def upsert_points(self, points: list[dict[str, Any]]) -> bool:
        if not points:
            return True
        payload = {"points": points}
        return self._post(
            f"/collections/{self.collection_name}/points",
            payload,
        ) is not None

    def ensure_collection(self, *, vector_size: int) -> bool:
        payload = {
            "vectors": {
                "dense": {
                    "size": vector_size,
                    "distance": "Cosine",
                }
            }
        }
        return self._request(
            method="PUT",
            path=f"/collections/{self.collection_name}",
            payload=payload,
        ) is not None

    def query_dense(
        self,
        *,
        dense_vector: list[float],
        limit: int,
        query_filter: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        if not dense_vector:
            return []

        payload: dict[str, Any] = {
            "query": dense_vector,
            "using": "dense",
            "limit": limit,
            "with_payload": True,
        }
        if query_filter:
            payload["filter"] = query_filter

        data = self._post(f"/collections/{self.collection_name}/points/query", payload)
        points = self._extract_points(data)
        return [self._to_chunk(point) for point in points]

    def query_hybrid(
        self,
        *,
        dense_vector: list[float],
        sparse_vector: dict[str, Any] | None,
        limit: int,
        prefetch_limit: int,
        query_filter: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        if not dense_vector:
            return []

        prefetch = [
            {
                "query": dense_vector,
                "using": "dense",
                "limit": prefetch_limit,
            }
        ]
        if sparse_vector:
            prefetch.append(
                {
                    "query": sparse_vector,
                    "using": "sparse",
                    "limit": prefetch_limit,
                }
            )

        payload: dict[str, Any] = {
            "prefetch": prefetch,
            "query": {"rrf": {}},
            "limit": limit,
            "with_payload": True,
        }
        if query_filter:
            payload["filter"] = query_filter

        data = self._post(f"/collections/{self.collection_name}/points/query", payload)
        points = self._extract_points(data)
        return [self._to_chunk(point) for point in points]

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        return self._request(method="POST", path=path, payload=payload)

    def _request(self, *, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        req = urllib_request.Request(
            url=f"{self.base_url}{path}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib_request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return None
        except Exception:
            return None

    def _extract_points(self, data: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not data:
            return []
        result = data.get("result")
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            points = result.get("points")
            if isinstance(points, list):
                return points
        return []

    def _to_chunk(self, point: dict[str, Any]) -> RetrievedChunk:
        payload = point.get("payload") or {}
        return RetrievedChunk(
            point_id=str(point.get("id")),
            score=float(point.get("score") or 0.0),
            text=str(payload.get("text") or payload.get("content") or ""),
            source_key=payload.get("source_key"),
            title=payload.get("title"),
            url=payload.get("url"),
            published_at=payload.get("published_at"),
            source_type=payload.get("source_type"),
            risk_type=payload.get("risk_type"),
            vertical_key=payload.get("vertical_key"),
            trust_score=payload.get("trust_score"),
            payload=payload,
        )

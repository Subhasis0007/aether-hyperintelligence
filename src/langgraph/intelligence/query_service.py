from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol


@dataclass(slots=True)
class QueryRequest:
    question: str
    systems: list[str] = field(default_factory=list)
    explain: bool = False
    tenant: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SourceCitation:
    system: str
    reference: str
    score: float = 1.0


@dataclass(slots=True)
class QueryResult:
    answer: str
    citations: list[SourceCitation] = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Connector(Protocol):
    async def search(self, request: QueryRequest) -> list[dict[str, Any]]:
        ...


class QueryService:
    """
    Lightweight intelligence query service.

    This service is intentionally framework-light so it can later be wired to:
    - Aether.API endpoints
    - Python SDK intelligence.query(...)
    - LangGraph orchestration
    - connector adapters for Salesforce / Stripe / ServiceNow / Dynamics / SAP
    """

    def __init__(self, connectors: dict[str, Connector] | None = None) -> None:
        self._connectors = connectors or {}

    def register_connector(self, name: str, connector: Connector) -> None:
        self._connectors[name] = connector

    async def query(self, request: QueryRequest) -> QueryResult:
        selected_systems = request.systems or list(self._connectors.keys())

        collected: list[dict[str, Any]] = []
        citations: list[SourceCitation] = []

        for system in selected_systems:
            connector = self._connectors.get(system)
            if connector is None:
                continue

            rows = await connector.search(request)
            collected.extend(rows)

            for row in rows:
                citations.append(
                    SourceCitation(
                        system=system,
                        reference=str(row.get("id", row.get("reference", "unknown"))),
                        score=float(row.get("score", 1.0)),
                    )
                )

        answer = self._synthesize_answer(request.question, collected)
        reasoning = self._build_reasoning(request, collected) if request.explain else []

        return QueryResult(
            answer=answer,
            citations=citations,
            reasoning=reasoning,
            metadata={
                "tenant": request.tenant,
                "systems_consulted": selected_systems,
                "result_count": len(collected),
            },
        )

    def _synthesize_answer(self, question: str, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return f"No results found for question: {question}"

        summary_parts: list[str] = []
        for row in rows[:5]:
            label = row.get("label") or row.get("name") or row.get("title") or "item"
            value = row.get("value") or row.get("status") or row.get("summary") or "available"
            summary_parts.append(f"{label}: {value}")

        return " | ".join(summary_parts)

    def _build_reasoning(self, request: QueryRequest, rows: list[dict[str, Any]]) -> list[str]:
        steps: list[str] = []
        steps.append(f"Question received: {request.question}")
        steps.append(f"Systems selected: {', '.join(request.systems) if request.systems else 'all registered connectors'}")
        steps.append(f"Rows collected: {len(rows)}")

        if rows:
            top = rows[0]
            steps.append(
                "Top result fields inspected: "
                + ", ".join(sorted(str(k) for k in top.keys())[:10])
            )

        return steps


class InMemoryConnector:
    """
    Simple in-memory connector for local development and tests.
    """

    def __init__(self, system_name: str, rows: Iterable[dict[str, Any]]) -> None:
        self.system_name = system_name
        self._rows = list(rows)

    async def search(self, request: QueryRequest) -> list[dict[str, Any]]:
        question = request.question.lower()
        results: list[dict[str, Any]] = []

        for row in self._rows:
            haystack = " ".join(str(v).lower() for v in row.values())
            if any(token in haystack for token in question.split()):
                results.append(row)

        if not results:
            return self._rows[:3]

        return results
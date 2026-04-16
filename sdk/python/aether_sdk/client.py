from __future__ import annotations

from typing import Any, AsyncIterator, Optional


class IntelligenceClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def query(
        self,
        question: str,
        *,
        systems: Optional[list[str]] = None,
        explain: bool = False,
    ) -> dict[str, Any]:
        raise NotImplementedError("Wire IntelligenceClient.query to the AETHER API")


class IncidentCommandClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def invoke(
        self,
        *,
        incident_id: str,
        auto_deploy: bool = False,
    ) -> dict[str, Any]:
        raise NotImplementedError("Wire IncidentCommandClient.invoke to the AETHER API")


class TeamsClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root
        self.incident_command = IncidentCommandClient(root)


class ConnectorsClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root


class UseCasesClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def ma_due_diligence(
        self,
        *,
        documents: list[Any],
        target_systems: list[str],
        output_format: str = "executive_brief",
    ) -> dict[str, Any]:
        raise NotImplementedError("Wire UseCasesClient.ma_due_diligence to the AETHER API")


class MarketplaceClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def publish(
        self,
        *,
        wasm_path: str,
        manifest: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError("Wire MarketplaceClient.publish to the AETHER API")


class EventStreamClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def stream(self, *, topics: list[str]) -> AsyncIterator[dict[str, Any]]:
        if False:
            yield {}
        raise NotImplementedError("Wire EventStreamClient.stream to the AETHER SSE endpoint")


class AetherClient:
    """
    Official AETHER Python SDK — async-first, fully typed.

    Quick start:
        from aether_sdk import AetherClient

        async with AetherClient(api_key="aeth_live_xxx", tenant="acme") as client:

            result = await client.intelligence.query(
                "Which of our top 20 customers are at churn risk this quarter?",
                systems=["Salesforce", "Stripe", "ServiceNow", "Dynamics"],
                explain=True,
            )

            incident = await client.teams.incident_command.invoke(
                incident_id="INC0123456",
                auto_deploy=True,
            )

            dd = await client.use_cases.ma_due_diligence(
                documents=["doc1.pdf", "doc2.pdf"],
                target_systems=["SAP", "Dynamics", "Workday"],
                output_format="executive_brief",
            )

            async for event in client.events.stream(topics=["incident", "anomaly"]):
                print(event)
    """

    def __init__(
        self,
        api_key: str,
        tenant: str,
        base_url: str = "https://api.aether.subhasisnanda.com",
    ) -> None:
        self.api_key = api_key
        self.tenant = tenant
        self.base_url = base_url

        self.intelligence = IntelligenceClient(self)
        self.teams = TeamsClient(self)
        self.connectors = ConnectorsClient(self)
        self.use_cases = UseCasesClient(self)
        self.marketplace = MarketplaceClient(self)
        self.events = EventStreamClient(self)

    async def __aenter__(self) -> "AetherClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None
from __future__ import annotations

import json
from typing import Any, AsyncIterator, Optional

import httpx

from .models import AgentManifest, AgentEvent


class IntelligenceClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def query(
        self,
        question: str,
        *,
        systems: Optional[list[str]] = None,
        explain: bool = False,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        payload = {
            "question": question,
            "systems": systems or [],
            "explain": explain,
            "tenant": self._root.tenant,
            "metadata": metadata or {},
        }
        response = await self._root._request(
            "POST",
            "/v1/intelligence/query",
            json=payload,
        )
        return response.json()


class IncidentCommandClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def invoke(
        self,
        *,
        incident_id: str,
        auto_deploy: bool = False,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        payload = {
            "incidentId": incident_id,
            "autoDeploy": auto_deploy,
            "tenant": self._root.tenant,
            "metadata": metadata or {},
        }
        response = await self._root._request(
            "POST",
            "/v1/teams/incident-command/invoke",
            json=payload,
        )
        return response.json()


class TeamsClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root
        self.incident_command = IncidentCommandClient(root)


class SapConnectorClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def create_maintenance_order(
        self,
        *,
        equipment_id: Optional[str],
        plant: str,
        order_type: str,
        priority: str,
        short_text: str,
        long_text: str,
        work_centre: str,
    ) -> dict[str, Any]:
        payload = {
            "equipmentId": equipment_id,
            "plant": plant,
            "orderType": order_type,
            "priority": priority,
            "shortText": short_text,
            "longText": long_text,
            "workCentre": work_centre,
        }
        response = await self._root._request(
            "POST",
            "/v1/connectors/sap/maintenance-orders",
            json=payload,
        )
        return response.json()


class ConnectorsClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root
        self.sap = SapConnectorClient(root)


class UseCasesClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def ma_due_diligence(
        self,
        *,
        documents: list[str],
        target_systems: list[str],
        output_format: str = "executive_brief",
    ) -> dict[str, Any]:
        payload = {
            "documents": documents,
            "targetSystems": target_systems,
            "outputFormat": output_format,
        }
        response = await self._root._request(
            "POST",
            "/v1/use-cases/ma-due-diligence",
            json=payload,
        )
        return response.json()


class MarketplaceClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def publish(
        self,
        *,
        wasm_path: str,
        manifest: AgentManifest,
    ) -> dict[str, Any]:
        with open(wasm_path, "rb") as wasm_file:
            files = {
                "wasm": (
                    wasm_path.split("/")[-1],
                    wasm_file,
                    "application/wasm",
                ),
                "manifest": (
                    "manifest.json",
                    json.dumps(manifest.__dict__),
                    "application/json",
                ),
            }
            response = await self._root._request(
                "POST",
                "/v1/marketplace/publish",
                files=files,
            )
            return response.json()


class EventStreamClient:
    def __init__(self, root: "AetherClient") -> None:
        self._root = root

    async def stream(self, *, topics: list[str]) -> AsyncIterator[AgentEvent]:
        params = {"topics": ",".join(topics)}
        headers = self._root._headers()

        async with self._root._client.stream(
            "GET",
            f"{self._root.base_url}/v1/events/stream",
            params=params,
            headers=headers,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line:
                    continue

                if line.startswith("data:"):
                    raw_json = line[len("data:"):].strip()

                    try:
                        payload = json.loads(raw_json)
                    except json.JSONDecodeError:
                        continue

                    yield AgentEvent(
                        agent=payload.get("agent", ""),
                        action=payload.get("action", ""),
                        outcome=payload.get("outcome", ""),
                        topic=payload.get("topic"),
                        raw=payload,
                    )


class AetherClient:
    def __init__(
        self,
        api_key: str,
        tenant: str,
        base_url: str = "https://api.aether.subhasisnanda.com",
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.tenant = tenant
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self._client = httpx.AsyncClient(timeout=self.timeout)

        self.intelligence = IntelligenceClient(self)
        self.teams = TeamsClient(self)
        self.connectors = ConnectorsClient(self)
        self.use_cases = UseCasesClient(self)
        self.marketplace = MarketplaceClient(self)
        self.events = EventStreamClient(self)

    async def __aenter__(self) -> "AetherClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Aether-Tenant": self.tenant,
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[dict[str, Any]] = None,
        files: Optional[dict[str, Any]] = None,
    ) -> httpx.Response:
        response = await self._client.request(
            method=method,
            url=f"{self.base_url}{path}",
            headers=self._headers(),
            json=json,
            files=files,
        )
        response.raise_for_status()
        return response
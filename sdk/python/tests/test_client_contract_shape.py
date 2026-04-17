from __future__ import annotations

import pathlib
import sys
import unittest
from typing import Any


# Ensure sdk/python is importable when this test is run from repo root
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class TestAetherClientContractShape(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        from aether_sdk import AetherClient

        self.client = AetherClient(
            api_key="aeth_test_key",
            tenant="acme",
            base_url="https://api.example.com",
        )
        self.captured: list[dict[str, Any]] = []

        async def fake_request(method: str, path: str, *, json=None, files=None):
            self.captured.append(
                {
                    "method": method,
                    "path": path,
                    "json": json,
                    "files": files,
                }
            )
            return _FakeResponse({"ok": True, "path": path, "json": json})

        self.client._request = fake_request  # type: ignore[method-assign]

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_intelligence_query_payload_shape(self) -> None:
        result = await self.client.intelligence.query(
            "Which customers are at churn risk?",
            systems=["Salesforce", "Stripe"],
            explain=True,
            metadata={"traceId": "abc-123"},
        )

        self.assertTrue(result["ok"])
        call = self.captured[-1]

        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["path"], "/v1/intelligence/query")
        self.assertEqual(
            call["json"],
            {
                "question": "Which customers are at churn risk?",
                "systems": ["Salesforce", "Stripe"],
                "explain": True,
                "tenant": "acme",
                "metadata": {"traceId": "abc-123"},
            },
        )

    async def test_incident_command_payload_shape(self) -> None:
        result = await self.client.teams.incident_command.invoke(
            incident_id="INC0123456",
            auto_deploy=True,
            metadata={"source": "sdk-test"},
        )

        self.assertTrue(result["ok"])
        call = self.captured[-1]

        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["path"], "/v1/teams/incident-command/invoke")
        self.assertEqual(
            call["json"],
            {
                "incidentId": "INC0123456",
                "autoDeploy": True,
                "tenant": "acme",
                "metadata": {"source": "sdk-test"},
            },
        )

    async def test_sap_maintenance_order_payload_shape(self) -> None:
        result = await self.client.connectors.sap.create_maintenance_order(
            equipment_id="MIXER-17",
            plant="1000",
            order_type="PM01",
            priority="1",
            short_text="Bearing anomaly detected",
            long_text="Vibration and temperature exceeded threshold.",
            work_centre="MAINT",
        )

        self.assertTrue(result["ok"])
        call = self.captured[-1]

        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["path"], "/v1/connectors/sap/maintenance-orders")
        self.assertEqual(
            call["json"],
            {
                "equipmentId": "MIXER-17",
                "plant": "1000",
                "orderType": "PM01",
                "priority": "1",
                "shortText": "Bearing anomaly detected",
                "longText": "Vibration and temperature exceeded threshold.",
                "workCentre": "MAINT",
            },
        )


if __name__ == "__main__":
    unittest.main()
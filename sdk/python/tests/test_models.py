from __future__ import annotations

import pathlib
import sys
import unittest


# Ensure sdk/python is importable when this test is run from repo root
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestAetherSdkModels(unittest.TestCase):
    def test_agent_manifest_fields(self) -> None:
        from aether_sdk import AgentManifest

        manifest = AgentManifest(
            name="invoice-validator",
            version="1.0.0",
            description="Validates SAP invoices against Stripe payments",
            capabilities=["sap.read", "stripe.read"],
            max_memory_mb=16,
            max_duration_ms=500,
            author_pq_key="dilithium-public-key",
        )

        self.assertEqual(manifest.name, "invoice-validator")
        self.assertEqual(manifest.version, "1.0.0")
        self.assertEqual(
            manifest.description,
            "Validates SAP invoices against Stripe payments",
        )
        self.assertEqual(manifest.capabilities, ["sap.read", "stripe.read"])
        self.assertEqual(manifest.max_memory_mb, 16)
        self.assertEqual(manifest.max_duration_ms, 500)
        self.assertEqual(manifest.author_pq_key, "dilithium-public-key")

    def test_agent_event_fields(self) -> None:
        from aether_sdk import AgentEvent

        event = AgentEvent(
            agent="incident-commander",
            action="diagnose",
            outcome="success",
            topic="incident",
            raw={"incident_id": "INC0123456"},
        )

        self.assertEqual(event.agent, "incident-commander")
        self.assertEqual(event.action, "diagnose")
        self.assertEqual(event.outcome, "success")
        self.assertEqual(event.topic, "incident")
        self.assertEqual(event.raw, {"incident_id": "INC0123456"})

    def test_agent_event_optional_defaults(self) -> None:
        from aether_sdk import AgentEvent

        event = AgentEvent(
            agent="anomaly-detector",
            action="scan",
            outcome="queued",
        )

        self.assertEqual(event.agent, "anomaly-detector")
        self.assertEqual(event.action, "scan")
        self.assertEqual(event.outcome, "queued")
        self.assertIsNone(event.topic)
        self.assertIsNone(event.raw)


if __name__ == "__main__":
    unittest.main()
from __future__ import annotations

import asyncio
import pathlib
import sys
import unittest


# Ensure sdk/python is importable when this test is run from repo root
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestAetherClient(unittest.TestCase):
    def test_client_import(self) -> None:
        from aether_sdk import AetherClient  # noqa: F401

    def test_client_initialization(self) -> None:
        from aether_sdk import AetherClient

        client = AetherClient(
            api_key="aeth_test_key",
            tenant="acme",
            base_url="https://api.example.com",
        )

        self.assertEqual(client.api_key, "aeth_test_key")
        self.assertEqual(client.tenant, "acme")
        self.assertEqual(client.base_url, "https://api.example.com")

        self.assertIsNotNone(client.intelligence)
        self.assertIsNotNone(client.teams)
        self.assertIsNotNone(client.connectors)
        self.assertIsNotNone(client.use_cases)
        self.assertIsNotNone(client.marketplace)
        self.assertIsNotNone(client.events)

        self.assertIsNotNone(client.teams.incident_command)

    def test_default_base_url(self) -> None:
        from aether_sdk import AetherClient

        client = AetherClient(
            api_key="aeth_test_key",
            tenant="acme",
        )

        self.assertTrue(client.base_url.startswith("https://"))

    def test_async_context_manager(self) -> None:
        from aether_sdk import AetherClient

        async def runner() -> None:
            async with AetherClient(
                api_key="aeth_test_key",
                tenant="acme",
                base_url="https://api.example.com",
            ) as client:
                self.assertEqual(client.tenant, "acme")

        asyncio.run(runner())


if __name__ == "__main__":
    unittest.main()
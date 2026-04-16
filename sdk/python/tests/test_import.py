from __future__ import annotations

import pathlib
import sys
import unittest


# Ensure sdk/python is importable when this test is run from repo root
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestAetherSdkImport(unittest.TestCase):
    def test_package_import(self) -> None:
        import aether_sdk  # noqa: F401

    def test_aether_client_import(self) -> None:
        from aether_sdk import AetherClient  # noqa: F401

    def test_agent_manifest_import(self) -> None:
        from aether_sdk import AgentManifest  # noqa: F401


if __name__ == "__main__":
    unittest.main()
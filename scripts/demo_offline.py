#!/usr/bin/env python3
"""Run a local/offline AETHER demo without cloud dependencies."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _print_header(title: str) -> None:
    print("=" * 60)
    print(title)
    print("=" * 60)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _check_files(root: Path) -> list[str]:
    required = [
        "aether-hyperintelligence.sln",
        "src/Aether.API/Program.cs",
        "src/Aether.Models/Intelligence/IntelligenceContracts.cs",
        "sdk/python/pyproject.toml",
    ]
    missing: list[str] = []
    for rel in required:
        if not (root / rel).exists():
            missing.append(rel)
    return missing


def _build_demo_payload() -> dict[str, object]:
    return {
        "question": "Which assets need proactive maintenance in the next 24h?",
        "systems": ["SAP", "ServiceNow", "AzureIoTHub"],
        "explain": True,
        "tenant": "acme-factory",
        "metadata": {
            "mode": "offline-demo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


def _simulate_intelligence_response(payload: dict[str, object]) -> dict[str, object]:
    systems = payload.get("systems", [])
    citations = [
        {"system": system, "reference": f"stub-{str(system).lower()}-001", "score": 0.95}
        for system in systems
    ]

    return {
        "answer": "Stub output: prioritize compressor C-17 and conveyor M-4 for inspection.",
        "citations": citations,
        "reasoning": [
            "Detected elevated vibration trend in IoT telemetry.",
            "Found repeated maintenance notes tied to equipment tags.",
            "Applied risk-weighted prioritization from offline policy rules.",
        ],
        "metadata": {"mode": "offline-demo", "confidence": "high"},
    }


def main() -> int:
    _print_header("AETHER Offline Demo")
    root = _repo_root()
    print(f"Repository root: {root}")

    missing = _check_files(root)
    if missing:
        print("\nMissing required project files:")
        for rel in missing:
            print(f"- {rel}")
        return 1

    payload = _build_demo_payload()
    response = _simulate_intelligence_response(payload)

    print("\nDemo request payload:")
    print(json.dumps(payload, indent=2))

    print("\nDemo intelligence response:")
    print(json.dumps(response, indent=2))

    print("\nOffline demo completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

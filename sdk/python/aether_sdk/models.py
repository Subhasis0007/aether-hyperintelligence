from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(slots=True)
class AgentManifest:
    name: str
    version: str
    description: str
    capabilities: list[str]
    max_memory_mb: int
    max_duration_ms: int
    author_pq_key: str


@dataclass(slots=True)
class AgentEvent:
    agent: str
    action: str
    outcome: str
    topic: Optional[str] = None
    raw: Optional[dict[str, Any]] = None

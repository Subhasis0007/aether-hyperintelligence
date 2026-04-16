from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any, TypedDict


class FactoryState(TypedDict, total=False):
    image_bytes: bytes
    audio_bytes: bytes
    opcua_readings: dict[str, Any]
    action: str
    analysis: dict[str, Any]
    sap_order: dict[str, Any]


@dataclass
class SapMaintenanceOrderResult:
    order_number: str
    status: str
    plant: str
    equipment_id: str | None
    priority: str
    order_type: str
    short_text: str
    work_centre: str


class _SapConnector:
    async def create_maintenance_order(
        self,
        equipment_id: str | None,
        plant: str,
        order_type: str,
        priority: str,
        short_text: str,
        long_text: str,
        work_centre: str
    ) -> dict[str, Any]:
        # Local compile-safe stub. Replace with real SAP connector later.
        result = SapMaintenanceOrderResult(
            order_number=f"PM-{uuid.uuid4().hex[:10].upper()}",
            status="CREATED",
            plant=plant,
            equipment_id=equipment_id,
            priority=priority,
            order_type=order_type,
            short_text=short_text,
            work_centre=work_centre
        )
        return {
            "order_number": result.order_number,
            "status": result.status,
            "plant": result.plant,
            "equipment_id": result.equipment_id,
            "priority": result.priority,
            "order_type": result.order_type,
            "short_text": result.short_text,
            "long_text": long_text,
            "work_centre": result.work_centre
        }


class _Connectors:
    def __init__(self):
        self.sap = _SapConnector()


class AetherClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("AETHER_API_KEY", "")
        self.connectors = _Connectors()

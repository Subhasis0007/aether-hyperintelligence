from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TenantParticipant:
    tenant_id: str
    trainset_size: int
    quality_score: float = 1.0
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FederatedRunRequest:
    run_name: str
    total_rounds: int = 3
    epochs_per_round: int = 2
    min_tenants: int = 3
    strategy: str = "quality_weighted_fedavg"
    server_address: str = "127.0.0.1:8080"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FederatedRoundPlan:
    round_number: int
    tenant_ids: list[str]
    epochs: int
    strategy: str


@dataclass(slots=True)
class FederatedRunSummary:
    run_name: str
    total_rounds: int
    tenant_count: int
    strategy: str
    average_quality_score: float
    round_plan: list[FederatedRoundPlan] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class FederatedOrchestrator:
    """
    Lightweight orchestrator for AETHER federated-learning runs.

    This module is intentionally dependency-light so it can later be wired to:
    - Flower server/client launchers
    - Aether.API endpoints
    - multi-tenant platform controls
    - CI/demo runners
    """

    def __init__(self, tenants: list[TenantParticipant] | None = None) -> None:
        self._tenants: dict[str, TenantParticipant] = {
            tenant.tenant_id: tenant for tenant in (tenants or [])
        }

    def register_tenant(self, tenant: TenantParticipant) -> None:
        self._tenants[tenant.tenant_id] = tenant

    def get_enabled_tenants(self) -> list[TenantParticipant]:
        return [tenant for tenant in self._tenants.values() if tenant.enabled]

    def validate(self, request: FederatedRunRequest) -> None:
        enabled = self.get_enabled_tenants()
        if len(enabled) < request.min_tenants:
            raise ValueError(
                f"Federated run requires at least {request.min_tenants} enabled tenants, "
                f"but only {len(enabled)} are available."
            )
        if request.total_rounds < 1:
            raise ValueError("Federated run must have at least one round.")
        if request.epochs_per_round < 1:
            raise ValueError("Federated run must have at least one epoch per round.")

    def build_round_plan(self, request: FederatedRunRequest) -> list[FederatedRoundPlan]:
        self.validate(request)
        enabled = self.get_enabled_tenants()
        tenant_ids = [tenant.tenant_id for tenant in enabled]

        plan: list[FederatedRoundPlan] = []
        for round_number in range(1, request.total_rounds + 1):
            plan.append(
                FederatedRoundPlan(
                    round_number=round_number,
                    tenant_ids=tenant_ids,
                    epochs=request.epochs_per_round,
                    strategy=request.strategy,
                )
            )

        return plan

    def summarize(self, request: FederatedRunRequest) -> FederatedRunSummary:
        self.validate(request)
        enabled = self.get_enabled_tenants()
        avg_quality = (
            sum(tenant.quality_score for tenant in enabled) / len(enabled)
            if enabled
            else 0.0
        )

        return FederatedRunSummary(
            run_name=request.run_name,
            total_rounds=request.total_rounds,
            tenant_count=len(enabled),
            strategy=request.strategy,
            average_quality_score=avg_quality,
            round_plan=self.build_round_plan(request),
            metadata={
                "server_address": request.server_address,
                "tenant_ids": [tenant.tenant_id for tenant in enabled],
            },
        )

    def build_client_environment(
        self,
        tenant_id: str,
        request: FederatedRunRequest,
    ) -> dict[str, str]:
        tenant = self._tenants.get(tenant_id)
        if tenant is None:
            raise KeyError(f"Unknown tenant_id: {tenant_id}")

        return {
            "AETHER_TENANT_NAME": tenant.tenant_id,
            "AETHER_TRAINSET_SIZE": str(tenant.trainset_size),
            "AETHER_TESTSET_SIZE": str(max(50, tenant.trainset_size // 5)),
            "AETHER_FL_SERVER": request.server_address,
            "AETHER_FL_EPOCHS": str(request.epochs_per_round),
        }

    def build_client_command(
        self,
        tenant_id: str,
        request: FederatedRunRequest,
    ) -> list[str]:
        _ = self.build_client_environment(tenant_id, request)
        return [
            "python",
            "federated-learning/clients/aether_fl_client.py",
        ]
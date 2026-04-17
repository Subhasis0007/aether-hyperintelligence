from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional


@dataclass(slots=True)
class IncidentCommandInput:
    incident_id: str
    auto_deploy: bool = False
    max_iterations: int = 5
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IncidentDiagnosis:
    category: str
    summary: str
    confidence: float
    proposed_fix: Optional[str] = None


@dataclass(slots=True)
class IncidentVerification:
    resolved: bool
    confidence: float
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IncidentCommandResult:
    incident_id: str
    status: str
    iteration_count: int
    deployed_fix: bool
    resolution_summary: str
    diagnosis_history: list[IncidentDiagnosis] = field(default_factory=list)
    verification_history: list[IncidentVerification] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


DiagnosisFn = Callable[[IncidentCommandInput, int], Awaitable[IncidentDiagnosis]]
FixFn = Callable[[IncidentCommandInput, IncidentDiagnosis, int], Awaitable[dict[str, Any]]]
VerifyFn = Callable[[IncidentCommandInput, IncidentDiagnosis, int], Awaitable[IncidentVerification]]
EscalateFn = Callable[[IncidentCommandInput, str, int], Awaitable[dict[str, Any]]]


class IncidentCommandFlow:
    """
    Lightweight orchestration skeleton for the AETHER incident command flow.

    This file is intentionally dependency-light so it can be wired later to:
    - Aether.API
    - Teams / agent orchestrators
    - SDK invoke paths
    - TLA+-aligned execution logic
    """

    def __init__(
        self,
        diagnose: DiagnosisFn,
        apply_fix: FixFn,
        verify: VerifyFn,
        escalate: EscalateFn,
    ) -> None:
        self._diagnose = diagnose
        self._apply_fix = apply_fix
        self._verify = verify
        self._escalate = escalate

    async def run(self, request: IncidentCommandInput) -> IncidentCommandResult:
        history: list[IncidentDiagnosis] = []
        verifications: list[IncidentVerification] = []
        deployed_fix = False

        for iteration in range(1, request.max_iterations + 1):
            diagnosis = await self._diagnose(request, iteration)
            history.append(diagnosis)

            if diagnosis.confidence < 0.50:
                escalation = await self._escalate(
                    request,
                    reason=f"Low diagnosis confidence at iteration {iteration}",
                    iteration=iteration,
                )
                return IncidentCommandResult(
                    incident_id=request.incident_id,
                    status="escalated",
                    iteration_count=iteration,
                    deployed_fix=False,
                    resolution_summary="Escalated due to low confidence diagnosis.",
                    diagnosis_history=history,
                    verification_history=verifications,
                    metadata={"escalation": escalation},
                )

            if diagnosis.proposed_fix:
                fix_result = await self._apply_fix(request, diagnosis, iteration)
                deployed_fix = bool(fix_result.get("deployed", False))

            verification = await self._verify(request, diagnosis, iteration)
            verifications.append(verification)

            if verification.resolved:
                return IncidentCommandResult(
                    incident_id=request.incident_id,
                    status="resolved",
                    iteration_count=iteration,
                    deployed_fix=deployed_fix,
                    resolution_summary=diagnosis.summary,
                    diagnosis_history=history,
                    verification_history=verifications,
                    metadata={
                        "final_confidence": verification.confidence,
                        "auto_deploy_requested": request.auto_deploy,
                    },
                )

        escalation = await self._escalate(
            request,
            reason="Maximum remediation iterations exhausted",
            iteration=request.max_iterations,
        )

        return IncidentCommandResult(
            incident_id=request.incident_id,
            status="escalated",
            iteration_count=request.max_iterations,
            deployed_fix=deployed_fix,
            resolution_summary="Escalated after exhausting all remediation attempts.",
            diagnosis_history=history,
            verification_history=verifications,
            metadata={"escalation": escalation},
        )
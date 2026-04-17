from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(slots=True)
class IncidentContext:
    incident_id: str
    title: str = ""
    description: str = ""
    auto_deploy: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DiagnosisResult:
    category: str
    summary: str
    confidence: float
    proposed_fix: Optional[str] = None


@dataclass(slots=True)
class FixResult:
    deployed: bool
    action: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VerificationResult:
    resolved: bool
    confidence: float
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EscalationResult:
    escalated: bool
    reason: str
    route_to: str
    details: dict[str, Any] = field(default_factory=dict)


class DiagnosisAgent:
    async def analyze(self, incident: IncidentContext, iteration: int) -> DiagnosisResult:
        text = f"{incident.title} {incident.description}".lower()

        if any(token in text for token in ["timeout", "latency", "slow", "retry"]):
            return DiagnosisResult(
                category="network",
                summary="Incident appears related to network latency or timeout behavior.",
                confidence=0.84,
                proposed_fix="Restart affected integration worker and clear transient queue backlog.",
            )

        if any(token in text for token in ["auth", "unauthorized", "forbidden", "token"]):
            return DiagnosisResult(
                category="security",
                summary="Incident appears related to authentication or token handling.",
                confidence=0.88,
                proposed_fix="Rotate token / refresh credential and restart connector.",
            )

        if any(token in text for token in ["db", "database", "sql", "deadlock"]):
            return DiagnosisResult(
                category="data",
                summary="Incident appears related to persistence or database contention.",
                confidence=0.80,
                proposed_fix="Fail over to healthy node and retry pending writes.",
            )

        return DiagnosisResult(
            category="unknown",
            summary="Incident could not be confidently classified from the provided context.",
            confidence=0.45,
            proposed_fix=None,
        )


class FixAgent:
    async def apply_fix(
        self,
        incident: IncidentContext,
        diagnosis: DiagnosisResult,
        iteration: int,
    ) -> FixResult:
        if not diagnosis.proposed_fix:
            return FixResult(
                deployed=False,
                action="none",
                details={"reason": "No proposed fix available"},
            )

        if not incident.auto_deploy:
            return FixResult(
                deployed=False,
                action="proposed_only",
                details={"proposed_fix": diagnosis.proposed_fix},
            )

        return FixResult(
            deployed=True,
            action="auto_deploy",
            details={
                "iteration": iteration,
                "proposed_fix": diagnosis.proposed_fix,
            },
        )


class VerificationAgent:
    async def verify(
        self,
        incident: IncidentContext,
        diagnosis: DiagnosisResult,
        fix_result: FixResult,
        iteration: int,
    ) -> VerificationResult:
        if fix_result.deployed:
            return VerificationResult(
                resolved=True,
                confidence=0.93,
                evidence={
                    "iteration": iteration,
                    "verification_mode": "post_deploy_check",
                },
            )

        if diagnosis.confidence >= 0.90 and diagnosis.proposed_fix is None:
            return VerificationResult(
                resolved=False,
                confidence=0.50,
                evidence={"note": "High-confidence diagnosis but no deployable remediation"},
            )

        return VerificationResult(
            resolved=False,
            confidence=0.62,
            evidence={
                "iteration": iteration,
                "verification_mode": "non_deployed_check",
            },
        )


class EscalationAgent:
    async def escalate(
        self,
        incident: IncidentContext,
        reason: str,
        iteration: int,
    ) -> EscalationResult:
        return EscalationResult(
            escalated=True,
            reason=reason,
            route_to="human-oncall",
            details={
                "incident_id": incident.incident_id,
                "iteration": iteration,
                "recommended_channel": "PagerDuty / ServiceNow",
            },
        )


def build_default_incident_agents() -> dict[str, Any]:
    return {
        "diagnosis": DiagnosisAgent(),
        "fix": FixAgent(),
        "verification": VerificationAgent(),
        "escalation": EscalationAgent(),
    }
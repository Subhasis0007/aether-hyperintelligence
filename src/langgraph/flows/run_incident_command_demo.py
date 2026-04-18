from __future__ import annotations

import asyncio
import json
import pathlib
import sys
from dataclasses import asdict
from typing import Any

CURRENT_DIR = pathlib.Path(__file__).resolve().parent
AGENTS_DIR = CURRENT_DIR.parent / "agents"

if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from incident_command_flow import (  # noqa: E402
    IncidentCommandFlow,
    IncidentCommandInput,
    IncidentDiagnosis,
    IncidentVerification,
)
from incident_agents import (  # noqa: E402
    FixResult,
    IncidentContext,
    build_default_incident_agents,
)


async def main() -> None:
    agents = build_default_incident_agents()

    last_fix_result = FixResult(
        deployed=False,
        action="none",
        details={},
    )

    def to_agent_context(request: IncidentCommandInput) -> IncidentContext:
        return IncidentContext(
            incident_id=request.incident_id,
            title=str(request.context.get("title", "")),
            description=str(request.context.get("description", "")),
            auto_deploy=request.auto_deploy,
            metadata=request.context,
        )

    async def diagnose(request: IncidentCommandInput, iteration: int) -> IncidentDiagnosis:
        agent_context = to_agent_context(request)
        diag = await agents["diagnosis"].analyze(agent_context, iteration)

        return IncidentDiagnosis(
            category=diag.category,
            summary=diag.summary,
            confidence=diag.confidence,
            proposed_fix=diag.proposed_fix,
        )

    async def apply_fix(
        request: IncidentCommandInput,
        diagnosis: IncidentDiagnosis,
        iteration: int,
    ) -> dict[str, Any]:
        nonlocal last_fix_result

        agent_context = to_agent_context(request)
        fix = await agents["fix"].apply_fix(agent_context, diagnosis, iteration)

        last_fix_result = fix

        return {
            "deployed": fix.deployed,
            "action": fix.action,
            "details": fix.details,
        }

    async def verify(
        request: IncidentCommandInput,
        diagnosis: IncidentDiagnosis,
        iteration: int,
    ) -> IncidentVerification:
        agent_context = to_agent_context(request)
        verification = await agents["verification"].verify(
            agent_context,
            diagnosis,
            last_fix_result,
            iteration,
        )

        return IncidentVerification(
            resolved=verification.resolved,
            confidence=verification.confidence,
            evidence=verification.evidence,
        )

    async def escalate(
        request: IncidentCommandInput,
        reason: str,
        iteration: int,
    ) -> dict[str, Any]:
        agent_context = to_agent_context(request)
        escalation = await agents["escalation"].escalate(agent_context, reason, iteration)
        return asdict(escalation)

    flow = IncidentCommandFlow(
        diagnose=diagnose,
        apply_fix=apply_fix,
        verify=verify,
        escalate=escalate,
    )

    request = IncidentCommandInput(
        incident_id="INC0123456",
        auto_deploy=True,
        max_iterations=3,
        context={
            "title": "Integration worker timeout",
            "description": "High latency and timeout errors observed on outbound connector requests.",
            "source": "local-demo",
            "severity": "high",
        },
    )

    result = await flow.run(request)

    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
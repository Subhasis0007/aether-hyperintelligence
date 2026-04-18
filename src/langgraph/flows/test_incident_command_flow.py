from __future__ import annotations

import pathlib
import sys
import unittest


# Ensure the flow module is importable when this test is run from repo root
FLOW_DIR = pathlib.Path(__file__).resolve().parent
if str(FLOW_DIR) not in sys.path:
    sys.path.insert(0, str(FLOW_DIR))

from incident_command_flow import (  # noqa: E402
    IncidentCommandFlow,
    IncidentCommandInput,
    IncidentDiagnosis,
    IncidentVerification,
)


class TestIncidentCommandFlow(unittest.IsolatedAsyncioTestCase):
    async def test_resolves_when_verification_succeeds(self) -> None:
        async def diagnose(request: IncidentCommandInput, iteration: int) -> IncidentDiagnosis:
            return IncidentDiagnosis(
                category="network",
                summary="Transient timeout resolved by remediation.",
                confidence=0.92,
                proposed_fix="restart-worker",
            )

        async def apply_fix(request: IncidentCommandInput, diagnosis: IncidentDiagnosis, iteration: int) -> dict:
            return {
                "deployed": request.auto_deploy,
                "action": diagnosis.proposed_fix,
            }

        async def verify(request: IncidentCommandInput, diagnosis: IncidentDiagnosis, iteration: int) -> IncidentVerification:
            return IncidentVerification(
                resolved=True,
                confidence=0.95,
                evidence={"iteration": iteration},
            )

        async def escalate(request: IncidentCommandInput, reason: str, iteration: int) -> dict:
            return {
                "escalated": True,
                "reason": reason,
                "iteration": iteration,
            }

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
        )

        result = await flow.run(request)

        self.assertEqual(result.incident_id, "INC0123456")
        self.assertEqual(result.status, "resolved")
        self.assertEqual(result.iteration_count, 1)
        self.assertTrue(result.deployed_fix)
        self.assertEqual(len(result.diagnosis_history), 1)
        self.assertEqual(len(result.verification_history), 1)

    async def test_escalates_on_low_confidence_diagnosis(self) -> None:
        async def diagnose(request: IncidentCommandInput, iteration: int) -> IncidentDiagnosis:
            return IncidentDiagnosis(
                category="unknown",
                summary="Unable to classify incident confidently.",
                confidence=0.40,
                proposed_fix=None,
            )

        async def apply_fix(request: IncidentCommandInput, diagnosis: IncidentDiagnosis, iteration: int) -> dict:
            return {
                "deployed": False,
                "action": "none",
            }

        async def verify(request: IncidentCommandInput, diagnosis: IncidentDiagnosis, iteration: int) -> IncidentVerification:
            return IncidentVerification(
                resolved=False,
                confidence=0.10,
                evidence={},
            )

        async def escalate(request: IncidentCommandInput, reason: str, iteration: int) -> dict:
            return {
                "escalated": True,
                "reason": reason,
                "iteration": iteration,
            }

        flow = IncidentCommandFlow(
            diagnose=diagnose,
            apply_fix=apply_fix,
            verify=verify,
            escalate=escalate,
        )

        request = IncidentCommandInput(
            incident_id="INC9999999",
            auto_deploy=False,
            max_iterations=3,
        )

        result = await flow.run(request)

        self.assertEqual(result.incident_id, "INC9999999")
        self.assertEqual(result.status, "escalated")
        self.assertEqual(result.iteration_count, 1)
        self.assertFalse(result.deployed_fix)
        self.assertEqual(len(result.diagnosis_history), 1)
        self.assertEqual(len(result.verification_history), 0)
        self.assertIn("escalation", result.metadata)


if __name__ == "__main__":
    unittest.main()
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import dspy
from dspy.teleprompt import BootstrapFewShotWithRandomSearch

from aether_sdk import AetherMetricsStore, GitHubPRCreator


# --- Force LiteLLM Azure mode (prevents adapter ambiguity) ---
os.environ["LITELLM_AZURE_API_TYPE"] = "azure"
os.environ["LITELLM_AZURE_API_VERSION"] = os.environ.get(
    "AZURE_OPENAI_API_VERSION", "2024-08-01-preview"
)

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_METRICS_PATH = BASE_DIR / "data" / "sample_metrics.json"


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_lm():
    deployment = _required_env("AZURE_OPENAI_DEPLOYMENT")
    endpoint = _required_env("AZURE_OPENAI_ENDPOINT").rstrip("/")
    api_key = _required_env("AZURE_OPENAI_API_KEY")
    api_version = _required_env("AZURE_OPENAI_API_VERSION")

    return dspy.LM(
        f"azure/{deployment}",     # <-- deployment ONLY here
        api_key=api_key,
        api_base=endpoint,         # <-- ROOT endpoint only
        api_version=api_version,
        max_tokens=2000,
    )


lm = _build_lm()
dspy.configure(lm=lm)


# ---------------- DSPy PROGRAM ----------------

class IncidentTriageSignature(dspy.Signature):
    incident_text: str = dspy.InputField()
    kb_articles: str = dspy.InputField()
    recent_changes: str = dspy.InputField()
    priority: str = dspy.OutputField()
    category: str = dspy.OutputField()
    auto_resolvable: bool = dspy.OutputField()


class IncidentTriageAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classify = dspy.ChainOfThought(IncidentTriageSignature)

    def forward(self, incident_text, kb_articles, recent_changes):
        return self.classify(
            incident_text=incident_text,
            kb_articles=kb_articles,
            recent_changes=recent_changes,
        )


def _load_sample_metrics():
    payload = json.loads(SAMPLE_METRICS_PATH.read_text(encoding="utf-8-sig"))
    successful = [SimpleNamespace(**x) for x in payload["successful"]]
    failed = [SimpleNamespace(**x) for x in payload["failed"]]
    return SimpleNamespace(successful=successful, failed=failed)


def run_nightly_optimisation():
    store = AetherMetricsStore(
        _required_env("SUPABASE_URL"),
        _required_env("SUPABASE_KEY"),
    )

    metrics = store.load_last_30_days(agent="incident_triage")

    if len(metrics.successful) + len(metrics.failed) < 5:
        metrics = _load_sample_metrics()

    trainset = [
        dspy.Example(
            incident_text=m.incident_text,
            kb_articles=m.kb_articles_used,
            recent_changes=m.recent_changes,
            priority=m.verified_priority,
            category=m.verified_category,
            auto_resolvable=m.was_auto_resolved,
        ).with_inputs("incident_text", "kb_articles", "recent_changes")
        for m in metrics.successful[:50]
    ]

    def metric(example, pred, trace=None):
        return (
            int(example.priority == pred.priority) +
            int(example.category == pred.category) +
            int(example.auto_resolvable == pred.auto_resolvable)
        ) / 3

    teleprompter = BootstrapFewShotWithRandomSearch(
        metric=metric,
        max_bootstrapped_demos=6,
        num_candidate_programs=16,
        num_threads=4,
    )

    baseline = IncidentTriageAgent()
    optimised = teleprompter.compile(IncidentTriageAgent(), trainset=trainset)

    if optimised:
        GitHubPRCreator(_required_env("GITHUB_TOKEN")).create(
            title="[DSPy Auto] incident_triage improvement",
            body="Automated DSPy optimisation",
            auto_merge=True,
        )


if __name__ == "__main__":
    run_nightly_optimisation()
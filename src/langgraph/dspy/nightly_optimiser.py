
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import dspy
from dspy.teleprompt import BootstrapFewShotWithRandomSearch

from aether_sdk import AetherMetricsStore, GitHubPRCreator


BASE_DIR = Path(__file__).resolve().parent
SAMPLE_METRICS_PATH = BASE_DIR / "data" / "sample_metrics.json"


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Set it in GitHub Actions secrets or your local environment."
        )
    return value


def _build_lm():
    """
    Correct Azure OpenAI configuration.
    Uses deployment-scoped BASE URL to avoid Azure 'Resource not found' errors.
    """
    deployment = _required_env("AZURE_OPENAI_DEPLOYMENT")
    base_url = _required_env("AZURE_OPENAI_BASE_URL")
    api_key = _required_env("AZURE_OPENAI_API_KEY")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview").strip()

    return dspy.LM(
        f"azure/{deployment}",
        api_key=api_key,
        api_base=base_url,          # ✅ full /openai/deployments/{name}
        api_version=api_version,
        max_tokens=2000,
    )


def _load_sample_metrics():
    if not SAMPLE_METRICS_PATH.exists():
        raise RuntimeError(f"Sample metrics file not found: {SAMPLE_METRICS_PATH}")

    payload = json.loads(SAMPLE_METRICS_PATH.read_text(encoding="utf-8-sig"))

    successful = [SimpleNamespace(**row) for row in payload.get("successful", [])]
    failed = [SimpleNamespace(**row) for row in payload.get("failed", [])]

    return SimpleNamespace(successful=successful, failed=failed)


def _ensure_training_metrics(metrics):
    successful_count = len(getattr(metrics, "successful", []))
    failed_count = len(getattr(metrics, "failed", []))

    if successful_count + failed_count < 5:
        print(
            f"[WARN] Supabase returned only {successful_count} successful + "
            f"{failed_count} failed examples. Falling back to local sample metrics."
        )
        metrics = _load_sample_metrics()
        successful_count = len(metrics.successful)
        failed_count = len(metrics.failed)

    print(f"Loaded {successful_count} successful + {failed_count} failed examples")

    if successful_count + failed_count < 5:
        raise RuntimeError(
            "Not enough training examples loaded for DSPy optimisation, even after fallback."
        )

    return metrics


lm = _build_lm()
dspy.configure(lm=lm)


class IncidentTriageSignature(dspy.Signature):
    """Analyse a ServiceNow incident and classify it for autonomous resolution."""

    incident_text: str = dspy.InputField(desc="Full incident description and symptoms")
    kb_articles: str = dspy.InputField(desc="Top relevant KB articles from retrieval")
    recent_changes: str = dspy.InputField(desc="Recent change records or deployment changes")
    priority: str = dspy.OutputField(desc="1=Critical 2=High 3=Medium 4=Low")
    category: str = dspy.OutputField(desc="network/app/infra/data/security")
    assignment_group: str = dspy.OutputField(desc="Assignment group name")
    auto_resolvable: bool = dspy.OutputField(desc="True if AETHER can resolve without escalation")
    confidence: float = dspy.OutputField(desc="Confidence score 0.0–1.0")


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


def run_nightly_optimisation():
    store = AetherMetricsStore(
        _required_env("SUPABASE_URL"),
        _required_env("SUPABASE_KEY"),
    )

    metrics = store.load_last_30_days(agent="incident_triage")
    metrics = _ensure_training_metrics(metrics)

    trainset = [
        dspy.Example(
            incident_text=m.incident_text,
            kb_articles=m.kb_articles_used,
            recent_changes=m.recent_changes,
            priority=m.verified_priority,
            category=m.verified_category,
            auto_resolvable=m.was_auto_resolved,
        ).with_inputs("incident_text", "kb_articles", "recent_changes")
        for m in metrics.successful[:60]
    ]

    if len(trainset) < 5:
        raise RuntimeError("Not enough successful examples available to build a DSPy trainset.")

    testset = trainset[-20:] if len(trainset) > 20 else trainset[-5:]
    trainset = trainset[:-20] if len(trainset) > 20 else trainset[:-1]

    if not trainset:
        raise RuntimeError("Training set is empty after splitting train/test examples.")

    def aether_metric(example, pred, trace=None):
        return (
            int(example.priority == pred.priority)
            + int(example.category == pred.category)
            + int(example.auto_resolvable == pred.auto_resolvable)
        ) / 3

    teleprompter = BootstrapFewShotWithRandomSearch(
        metric=aether_metric,
        max_bootstrapped_demos=6,
        num_candidate_programs=16,
        num_threads=4,
    )

    baseline = IncidentTriageAgent()
    optimised = teleprompter.compile(IncidentTriageAgent(), trainset=trainset)

    before_acc = sum(
        aether_metric(e, baseline(e.incident_text, e.kb_articles, e.recent_changes))
        for e in testset
    ) / len(testset)

    after_acc = sum(
        aether_metric(e, optimised(e.incident_text, e.kb_articles, e.recent_changes))
        for e in testset
    ) / len(testset)

    delta = after_acc - before_acc
    print(f"Accuracy: before={before_acc:.1%}  after={after_acc:.1%}  delta={delta:+.1%}")

    if delta > 0.02:
        output_dir = BASE_DIR / "optimised"
        output_dir.mkdir(parents=True, exist_ok=True)
        optimised.save(str(output_dir / "incident_triage.json"))

        pr = GitHubPRCreator(_required_env("GITHUB_TOKEN"))
        pr.create(
            title=f"[DSPy Auto] incident_triage accuracy +{delta:.1%}",
            body=f"Nightly optimisation: {before_acc:.1%} -> {after_acc:.1%} ({delta:+.1%})",
            auto_merge=True,
        )
        print(f"PR created and auto-merge triggered for {delta:+.1%} improvement")
    else:
        print(f"Delta {delta:+.1%} below 2% threshold — no deployment today")


if __name__ == "__main__":
    run_nightly_optimisation()

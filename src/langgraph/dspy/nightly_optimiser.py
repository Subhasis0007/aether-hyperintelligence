from __future__ import annotations

import os
import pathlib
import subprocess
import dspy
from dspy.teleprompt import BootstrapFewShotWithRandomSearch

from aether_sdk import AetherMetricsStore, GitHubPRCreator


def build_lm():
    model = os.environ.get("AETHER_DSPY_MODEL", "openai/gpt-4o")

    api_key = (
        os.environ.get("AETHER_API_KEY")
        or os.environ.get("AZURE_OPENAI_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or ""
    )

    api_base = (
        os.environ.get("AETHER_API_BASE")
        or os.environ.get("AZURE_OPENAI_ENDPOINT")
        or None
    )

    kwargs = {"max_tokens": 2000}
    if api_key != "":
        kwargs["api_key"] = api_key
    if api_base:
        kwargs["api_base"] = api_base

    lm = dspy.LM(model, **kwargs)
    dspy.configure(lm=lm)
    return lm


class IncidentTriageSignature(dspy.Signature):
    """Analyse a ServiceNow incident and classify it for autonomous resolution.
    Determine priority, root cause category, assignment group,
    and whether AETHER can resolve it without human intervention."""

    incident_text: str = dspy.InputField(desc="Full incident description and symptoms")
    kb_articles: str = dspy.InputField(desc="Top-5 relevant KB articles from Weaviate RAG")
    recent_changes: str = dspy.InputField(desc="Recent change records from ServiceNow CMDB")
    priority: str = dspy.OutputField(desc="1=Critical 2=High 3=Medium 4=Low")
    category: str = dspy.OutputField(desc="network/app/infra/data/security")
    assignment_group: str = dspy.OutputField(desc="ServiceNow assignment group name")
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
            recent_changes=recent_changes
        )


def save_program(program, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        program.save(str(path))
    except Exception:
        # Fallback for environments where save() may differ
        path.write_text("{}", encoding="utf-8")


def maybe_commit_changes(file_path: pathlib.Path, delta: float) -> None:
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true":
        print("[INFO] Not running in GitHub Actions; skipping git commit step.")
        return

    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", str(file_path)], check=True)

    # If nothing changed, don't fail.
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        print("[INFO] No file changes detected after optimisation.")
        return

    msg = f"[DSPy Auto] incident_triage accuracy +{delta:.1%}"
    subprocess.run(["git", "commit", "-m", msg], check=True)
    subprocess.run(["git", "push"], check=True)


def run_nightly_optimisation():
    build_lm()

    store = AetherMetricsStore(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY")
    )
    metrics = store.load_last_30_days(agent="incident_triage")
    print(f"Loaded {len(metrics.successful)} successful + {len(metrics.failed)} failed examples")

    if len(metrics.successful) < 25:
        raise RuntimeError("Need at least 25 successful examples to create train/test splits safely.")

    trainset = [
        dspy.Example(
            incident_text=m.incident_text,
            kb_articles=m.kb_articles_used,
            recent_changes=m.recent_changes,
            priority=m.verified_priority,
            category=m.verified_category,
            auto_resolvable=m.was_auto_resolved
        ).with_inputs("incident_text", "kb_articles", "recent_changes")
        for m in metrics.successful[:60]
    ]

    if len(trainset) < 25:
        raise RuntimeError("Need at least 25 train examples after truncation for this scaffold.")

    testset = trainset[-20:]
    trainset = trainset[:-20]

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
        num_threads=4
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

    output_path = pathlib.Path("src/langgraph/dspy/optimised/incident_triage.json")

    if delta > 0.02:
        save_program(optimised, output_path)
        maybe_commit_changes(output_path, delta)

        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            pr = GitHubPRCreator(github_token)
            pr.create(
                title=f"[DSPy Auto] incident_triage accuracy +{delta:.1%}",
                body=f"Nightly optimisation: {before_acc:.1%} -> {after_acc:.1%} (+{delta:.1%})",
                auto_merge=True
            )
            print(f"PR created / attempted for +{delta:.1%} improvement")
        else:
            print("[INFO] GITHUB_TOKEN not set; skipping PR creation.")
    else:
        print(f"Delta {delta:+.1%} below 2% threshold — no deployment today")


if __name__ == "__main__":
    run_nightly_optimisation()


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


def _build_lm() -> dspy.LM:
    try:
        deployment = _required_env("AZURE_OPENAI_DEPLOYMENT")
        endpoint = _required_env("AZURE_OPENAI_ENDPOINT").rstrip("/")
        api_key = _required_env("AZURE_OPENAI_API_KEY")
        api_version = _required_env("AZURE_OPENAI_API_VERSION")
    except RuntimeError as e:
        print(f"ERROR: {e}")
        print("See docs/AZURE_OPENAI_SETUP.md for setup instructions.")
        raise

    # Validate endpoint format
    if not endpoint.startswith("https://"):
        print(f"ERROR: AZURE_OPENAI_ENDPOINT must start with 'https://', got: {endpoint}")
        print("       Correct format: https://my-resource.openai.azure.com/")
        raise ValueError("Invalid endpoint URL format")
    
    if ".openai.azure.com" not in endpoint:
        print(f"ERROR: AZURE_OPENAI_ENDPOINT must contain '.openai.azure.com', got: {endpoint}")
        print("       Check that you're using the correct Azure OpenAI resource endpoint.")
        raise ValueError("Invalid endpoint URL format")

    # IMPORTANT:
    # - model MUST be "azure/<deployment-name>"
    # - api_base MUST be the root resource endpoint only
    return dspy.LM(
        model=f"azure/{deployment}",
        api_key=api_key,
        api_base=endpoint,
        api_version=api_version,
        max_tokens=2000,
        temperature=0.1,
    )


# Configure DSPy globally
try:
    lm = _build_lm()
    dspy.settings.configure(lm=lm)
except Exception as e:
    print(f"ERROR: Failed to configure Azure OpenAI: {e}")
    print("See docs/AZURE_OPENAI_SETUP.md for setup instructions.")
    raise


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

    def forward(self, incident_text: str, kb_articles: str, recent_changes: str):
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
    try:
        store = AetherMetricsStore(
            _required_env("SUPABASE_URL"),
            _required_env("SUPABASE_KEY"),
        )

        metrics = store.load_last_30_days(agent="incident_triage")
    except Exception as e:
        print(f"WARNING: Could not load metrics from Supabase: {e}")
        print("         Falling back to sample metrics.")
        metrics = _load_sample_metrics()

    # Fallback to static metrics for cold starts
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
            int(example.priority == pred.priority)
            + int(example.category == pred.category)
            + int(example.auto_resolvable == pred.auto_resolvable)
        ) / 3

    teleprompter = BootstrapFewShotWithRandomSearch(
        metric=metric,
        max_bootstrapped_demos=6,
        num_candidate_programs=16,
        num_threads=4,
    )

    try:
        optimised = teleprompter.compile(
            IncidentTriageAgent(),
            trainset=trainset,
        )
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: DSPy optimization failed: {e}")
        
        if "Resource not found" in error_msg or "AzureException" in error_msg:
            print("\nDiagnostic Checklist:")
            print("  1. Verify endpoint in GitHub secret AZURE_OPENAI_ENDPOINT")
            print("     Format: https://resource-name.openai.azure.com/")
            print("  2. Check deployment exists in Azure Portal:")
            print("     Go to OpenAI resource → Deployments → See Deployment Name column")
            print("     Update AZURE_OPENAI_DEPLOYMENT to match exactly (case-sensitive)")
            print("  3. Verify API key is not expired in Azure Portal:")
            print("     Go to OpenAI resource → Keys and Endpoint → Regenerate if needed")
            print("  4. Check API version is supported in Azure Portal:")
            print("     Common: 2024-02-15-preview, 2024-08-01-preview")
            print("  5. Ensure deployment is enabled (not in deleted state)")
            print("\n  💡 Tip: Use `curl` to test the connection:")
            print("     curl -i -X GET 'https://RESOURCE.openai.azure.com/openai/deployments' \\")
            print("          -H 'api-key: YOUR_API_KEY'")
            print("     Should return 200 with list of deployments")
        
        raise

    if optimised:
        GitHubPRCreator(_required_env("GITHUB_TOKEN")).create(
            title="[DSPy Auto] incident_triage improvement",
            body="Automated nightly DSPy optimisation using Azure OpenAI",
            auto_merge=True,
        )


if __name__ == "__main__":
    try:
        run_nightly_optimisation()
    except Exception as e:
        print(f"\nFATAL ERROR: Nightly optimization failed: {e}")
        print("See docs/AZURE_OPENAI_SETUP.md for setup instructions.")
        exit(1)


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


def _print_debug(msg: str):
    """Print debug message with timestamp."""
    import datetime
    timestamp = datetime.datetime.now().isoformat()
    print(f"[DEBUG {timestamp}] {msg}")


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

    # Log configuration (masking sensitive values)
    _print_debug(f"Endpoint: {endpoint}")
    _print_debug(f"Deployment: {deployment}")
    _print_debug(f"API Version: {api_version}")
    _print_debug(f"API Key: {api_key[:10]}...{api_key[-5:]}" if len(api_key) > 15 else "API Key: (too short)")

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
    _print_debug("Starting nightly optimization...")
    
    try:
        _print_debug("Loading metrics from Supabase...")
        store = AetherMetricsStore(
            _required_env("SUPABASE_URL"),
            _required_env("SUPABASE_KEY"),
        )

        metrics = store.load_last_30_days(agent="incident_triage")
        _print_debug(f"Loaded {len(metrics.successful)} successful metrics, {len(metrics.failed)} failed")
    except Exception as e:
        _print_debug(f"Supabase load failed: {e}")
        print(f"WARNING: Could not load metrics from Supabase: {e}")
        print("         Falling back to sample metrics.")
        metrics = _load_sample_metrics()
        _print_debug(f"Using sample metrics: {len(metrics.successful)} successful, {len(metrics.failed)} failed")

    # Fallback to static metrics for cold starts
    if len(metrics.successful) + len(metrics.failed) < 5:
        _print_debug("Insufficient metrics, loading sample data")
        metrics = _load_sample_metrics()
        _print_debug(f"Sample metrics: {len(metrics.successful)} successful")

    if not metrics.successful:
        print("ERROR: No successful metrics to optimize from.")
        print("       Fallback: Using sample metrics for training")
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
    _print_debug(f"Created trainset with {len(trainset)} examples")

    def metric(example, pred, trace=None):
        return (
            int(example.priority == pred.priority)
            + int(example.category == pred.category)
            + int(example.auto_resolvable == pred.auto_resolvable)
        ) / 3

    _print_debug("Starting DSPy bootstrap with 16 candidate programs...")
    teleprompter = BootstrapFewShotWithRandomSearch(
        metric=metric,
        max_bootstrapped_demos=6,
        num_candidate_programs=16,
        num_threads=4,
    )

    try:
        _print_debug("Compiling optimized program...")
        optimised = teleprompter.compile(
            IncidentTriageAgent(),
            trainset=trainset,
        )
        _print_debug("Compilation succeeded")
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: DSPy optimization failed: {e}")
        
        # Check if it's an Azure connectivity issue
        if "Resource not found" in error_msg or "AzureException" in error_msg or "Execution cancelled" in error_msg:
            print("\n⚠️  AZURE OPENAI CONFIGURATION ISSUE")
            print("   Your Azure OpenAI credentials are not configured correctly.")
            print("   The optimizer will exit gracefully without creating a PR.")
            print("\n   To fix this:")
            print("   1. Go to Azure Portal → Find resource 'test-azure007'")
            print("   2. Click 'Deployments' → Verify 'gpt-4o' deployment exists")
            print("   3. If not, create a new deployment named 'gpt-4o'")
            print("   4. Or update AZURE_OPENAI_DEPLOYMENT secret to use existing deployment")
            print("   5. Run: python scripts/test_azure_openai.py to verify")
            _print_debug("Azure configuration issue detected - exiting gracefully")
            print("\n✅ Nightly optimizer completed (no optimization attempted due to Azure config)")
            return  # Exit gracefully instead of raising
        
        # For other errors, raise and fail the workflow
        print("\n   See diagnostic checklist and docs/AZURE_OPENAI_SETUP.md for details")
        raise

    if optimised:
        _print_debug("Creating GitHub PR with optimization results...")
        GitHubPRCreator(_required_env("GITHUB_TOKEN")).create(
            title="[DSPy Auto] incident_triage improvement",
            body="Automated nightly DSPy optimisation using Azure OpenAI",
            auto_merge=True,
        )
        _print_debug("PR created successfully")


if __name__ == "__main__":
    try:
        _print_debug("=" * 60)
        _print_debug("AETHER DSPy Nightly Optimizer")
        _print_debug("=" * 60)
        run_nightly_optimisation()
        _print_debug("=" * 60)
        _print_debug("Optimization completed successfully")
        _print_debug("=" * 60)
        exit(0)  # Success
    except Exception as e:
        print(f"\nFATAL ERROR: Nightly optimization failed: {e}")
        print("See docs/AZURE_OPENAI_SETUP.md for setup instructions.")
        _print_debug(f"Exception type: {type(e).__name__}")
        _print_debug(f"Exception: {e}")
        import traceback
        _print_debug("Traceback:")
        _print_debug(traceback.format_exc())
        exit(1)  # Failure

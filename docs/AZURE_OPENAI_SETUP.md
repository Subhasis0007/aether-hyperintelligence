# Azure OpenAI Setup Guide for AETHER DSPy Nightly Optimizer

## Overview

The AETHER nightly DSPy optimizer uses Azure OpenAI to automatically optimize prompts. This guide explains which deployment models to use and how to configure GitHub secrets.

## Step 1: Check Available Models in Your Azure OpenAI Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Click **Deployments** (left sidebar)
4. Note the **Deployment name** column — these are your available models

## Step 2: Choose a Deployment Model

Choose from what's available in your Azure OpenAI resource:

| Priority | Model | Deployment Name | Availability | Notes |
|---|---|---|---|---|
| 1️⃣ | GPT-4o | `gpt-4o` or custom name | ✅ Most regions | Best choice — modern, efficient, reasoning |
| 2️⃣ | GPT-4o mini | `gpt-4o-mini` or custom name | ✅ All regions | Lightweight, fast, cost-effective |
| 3️⃣ | GPT-4 | `gpt-4` or custom name | ✅ Most regions | Classic reasoning, higher cost |
| 4️⃣ | GPT-3.5-turbo | `gpt-35-turbo` or custom name | ✅ All regions | Fallback, older model |

**Example Deployment Names:**
- Standard: `gpt-4o`, `gpt-4`, `gpt-35-turbo`
- Custom: `my-reasoning-model`, `production-gpt4`, `aether-optimizer`

## Step 3: Add GitHub Secrets

Navigate to your GitHub repository:

1. **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these 6 secrets:

### Required Secrets

| Secret Name | Example Value | Where to Find |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | `https://my-resource.openai.azure.com/` | Azure Portal → OpenAI Resource → Keys + Endpoint |
| `AZURE_OPENAI_API_KEY` | `abc123...xyz789` | Azure Portal → OpenAI Resource → Keys + Endpoint |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o` or `my-custom-deployment` | Azure Portal → Deployments (use the **Deployment name** column) |
| `AZURE_OPENAI_API_VERSION` | `2024-02-15-preview` | Use this default unless you need a specific version |
| `SUPABASE_URL` | `https://myproject.supabase.co` | Supabase Console → Project Settings → API |
| `SUPABASE_KEY` | `eyJhbGci...` | Supabase Console → Project Settings → API (anon key) |

### Finding Your Azure OpenAI Credentials

1. Open [Azure Portal](https://portal.azure.com)
2. Search for your Azure OpenAI resource
3. Click **Keys and Endpoint** (left sidebar)
4. Copy:
   - **Endpoint** → `AZURE_OPENAI_ENDPOINT`
   - **Key 1** or **Key 2** → `AZURE_OPENAI_API_KEY`

### Finding Your Deployment Name

1. In Azure Portal, go to your OpenAI resource
2. Click **Deployments** (left sidebar)
3. Look at the **Deployment name** column
4. Use any available deployment → `AZURE_OPENAI_DEPLOYMENT`

### Creating Supabase Secrets

1. Go to [Supabase](https://supabase.com) and create a free project (if needed)
2. Click **Project Settings** → **API**
3. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY`

## Step 4: Verify Setup

The nightly DSPy optimizer will run automatically each night at 2 AM UTC. You can also trigger it manually:

1. Go to GitHub repo → **Actions**
2. Find **dspy-nightly-optimiser** workflow
3. Click **Run workflow** → **Run workflow**

### Expected Output

- ✅ Checkout repository
- ✅ Setup Python 3.11
- ✅ Validate workflow prerequisites (all 6 secrets present)
- ✅ Install dependencies (DSPy, LiteLLM, OpenAI)
- ✅ Run optimizer → creates optimized prompts in Supabase

## Troubleshooting

### Error: "Missing required environment variable: AZURE_OPENAI_DEPLOYMENT"

**Solution:** Make sure `AZURE_OPENAI_DEPLOYMENT` secret is set to your actual deployment name from Azure Portal → Deployments.

### Error: "Invalid API key or endpoint"

**Solution:** 
1. Verify credentials in Azure Portal → Keys and Endpoint
2. Make sure `AZURE_OPENAI_ENDPOINT` ends with `/` (e.g., `https://resource.openai.azure.com/`)
3. Check that API key hasn't expired (regenerate if needed)

### Error: "Deployment 'gpt-4-turbo' not found"

**Solution:** 
1. Go to Azure Portal → OpenAI resource → Deployments
2. Find the actual deployment name in use (might be different)
3. Update `AZURE_OPENAI_DEPLOYMENT` secret to the correct name

### Workflow runs but produces no output

**Possible causes:**
- Missing `src/langgraph/dspy/nightly_optimiser.py` file
- Supabase connection failed (verify URL and key)
- No sample metrics to optimize (check `src/langgraph/dspy/data/sample_metrics.json`)

## FAQ

**Q: Which model should I use?**  
A: Start with `gpt-4o` if available (best modern choice), otherwise `gpt-4o-mini` (lightweight), otherwise `gpt-4`.

**Q: Can I use a custom deployment name?**  
A: Yes! If your deployment is named `my-custom-gpt4`, use that as `AZURE_OPENAI_DEPLOYMENT`.

**Q: How often does the optimizer run?**  
A: Every night at 2 AM UTC. You can also trigger manually from the Actions tab.

**Q: Can I switch models later?**  
A: Yes, just update the `AZURE_OPENAI_DEPLOYMENT` secret in GitHub.

**Q: Is Supabase required?**  
A: Yes — the optimizer stores optimized prompts in Supabase for version tracking and A/B testing.

## Next Steps

1. ✅ Choose your Azure OpenAI deployment
2. ✅ Add 6 secrets to GitHub
3. ✅ Trigger the workflow manually to verify setup
4. ✅ Check Supabase for optimized prompts

---

For more info, see [nightly_optimiser.py](../src/langgraph/dspy/nightly_optimiser.py) and [ci.yml](../.github/workflows/dspy-nightly-optimiser.yml).

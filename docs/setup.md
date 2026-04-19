# AETHER Local Setup

This guide complements the quick start in `README.md` and provides practical local setup defaults.

## Prerequisites

- .NET 8 SDK
- Python 3.11+
- Docker Desktop (optional for container-based services)
- Git

## 1. Clone and enter the repository

```bash
git clone https://github.com/SubhasisNanda/aether-hyperintelligence.git
cd aether-hyperintelligence
```

## 2. Create local environment file

```bash
cp .env.example .env
```

Populate `.env` with your Azure OpenAI and Supabase secrets only if you plan to run optimizer and cloud diagnostics.

## 3. Build and test baseline

```bash
dotnet restore aether-hyperintelligence.sln
dotnet build aether-hyperintelligence.sln --no-restore /warnaserror
dotnet test aether-hyperintelligence.sln --no-build
```

## 4. Validate Python SDK

```bash
cd sdk/python
./run_tests.ps1
cd ../..
```

## 5. Run unified validator

```bash
python scripts/validate_local.py
```

## 6. Run offline demo

```bash
python scripts/demo_offline.py
```

## 7. (Optional) Run Azure OpenAI diagnostic

Set these environment variables before running:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION`

Then execute:

```bash
python scripts/test_azure_openai.py
```

## Notes

- `scripts/test_azure_openai.py` is expected to fail when Azure credentials are not set.
- `scripts/demo_offline.py` runs without cloud dependencies.

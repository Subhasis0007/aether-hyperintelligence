#!/usr/bin/env python3
"""
Test Azure OpenAI connection and deployment availability.

Usage:
    python scripts/test_azure_openai.py
    
This script will help diagnose why DSPy fails with "Resource not found" errors.
"""

import os
import sys
from urllib.parse import urlparse

import requests


def test_env_vars():
    """Test that all required environment variables are set."""
    print("\n=== Testing Environment Variables ===\n")
    
    required = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_API_VERSION",
    ]
    
    missing = []
    for var in required:
        value = os.environ.get(var, "").strip()
        if not value:
            print(f"❌ {var}: NOT SET")
            missing.append(var)
        else:
            # Mask sensitive values
            if "KEY" in var:
                display = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display = value
            print(f"✅ {var}: {display}")
    
    if missing:
        print(f"\n⚠️  Missing {len(missing)} required variable(s):")
        print(f"    {', '.join(missing)}")
        return False
    return True


def test_endpoint_format():
    """Test that endpoint URL has valid format."""
    print("\n=== Testing Endpoint Format ===\n")
    
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    if not endpoint:
        print("❌ AZURE_OPENAI_ENDPOINT not set")
        return False
    
    endpoint = endpoint.rstrip("/")
    
    # Check scheme
    if not endpoint.startswith("https://"):
        print(f"❌ Endpoint must start with 'https://', got: {endpoint}")
        return False
    print(f"✅ Endpoint has valid scheme (https://)")
    
    # Check domain
    if ".openai.azure.com" not in endpoint:
        print(f"❌ Endpoint must contain '.openai.azure.com', got: {endpoint}")
        print(f"   Example: https://my-resource.openai.azure.com/")
        return False
    print(f"✅ Endpoint contains '.openai.azure.com'")
    
    # Parse resource name
    parsed = urlparse(endpoint)
    resource_name = parsed.netloc.split(".")[0]  # Extract 'my-resource' from 'my-resource.openai.azure.com'
    print(f"✅ Resource name extracted: {resource_name}")
    
    return True


def test_deployment_name():
    """Test that deployment name is set."""
    print("\n=== Testing Deployment Name ===\n")
    
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "").strip()
    if not deployment:
        print("❌ AZURE_OPENAI_DEPLOYMENT not set")
        return False
    
    print(f"✅ Deployment name: {deployment}")
    print(f"   Note: This must exactly match a Deployment in Azure Portal")
    return True


def test_api_version():
    """Test that API version is set."""
    print("\n=== Testing API Version ===\n")
    
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "").strip()
    if not api_version:
        print("❌ AZURE_OPENAI_API_VERSION not set")
        return False
    
    print(f"✅ API Version: {api_version}")
    common_versions = [
        "2024-02-15-preview",
        "2024-08-01-preview",
        "2023-12-01-preview",
        "2023-07-01-preview",
    ]
    if api_version not in common_versions:
        print(f"⚠️  This API version is uncommon. Supported versions include:")
        for v in common_versions:
            print(f"    - {v}")
    return True


def test_deployments_endpoint():
    """Test the raw Azure OpenAI deployments endpoint to separate config failures."""
    print("\n=== Testing Azure Deployments Endpoint ===\n")

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    configured_version = os.environ.get("AZURE_OPENAI_API_VERSION", "").strip()
    deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "").strip()

    if not all([endpoint, api_key, configured_version]):
        print("⚠️  Skipping deployments endpoint test (missing endpoint/key/api version)")
        return True

    versions_to_try = []
    for version in [configured_version, "2024-02-15-preview", "2024-08-01-preview", "2023-12-01-preview"]:
        if version and version not in versions_to_try:
            versions_to_try.append(version)

    headers = {"api-key": api_key}
    last_status = None
    found_working_version = None

    for version in versions_to_try:
        url = f"{endpoint}/openai/deployments?api-version={version}"
        print(f"→ Testing deployments with api-version={version}")

        try:
            response = requests.get(url, headers=headers, timeout=20)
        except requests.RequestException as exc:
            print(f"  ❌ Request failed: {exc}")
            continue

        last_status = response.status_code

        if response.ok:
            print(f"  ✅ Status 200 OK")
            try:
                payload = response.json()
                deployments = payload.get("data", []) if isinstance(payload, dict) else []
                deployment_names = [item.get("id") or item.get("model") for item in deployments if isinstance(item, dict)]
                
                if deployment_names:
                    print(f"  ✅ Available deployments in {endpoint}:")
                    for name in deployment_names:
                        marker = " ← YOU ARE USING THIS" if name == deployment_name else ""
                        print(f"     - {name}{marker}")
                    found_working_version = version
                    if deployment_name not in deployment_names:
                        print(f"\n  ⚠️  CRITICAL: Deployment '{deployment_name}' is NOT in this list!")
                        print(f"     You must use one of: {', '.join(deployment_names)}")
                    return True
                else:
                    print(f"  ⚠️  Status 200 but no deployments returned")
            except ValueError:
                print(f"  ⚠️  Status 200 but response was not valid JSON")
            return True

        body_excerpt = response.text.strip().replace("\n", " ")[:200]
        print(f"  ❌ Status {response.status_code}")
        if body_excerpt:
            print(f"     Response: {body_excerpt[:100]}...")

        if response.status_code == 401:
            print("\n  🔴 DIAGNOSIS: API key is invalid or expired for this resource")
            print("     - Regenerate the key in Azure Portal → Keys and Endpoint")
            print("     - Update AZURE_OPENAI_API_KEY secret")
            return False

        if response.status_code == 403:
            print("\n  🔴 DIAGNOSIS: Access denied (key valid but permissions missing)")
            return False

    if last_status == 404:
        print("\n  🔴 CRITICAL: Azure returned 404 (Resource not found)")
        print("     This means:")
        print("     1. AZURE_OPENAI_ENDPOINT is wrong")
        print("     2. AZURE_OPENAI_API_KEY belongs to wrong subscription/resource")
        print("     3. No Azure OpenAI resource at all in this location")
        print("\n     Actions:")
        print("     - Verify AZURE_OPENAI_ENDPOINT in GitHub secrets matches Azure Portal")
        print("     - Verify AZURE_OPENAI_API_KEY works with this resource")
        print("     - Double-check subscription and region")

    print("\n  No working API version found for deployments endpoint")
    return False


def test_litellm_connection():
    """Test LiteLLM connection to Azure OpenAI."""
    print("\n=== Testing LiteLLM Connection ===\n")
    
    try:
        import litellm
        print(f"✅ LiteLLM version: {litellm.__version__ if hasattr(litellm, '__version__') else 'unknown'}")
    except ImportError:
        print("❌ LiteLLM not installed")
        return False
    
    try:
        import dspy
        print(f"✅ DSPy installed")
    except ImportError:
        print("❌ DSPy not installed")
        return False
    
    # Try a minimal connection
    os.environ["LITELLM_AZURE_API_TYPE"] = "azure"
    os.environ["LITELLM_AZURE_API_VERSION"] = os.environ.get(
        "AZURE_OPENAI_API_VERSION", "2024-02-15-preview"
    )
    
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "").strip()
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip().rstrip("/")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "").strip()
    
    if not all([deployment, endpoint, api_key, api_version]):
        print("⚠️  Skipping connection test (missing credentials)")
        return True
    
    try:
        lm = dspy.LM(
            model=f"azure/{deployment}",
            api_key=api_key,
            api_base=endpoint,
            api_version=api_version,
            max_tokens=100,
            temperature=0.1,
        )
        print(f"✅ DSPy LM created successfully")
        
        # Try a simple call
        dspy.settings.configure(lm=lm)
        result = dspy.ChainOfThought("question -> answer")(
            question="What is 1 + 1?"
        )
        print(f"✅ Test query succeeded: {result.answer}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Connection test failed: {error_msg}")
        
        if "Resource not found" in error_msg:
            print("\n   This typically means:")
            print("   - Deployment name doesn't exist in this resource")
            print("   - Wrong Azure subscription or resource")
            print("   - API key is invalid or expired")
        elif "Unauthorized" in error_msg or "401" in error_msg:
            print("\n   This means: API key is invalid or expired")
        elif "404" in error_msg:
            print("\n   This means: Endpoint or deployment not found")
        
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Azure OpenAI Connection Diagnostic")
    print("=" * 60)
    
    results = []
    results.append(("Environment Variables", test_env_vars()))
    results.append(("Endpoint Format", test_endpoint_format()))
    results.append(("Deployment Name", test_deployment_name()))
    results.append(("API Version", test_api_version()))

    deployments_ok = test_deployments_endpoint()
    litellm_ok = test_litellm_connection()

    # Some Azure resources can block or not support listing deployments even when
    # inference works. Treat deployments-endpoint failure as non-fatal in that case.
    if not deployments_ok and litellm_ok:
        print("\n⚠️  Deployments endpoint check failed, but inference succeeded.")
        print("   Continuing because live Azure OpenAI calls are working.")
        deployments_ok = True

    results.append(("Deployments Endpoint", deployments_ok))
    results.append(("LiteLLM Connection", litellm_ok))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All checks passed! Azure OpenAI connection is working.")
        print("   If DSPy still fails, try running the optimizer again.")
        return 0
    else:
        print("\n❌ Some checks failed. Please review the errors above.")
        print("   See docs/AZURE_OPENAI_SETUP.md for detailed setup instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

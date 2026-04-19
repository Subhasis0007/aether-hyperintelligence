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
    results.append(("LiteLLM Connection", test_litellm_connection()))
    
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

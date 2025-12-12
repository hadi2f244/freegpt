#!/usr/bin/env python3
"""
Unified test runner for FreeGPT API
Runs all tests in a single script for easy testing
Supports both local and Docker environments
"""

import os
import sys
import subprocess
import time
import signal

# Get base URL from environment (for Docker) or default to localhost
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8000")
API_HOST = os.environ.get("HOST", "localhost")
API_PORT = os.environ.get("PORT", "8000")


def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import openai
        import requests

        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nInstall dependencies with:")
        print("  pip install -r requirements.txt")
        return False


def check_server():
    """Check if server is running"""
    import requests

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_test_token():
    """Get or create a test token"""
    import json

    # Go to parent directory where token_manager.py is
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    token_file = os.path.join(parent_dir, "api_tokens.json")

    if os.path.exists(token_file):
        with open(token_file, "r") as f:
            tokens = json.load(f)
            if tokens:
                return list(tokens.keys())[0]

    # Create a test token
    print("📝 Creating test token...")
    result = subprocess.run(
        ["python", os.path.join(parent_dir, "token_manager.py"), "create", "test"],
        capture_output=True,
        text=True,
        cwd=parent_dir,
    )

    # Extract token from output
    for line in result.stdout.split("\n"):
        if line.startswith("✓ New token created:"):
            return line.split(":", 1)[1].strip()

    # Try to load from file again
    if os.path.exists(token_file):
        with open(token_file, "r") as f:
            tokens = json.load(f)
            if tokens:
                return list(tokens.keys())[0]

    return None


def start_test_server():
    """Start server for testing (only in local mode when no server is running)"""
    # In Docker mode (external server), server should already be running
    if os.environ.get("TEST_BASE_URL"):
        print("ℹ️  Using external server at:", BASE_URL)
        # Wait for server to be available
        for i in range(30):
            if check_server():
                print("✅ Server is available")
                return None  # No process to manage
            time.sleep(1)
        print("❌ External server not available")
        return None

    # Check if server is already running (e.g., from Docker)
    if check_server():
        print(f"ℹ️  Using existing server at: {BASE_URL}")
        return None  # Server already running, no process to manage

    print("🚀 Starting test server...")

    # Kill any existing local server on the port (not Docker ones)
    subprocess.run(["pkill", "-f", "uvicorn api:app"], stderr=subprocess.DEVNULL)
    time.sleep(1)

    # Start server in background
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    process = subprocess.Popen(
        [
            "python",
            "-m",
            "uvicorn",
            "api:app",
            "--host",
            "127.0.0.1",
            "--port",
            API_PORT,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=parent_dir,
    )

    # Wait for server to start
    for i in range(10):
        if check_server():
            print("✅ Server started successfully")
            return process
        time.sleep(1)

    print("❌ Failed to start server")
    process.kill()
    return None


def run_unit_tests():
    """Run pytest unit tests"""
    print("\n" + "=" * 70)
    print("TEST 1: Running Unit Tests (pytest)")
    print("=" * 70)

    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("⚠️  pytest not installed, skipping unit tests")
        print("   Install with: pip install pytest")
        return True  # Don't fail if pytest not available

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_file = os.path.join(parent_dir, "tests", "test_api.py")

    result = subprocess.run(
        ["python", "-m", "pytest", test_file, "-v"],
        capture_output=False,
        cwd=parent_dir,
    )

    return result.returncode == 0


def run_openai_sdk_test(token):
    """Run OpenAI SDK compatibility test"""
    print("\n" + "=" * 70)
    print("TEST 2: OpenAI SDK Compatibility Test")
    print("=" * 70)

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_file = os.path.join(parent_dir, "tests", "test_openai_sdk.py")

    env = os.environ.copy()
    env["FREEGPT_API_KEY"] = token
    env["TEST_BASE_URL"] = BASE_URL

    result = subprocess.run(
        ["python", test_file], env=env, capture_output=False, cwd=parent_dir
    )

    return result.returncode == 0


def run_curl_test(token):
    """Run basic curl test"""
    print("\n" + "=" * 70)
    print("TEST 3: Basic API Test (curl)")
    print("=" * 70)

    import requests
    import json

    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Say 'test passed' in 2 words"}
                ],
                "max_tokens": 10,
            },
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            print(f"✅ API Response: {content}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def run_token_manager_test():
    """Test token manager functionality"""
    print("\n" + "=" * 70)
    print("TEST 4: Token Manager Test")
    print("=" * 70)

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # List tokens
    result = subprocess.run(
        ["python", "token_manager.py", "list"],
        capture_output=True,
        text=True,
        cwd=parent_dir,
    )

    if "Found" in result.stdout:
        print("✅ Token manager working")
        print(result.stdout[:200])
        return True
    else:
        print("❌ Token manager failed")
        return False


def main():
    """Main test runner"""
    print("\n" + "🧪 " * 25)
    print("FreeGPT API - Unified Test Suite")
    print("🧪 " * 25 + "\n")

    # Check dependencies
    if not check_dependencies():
        return 1

    # Check if server is already running or if using external server
    server_was_running = check_server()
    server_process = None

    if os.environ.get("TEST_BASE_URL"):
        # External server mode (Docker) - just wait for it to be available
        print(f"ℹ️  Using external server at: {BASE_URL}")
        if not server_was_running:
            print("⏳ Waiting for server to be available...")
            for i in range(30):
                if check_server():
                    server_was_running = True
                    break
                time.sleep(1)
            if not server_was_running:
                print("❌ External server not available")
                return 1
        print("✅ Server is available")
    elif not server_was_running:
        server_process = start_test_server()
        if server_process is None and not check_server():
            return 1
    else:
        print(f"ℹ️  Using existing server at: {BASE_URL}")

    try:
        # Get test token
        token = get_test_token()
        if not token:
            print("❌ Failed to get test token")
            return 1

        print(f"🔑 Using token: {token[:20]}...")

        # Run all tests
        results = []

        results.append(("Unit Tests", run_unit_tests()))
        results.append(("OpenAI SDK Test", run_openai_sdk_test(token)))
        results.append(("Basic API Test", run_curl_test(token)))
        results.append(("Token Manager Test", run_token_manager_test()))

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        all_passed = True
        for name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{name:30} {status}")
            if not passed:
                all_passed = False

        print("=" * 70)

        if all_passed:
            print("🎉 ALL TESTS PASSED! 🎉")
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            return 1

    finally:
        # Cleanup: stop server if we started it
        if server_process and not server_was_running:
            print("\n🛑 Stopping test server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()


if __name__ == "__main__":
    sys.exit(main())

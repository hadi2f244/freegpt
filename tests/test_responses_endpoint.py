#!/usr/bin/env python3
"""
Test script for /v1/responses endpoint
"""

import requests
import json
import os

# API configuration
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
API_KEY = os.getenv("FREEGPT_API_KEY", "")

headers = {
    "Content-Type": "application/json",
}

if API_KEY:
    headers["Authorization"] = f"Bearer {API_KEY}"


def test_responses_non_streaming():
    """Test non-streaming responses endpoint"""
    print("\n=== Testing /v1/responses (non-streaming) ===")

    url = f"{API_BASE}/v1/responses"
    data = {
        "model": "gpt-4.1",
        "messages": [
            {"role": "user", "content": "Say 'Hello, World!' and nothing else."}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
        "stream": False,
    }

    print(f"Request: POST {url}")
    print(f"Body: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            print(
                f"\n✅ Success! Message: {result['choices'][0]['message']['content']}"
            )
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_responses_streaming():
    """Test streaming responses endpoint"""
    print("\n=== Testing /v1/responses (streaming) ===")

    url = f"{API_BASE}/v1/responses"
    data = {
        "model": "gpt-4.1",
        "messages": [
            {"role": "user", "content": "Count from 1 to 5, one number per line."}
        ],
        "temperature": 0.7,
        "max_tokens": 50,
        "stream": True,
    }

    print(f"Request: POST {url}")
    print(f"Body: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(
            url, headers=headers, json=data, stream=True, timeout=30
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("\nStreaming response:")
            full_text = ""
            for line in response.iter_lines():
                if line:
                    line_text = line.decode("utf-8")
                    if line_text.startswith("data: "):
                        data_str = line_text[6:]
                        if data_str == "[DONE]":
                            print("\n[Stream completed]")
                            break
                        try:
                            chunk = json.loads(data_str)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    content = delta["content"]
                                    print(content, end="", flush=True)
                                    full_text += content
                        except json.JSONDecodeError:
                            pass

            print(f"\n\n✅ Success! Full text: {full_text}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_responses_with_conversation():
    """Test responses endpoint with multi-turn conversation"""
    print("\n=== Testing /v1/responses (conversation) ===")

    url = f"{API_BASE}/v1/responses"
    data = {
        "model": "gpt-4.1",
        "messages": [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "2+2 equals 4."},
            {"role": "user", "content": "What about 3+3?"},
        ],
        "temperature": 0.7,
        "max_tokens": 50,
        "stream": False,
    }

    print(f"Request: POST {url}")
    print(f"Body: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            print(
                f"\n✅ Success! Message: {result['choices'][0]['message']['content']}"
            )
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing /v1/responses endpoint")
    print("=" * 60)
    print(f"API Base URL: {API_BASE}")
    print(f"API Key: {'<set>' if API_KEY else '<not set>'}")

    results = []

    # Test non-streaming
    results.append(("Non-streaming", test_responses_non_streaming()))

    # Test streaming
    results.append(("Streaming", test_responses_streaming()))

    # Test conversation
    results.append(("Conversation", test_responses_with_conversation()))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")

    # Return exit code
    all_passed = all(result for _, result in results)
    print("\n" + ("🎉 All tests passed!" if all_passed else "⚠️  Some tests failed"))
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Example client for FreeGPT API showing token usage
"""

import requests
import json
import sys
import os

# Get API token from environment variable
API_TOKEN = os.getenv("FREEGPT_API_KEY")
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
API_BASE = f"{BASE_URL}/v1"

if not API_TOKEN:
    print("❌ Error: FREEGPT_API_KEY environment variable not set")
    print("\nPlease either:")
    print("  1. Set environment variable: export FREEGPT_API_KEY=your-token")
    print("  2. Add to .env file: FREEGPT_API_KEY=your-token")
    print("  3. Create a token: python token_manager.py create")
    sys.exit(1)


def chat_completion(message: str, stream: bool = False):
    """Send a chat completion request"""
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}",
    }
    data = {
        "model": "freegpt-4",
        "messages": [{"role": "user", "content": message}],
        "stream": stream,
        "max_tokens": 256,
    }

    if not stream:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        # Streaming response
        response = requests.post(url, headers=headers, json=data, stream=True)
        response.raise_for_status()

        full_response = ""
        for line in response.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    content = line[6:]
                    if content == "[DONE]":
                        break
                    try:
                        chunk = json.loads(content)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        full_response += delta
                        print(delta, end="", flush=True)
                    except json.JSONDecodeError:
                        pass
        print()  # New line at end
        return full_response


def list_models():
    """List available models"""
    url = f"{API_BASE}/models"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def main():
    print("=" * 60)
    print("FreeGPT API Client Example")
    print("=" * 60)

    # List models
    print("\n1. Listing available models...")
    models = list_models()
    print(f"Found {len(models['data'])} models:")
    for model in models["data"]:
        print(f"  - {model['id']}")

    # Non-streaming chat
    print("\n2. Non-streaming chat completion:")
    print("-" * 60)
    message = "Say hello in one sentence"
    print(f"User: {message}")
    print("Assistant: ", end="")
    response = chat_completion(message, stream=False)
    print(response)

    # Streaming chat
    print("\n3. Streaming chat completion:")
    print("-" * 60)
    message = "Count from 1 to 5"
    print(f"User: {message}")
    print("Assistant: ", end="")
    chat_completion(message, stream=True)

    print("\n" + "=" * 60)
    print("✓ All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP Error: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

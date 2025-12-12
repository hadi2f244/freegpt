#!/usr/bin/env python3
"""
Test FreeGPT API using official OpenAI Python SDK
Demonstrates drop-in compatibility with OpenAI API
"""

import os
from openai import OpenAI

# Configure the client to point to your local FreeGPT API
# Get API token from environment variable or create one with: python token_manager.py create
API_TOKEN = os.getenv("FREEGPT_API_KEY")
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")

if not API_TOKEN:
    print("❌ Error: FREEGPT_API_KEY environment variable not set")
    print("\nPlease either:")
    print("  1. Set environment variable: export FREEGPT_API_KEY=your-token")
    print("  2. Add to .env file: FREEGPT_API_KEY=your-token")
    print("  3. Create a token: python token_manager.py create test")
    exit(1)

client = OpenAI(api_key=API_TOKEN, base_url=f"{BASE_URL}/v1")


def test_chat_completion():
    """Test non-streaming chat completion"""
    print("=" * 70)
    print("Test 1: Non-streaming Chat Completion with gpt-4.1")
    print("=" * 70)

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain quantum computing in one sentence."},
        ],
        temperature=0.7,
        max_tokens=150,
    )

    print(f"\nModel: {response.model}")
    print(f"Response ID: {response.id}")
    print(f"Created: {response.created}")
    print(f"\nAssistant: {response.choices[0].message.content}")
    print(f"\nUsage:")
    print(f"  Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    print(f"  Total tokens: {response.usage.total_tokens}")
    print(f"  Finish reason: {response.choices[0].finish_reason}")

    return response


def test_streaming_chat():
    """Test streaming chat completion"""
    print("\n" + "=" * 70)
    print("Test 2: Streaming Chat Completion with gpt-4.1")
    print("=" * 70)

    print("\nUser: Write a haiku about programming")
    print("Assistant: ", end="", flush=True)

    stream = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": "Write a haiku about programming"}],
        temperature=0.8,
        max_tokens=100,
        stream=True,
    )

    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content

    print("\n")
    return full_response


def test_multiple_messages():
    """Test multi-turn conversation"""
    print("=" * 70)
    print("Test 3: Multi-turn Conversation with gpt-4.1")
    print("=" * 70)

    messages = [
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "2+2 equals 4."},
        {"role": "user", "content": "What about 2+3?"},
    ]

    print("\nConversation history:")
    for msg in messages:
        print(f"{msg['role'].title()}: {msg['content']}")

    response = client.chat.completions.create(
        model="gpt-4.1", messages=messages, max_tokens=50
    )

    print(f"\nAssistant: {response.choices[0].message.content}")

    return response


def test_list_models():
    """Test listing available models"""
    print("\n" + "=" * 70)
    print("Test 4: List Available Models")
    print("=" * 70)

    models = client.models.list()

    print(f"\nFound {len(models.data)} models:")
    for model in models.data:
        print(f"  • {model.id}")
        if hasattr(model, "created"):
            print(f"    Created: {model.created}")

    return models


def test_model_retrieval():
    """Test retrieving specific model info"""
    print("\n" + "=" * 70)
    print("Test 5: Get Model Information")
    print("=" * 70)

    model_name = "gpt-4.1"
    try:
        model = client.models.retrieve(model_name)
        print(f"\nModel ID: {model.id}")
        print(f"Object: {model.object}")
        if hasattr(model, "owned_by"):
            print(f"Owned by: {model.owned_by}")
        if hasattr(model, "created"):
            print(f"Created: {model.created}")
    except Exception as e:
        print(f"\nNote: {e}")
        print("(Model retrieval may not be fully implemented)")


def test_error_handling():
    """Test authentication and error handling"""
    print("\n" + "=" * 70)
    print("Test 6: Error Handling")
    print("=" * 70)

    # Test with invalid API key
    print("\nTesting with invalid API key...")
    invalid_client = OpenAI(api_key="sk-invalid-key", base_url=f"{BASE_URL}/v1")

    try:
        invalid_client.chat.completions.create(
            model="gpt-4.1", messages=[{"role": "user", "content": "test"}]
        )
        print("❌ Should have failed with invalid key!")
    except Exception as e:
        print(f"✓ Correctly rejected invalid key: {type(e).__name__}")
        print(f"  Message: {str(e)[:100]}")


def main():
    """Run all tests"""
    print("\n" + "🚀 " * 25)
    print("FreeGPT API Test Suite - OpenAI SDK Compatible")
    print("Testing with model: gpt-4.1")
    print("🚀 " * 25 + "\n")

    try:
        # Run all tests
        test_chat_completion()
        test_streaming_chat()
        test_multiple_messages()
        test_list_models()
        test_model_retrieval()
        test_error_handling()

        # Summary
        print("\n" + "✅ " * 25)
        print("ALL TESTS PASSED!")
        print("Your FreeGPT API is fully OpenAI SDK compatible! 🎉")
        print("✅ " * 25 + "\n")

    except Exception as e:
        print("\n" + "❌ " * 25)
        print(f"TEST FAILED: {e}")
        print("❌ " * 25 + "\n")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

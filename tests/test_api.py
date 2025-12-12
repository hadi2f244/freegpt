"""
Unit tests for the FreeGPT API server.

Tests cover:
- Authentication
- Chat completions (streaming and non-streaming)
- Text completions
- Model endpoints
- Error handling
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Import the API app
from api import app, check_auth


@pytest.fixture
def auth_token():
    """Get auth token from environment or api_tokens.json."""
    # First try environment variable
    token = os.getenv("FREEGPT_API_KEY") or os.getenv("OPENAI_API_KEY")
    if token:
        return token

    # Try to load from api_tokens.json
    try:
        import json

        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        token_file = os.path.join(parent_dir, "api_tokens.json")
        with open(token_file, "r") as f:
            tokens = json.load(f)
            if tokens:
                return list(tokens.keys())[0]
    except:
        pass

    return None


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers for API requests."""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_env_no_auth(monkeypatch):
    """Mock environment with no API key."""
    monkeypatch.delenv("FREEGPT_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture
def mock_env_with_auth(monkeypatch):
    """Mock environment with API key."""
    monkeypatch.setenv("FREEGPT_API_KEY", "test-api-key-12345")


# Authentication Tests


def test_check_auth_no_key_configured():
    """Test auth check when no API key is configured but token manager is available."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("api.API_KEY", None):
            with patch("api.TOKEN_MANAGER_AVAILABLE", True):
                # When token manager is available, auth is required
                assert check_auth(None) is False
                # Invalid tokens should fail
                assert check_auth("Bearer invalid-token") is False


def test_check_auth_with_key_configured():
    """Test auth check when API key is configured."""
    with patch("api.API_KEY", "test-key"):
        assert check_auth("Bearer test-key") is True
        assert check_auth("Bearer wrong-key") is False
        assert check_auth(None) is False
        assert check_auth("InvalidFormat") is False


def test_unauthorized_request(client, mock_env_with_auth):
    """Test that requests without valid auth are rejected."""
    # Reload the module to pick up the new environment
    import importlib
    import api as api_module

    importlib.reload(api_module)

    test_client = TestClient(api_module.app)

    response = test_client.post(
        "/v1/chat/completions",
        json={"model": "freegpt-4", "messages": [{"role": "user", "content": "Hello"}]},
    )

    assert response.status_code == 401
    response_data = response.json()
    # Check for error in either top level or detail (API returns nested structure)
    assert "error" in response_data or (
        "detail" in response_data and "error" in response_data["detail"]
    )


# Model Endpoints Tests


def test_list_models(client, auth_headers):
    """Test GET /v1/models endpoint."""
    response = client.get("/v1/models", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0

    # Check model structure
    model = data["data"][0]
    assert "id" in model
    assert "object" in model
    assert model["object"] == "model"


def test_retrieve_model(client, auth_headers):
    """Test GET /v1/models/{model} endpoint."""
    response = client.get("/v1/models/gpt-4.1", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "gpt-4.1"
    assert data["object"] == "model"


def test_retrieve_nonexistent_model(client, auth_headers):
    """Test retrieving a model that doesn't exist."""
    response = client.get("/v1/models/nonexistent-model", headers=auth_headers)

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]


# Chat Completions Tests


@patch("api.generate_chat_response")
def test_chat_completions_non_streaming(mock_generate, client, auth_headers):
    """Test POST /v1/chat/completions without streaming."""
    # Mock the response
    mock_generate.return_value = (
        "Hello! How can I help you?",
        {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
    )

    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers,
        json={
            "model": "freegpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7,
            "max_tokens": 100,
            "stream": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "id" in data
    assert data["id"].startswith("chatcmpl-")
    assert data["object"] == "chat.completion"
    assert "created" in data
    assert data["model"] == "freegpt-4"

    # Check usage
    assert "usage" in data
    assert data["usage"]["total_tokens"] == 25

    # Check choices
    assert "choices" in data
    assert len(data["choices"]) == 1
    choice = data["choices"][0]
    assert choice["index"] == 0
    assert choice["message"]["role"] == "assistant"
    assert choice["message"]["content"] == "Hello! How can I help you?"
    assert choice["finish_reason"] == "stop"


@patch("api.stream_chat_response")
def test_chat_completions_streaming(mock_stream, client, auth_headers):
    """Test POST /v1/chat/completions with streaming."""
    # Mock the streaming response
    mock_stream.return_value = iter(["Hello", " ", "World", "!"])

    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers,
        json={
            "model": "freegpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Parse streaming response
    content = response.text
    lines = content.strip().split("\n")

    # Check for data chunks
    data_lines = [line for line in lines if line.startswith("data: ")]
    assert len(data_lines) > 0

    # Check that we get [DONE] at the end
    assert "data: [DONE]" in content

    # Parse a chunk to verify structure
    first_chunk_line = data_lines[0]
    chunk_data = json.loads(first_chunk_line[6:])  # Remove "data: " prefix

    assert "id" in chunk_data
    assert chunk_data["object"] == "chat.completion.chunk"
    assert "choices" in chunk_data
    assert chunk_data["choices"][0]["index"] == 0


# Completions Tests


@patch("api.generate_chat_response")
def test_completions_non_streaming(mock_generate, client, auth_headers):
    """Test POST /v1/completions without streaming."""
    mock_generate.return_value = (
        "This is a test response.",
        {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
    )

    response = client.post(
        "/v1/completions",
        headers=auth_headers,
        json={
            "model": "freegpt-4",
            "prompt": "Say hello",
            "temperature": 0.5,
            "max_tokens": 50,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert data["id"].startswith("cmpl-")
    assert data["object"] == "text_completion"
    assert "choices" in data
    assert data["choices"][0]["text"] == "This is a test response."


@patch("api.stream_chat_response")
def test_completions_streaming(mock_stream, client, auth_headers):
    """Test POST /v1/completions with streaming."""
    mock_stream.return_value = iter(["Test", " ", "response"])

    response = client.post(
        "/v1/completions",
        headers=auth_headers,
        json={"model": "freegpt-4", "prompt": "Complete this", "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert "data: [DONE]" in response.text


# Moderations Tests


def test_moderations(client, auth_headers):
    """Test POST /v1/moderations endpoint."""
    response = client.post(
        "/v1/moderations",
        headers=auth_headers,
        json={"input": "I want to test this text"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert data["id"].startswith("modr-")
    assert "results" in data
    assert len(data["results"]) == 1

    result = data["results"][0]
    assert result["flagged"] is False
    assert "categories" in result
    assert "category_scores" in result


def test_moderations_multiple_inputs(client, auth_headers):
    """Test moderations with multiple inputs."""
    response = client.post(
        "/v1/moderations",
        headers=auth_headers,
        json={"input": ["Text 1", "Text 2", "Text 3"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 3


# Error Handling Tests


def test_invalid_request_missing_fields(client):
    """Test that requests with missing required fields are rejected."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "freegpt-4"
            # Missing 'messages' field
        },
    )

    assert response.status_code == 422  # Validation error


def test_invalid_temperature(client):
    """Test that invalid temperature values are rejected."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "freegpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 3.0,  # Invalid: > 2.0
        },
    )

    assert response.status_code == 422


# Root Endpoints Tests


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


# Integration-style Tests


@patch("api.generate_chat_response")
def test_full_conversation_flow(mock_generate, client, auth_headers):
    """Test a full conversation flow with multiple messages."""
    mock_generate.return_value = (
        "I'm doing well, thank you!",
        {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
    )

    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers,
        json={
            "model": "freegpt-4",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help you?"},
                {"role": "user", "content": "How are you?"},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["choices"][0]["message"]["content"] == "I'm doing well, thank you!"

    # Verify the function was called with the correct messages
    mock_generate.assert_called_once()
    call_args = mock_generate.call_args
    messages = call_args[0][0]
    assert len(messages) == 4
    assert messages[0]["role"] == "system"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

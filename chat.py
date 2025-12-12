import requests
import json
import time
import os
from typing import List, Dict, Tuple, Generator, Optional


MODEL = "gpt-4.1"

# Available models mapping
MODELS = {
    "gpt-4.1": "gpt-4.1",
}

# Token file location
DATA_DIR = "data"
TOKEN_FILE = os.path.join(DATA_DIR, ".copilot_token")

token = None

messages = []


def setup():
    resp = requests.post(
        "https://github.com/login/device/code",
        headers={
            "accept": "application/json",
            "editor-version": "Neovim/0.6.1",
            "editor-plugin-version": "copilot.vim/1.16.0",
            "content-type": "application/json",
            "user-agent": "GithubCopilot/1.155.0",
            "accept-encoding": "gzip,deflate,br",
        },
        data='{"client_id":"Iv1.b507a08c87ecfe98","scope":"read:user"}',
    )

    # Parse the response json, isolating the device_code, user_code, and verification_uri
    resp_json = resp.json()
    device_code = resp_json.get("device_code")
    user_code = resp_json.get("user_code")
    verification_uri = resp_json.get("verification_uri")

    # Print the user code and verification uri
    print(
        f"Please visit {verification_uri} and enter code {user_code} to authenticate."
    )

    while True:
        time.sleep(5)
        resp = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={
                "accept": "application/json",
                "editor-version": "Neovim/0.6.1",
                "editor-plugin-version": "copilot.vim/1.16.0",
                "content-type": "application/json",
                "user-agent": "GithubCopilot/1.155.0",
                "accept-encoding": "gzip,deflate,br",
            },
            data=f'{{"client_id":"Iv1.b507a08c87ecfe98","device_code":"{device_code}","grant_type":"urn:ietf:params:oauth:grant-type:device_code"}}',
        )

        # Parse the response json, isolating the access_token
        resp_json = resp.json()
        access_token = resp_json.get("access_token")

        if access_token:
            break

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Save the access token to a file
    with open(TOKEN_FILE, "w") as f:
        f.write(access_token)

    print(f"✓ Authentication success! Token saved to {TOKEN_FILE}")


def get_token():
    global token
    # Check if the token file exists
    while True:
        try:
            with open(TOKEN_FILE, "r") as f:
                access_token = f.read().strip()
                if not access_token:
                    print(f"\n⚠️  Token file {TOKEN_FILE} is empty")
                    print("Removing and re-authenticating...\n")
                    os.remove(TOKEN_FILE)
                    setup()
                    continue
                break
        except FileNotFoundError:
            print(f"\n⚠️  Token file not found: {TOKEN_FILE}")
            print("Starting authentication...\n")
            setup()

    # Get a session with the access token
    resp = requests.get(
        "https://api.github.com/copilot_internal/v2/token",
        headers={
            "authorization": f"token {access_token}",
            "editor-version": "Neovim/0.6.1",
            "editor-plugin-version": "copilot.vim/1.16.0",
            "user-agent": "GithubCopilot/1.155.0",
        },
    )

    if resp.status_code != 200:
        print(f"\n⚠️  Error getting Copilot token: {resp.status_code}")
        print(f"Response: {resp.text}")
        print("\nYour access token may be invalid or expired.")
        print("Removing old token and re-authenticating...\n")
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        setup()
        return get_token()

    # Parse the response json, isolating the token
    resp_json = resp.json()
    token = resp_json.get("token")

    if not token:
        print("\n⚠️  Failed to get Copilot token from response")
        print(f"Response: {resp_json}")
        raise Exception("Failed to obtain Copilot token")


def chat(message):
    global token, messages
    # If the token is None, get a new one
    if token is None:
        get_token()

    messages.append({"content": str(message), "role": "user"})

    try:
        resp = requests.post(
            "https://api.githubcopilot.com/chat/completions",
            headers={
                "authorization": f"Bearer {token}",
                "Editor-Version": "vscode/1.80.1",
            },
            json={
                "intent": False,
                "model": MODEL,
                "temperature": 0,
                "top_p": 1,
                "n": 1,
                "stream": True,
                "messages": messages,
            },
        )
    except requests.exceptions.ConnectionError as e:
        print(f"\n⚠️  Connection error: {e}")
        return ""

    result = ""

    # Parse the response text, splitting it by newlines
    resp_text = resp.text.split("\n")
    for line in resp_text:
        # If the line contains a completion, print it
        if line.startswith("data: {"):
            # Parse the completion from the line as json
            json_completion = json.loads(line[6:])
            try:
                completion = (
                    json_completion.get("choices")[0].get("delta").get("content")
                )
                if completion:
                    result += completion
                else:
                    result += "\n"
            except:
                pass

    messages.append({"content": result, "role": "assistant"})

    if result == "":
        print(f"\n⚠️  Error {resp.status_code}: {resp.text}")
        if resp.status_code == 400 or resp.status_code == 401:
            print(
                f"\nYour token may be invalid. Try deleting {TOKEN_FILE} and re-authenticating."
            )
    return result


# Programmatic API functions for use by api.py


def list_models() -> List[Dict]:
    """Return list of available models in OpenAI format."""
    models = []
    for name, internal_name in MODELS.items():
        models.append(
            {
                "id": name,
                "object": "model",
                "created": 1686935002,
                "owned_by": "freegpt",
            }
        )
    return models


def generate_chat_response(
    messages_list: List[Dict],
    model: str = "freegpt-4",
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> Tuple[str, Dict]:
    """
    Generate a chat response (non-streaming).

    Args:
        messages_list: List of message dicts with 'role' and 'content'
        model: Model name (will be mapped to internal model)
        temperature: Temperature for generation
        max_tokens: Max tokens to generate

    Returns:
        Tuple of (response_text, usage_dict)
    """
    global token

    # Get token if needed
    if token is None:
        get_token()

    # Map model name to internal model
    internal_model = MODELS.get(model, MODEL)

    try:
        resp = requests.post(
            "https://api.githubcopilot.com/chat/completions",
            headers={
                "authorization": f"Bearer {token}",
                "Editor-Version": "vscode/1.80.1",
            },
            json={
                "intent": False,
                "model": internal_model,
                "temperature": temperature,
                "top_p": 1,
                "n": 1,
                "stream": False,
                "messages": messages_list,
            },
        )

        if resp.status_code != 200:
            return f"Error: {resp.status_code}", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

        resp_json = resp.json()

        # Extract the response text
        result = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Extract usage info
        usage = resp_json.get(
            "usage",
            {
                "prompt_tokens": len(json.dumps(messages_list)) // 4,
                "completion_tokens": len(result) // 4,
                "total_tokens": (len(json.dumps(messages_list)) + len(result)) // 4,
            },
        )

        return result, usage

    except Exception as e:
        return f"Error: {str(e)}", {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }


def stream_chat_response(
    messages_list: List[Dict],
    model: str = "freegpt-4",
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> Generator[str, None, None]:
    """
    Generate a chat response (streaming).

    Args:
        messages_list: List of message dicts with 'role' and 'content'
        model: Model name (will be mapped to internal model)
        temperature: Temperature for generation
        max_tokens: Max tokens to generate

    Yields:
        String tokens as they are generated
    """
    global token

    # Get token if needed
    if token is None:
        get_token()

    # Map model name to internal model
    internal_model = MODELS.get(model, MODEL)

    try:
        resp = requests.post(
            "https://api.githubcopilot.com/chat/completions",
            headers={
                "authorization": f"Bearer {token}",
                "Editor-Version": "vscode/1.80.1",
            },
            json={
                "intent": False,
                "model": internal_model,
                "temperature": temperature,
                "top_p": 1,
                "n": 1,
                "stream": True,
                "messages": messages_list,
            },
        )

        # Parse the response text, splitting it by newlines
        resp_text = resp.text.split("\n")
        for line in resp_text:
            # If the line contains a completion, yield it
            if line.startswith("data: {"):
                # Parse the completion from the line as json
                json_completion = json.loads(line[6:])
                try:
                    completion = (
                        json_completion.get("choices")[0].get("delta").get("content")
                    )
                    if completion:
                        yield completion
                except Exception:
                    pass

    except Exception as e:
        yield f"Error: {str(e)}"


def main():
    print("=" * 60)
    print("FreeGPT Chat Interface")
    print("GitHub: https://github.com/hadi2f244/freegpt")
    print("=" * 60)
    print("\nAuthenticating with GitHub Copilot...")
    get_token()
    print("✓ Authentication successful!")
    print("\nYou can now start chatting. Type your message and press Enter.")
    print("(Press Ctrl+C to exit)\n")
    while True:
        try:
            print(chat(input(">>> ")))
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break


if __name__ == "__main__":
    main()

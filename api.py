"""
OpenAI-compatible API server for FreeGPT.

This FastAPI server provides OpenAI-compatible endpoints that wrap the
existing FreeGPT chat functionality from chat.py.
"""

from fastapi import FastAPI, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import os
import time
import uuid
import json
from typing import List, Optional, Dict, Any, Union
from chat import generate_chat_response, stream_chat_response, list_models as get_models

# Try to import token manager, but don't fail if not available
try:
    from token_manager import validate_token

    TOKEN_MANAGER_AVAILABLE = True
except ImportError:
    TOKEN_MANAGER_AVAILABLE = False
    validate_token = None


app = FastAPI(
    title="FreeGPT API",
    description="OpenAI-compatible API for FreeGPT",
    version="1.0.0",
)

# Get API key from environment
API_KEY = os.getenv("FREEGPT_API_KEY") or os.getenv("OPENAI_API_KEY")


def check_auth(auth: Optional[str]) -> bool:
    """
    Validate authorization header.
    Checks both environment variable API key and token file (if available).
    """
    if not auth or not auth.startswith("Bearer "):
        # If no API key is configured anywhere, allow all requests
        if not API_KEY and not TOKEN_MANAGER_AVAILABLE:
            return True
        return False

    token = auth.split(" ", 1)[1]

    # Check environment variable API key
    if API_KEY and token == API_KEY:
        return True

    # Check token manager (token file)
    if TOKEN_MANAGER_AVAILABLE and validate_token:
        return validate_token(token)

    return False


def create_error_response(
    message: str,
    error_type: str = "invalid_request_error",
    param: Optional[str] = None,
    code: Optional[str] = None,
) -> Dict:
    """Create OpenAI-style error response."""
    return {
        "error": {"message": message, "type": error_type, "param": param, "code": code}
    }


# Pydantic models for request/response validation


class Message(BaseModel):
    role: str = Field(
        ..., description="Role of the message sender (system, user, assistant)"
    )
    content: str = Field(..., description="Content of the message")
    name: Optional[str] = Field(None, description="Name of the participant")


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model to use for completion")
    messages: List[Message] = Field(
        ..., description="List of messages in the conversation"
    )
    temperature: Optional[float] = Field(
        1.0, ge=0, le=2, description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        512, ge=1, description="Maximum tokens to generate"
    )
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    top_p: Optional[float] = Field(
        1.0, ge=0, le=1, description="Nucleus sampling parameter"
    )
    n: Optional[int] = Field(1, ge=1, description="Number of completions to generate")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    presence_penalty: Optional[float] = Field(0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(0, ge=-2, le=2)
    user: Optional[str] = Field(None, description="Unique identifier for the user")


class CompletionRequest(BaseModel):
    model: str = Field(..., description="Model to use for completion")
    prompt: Union[str, List[str]] = Field(
        ..., description="Prompt(s) to generate completions for"
    )
    temperature: Optional[float] = Field(
        1.0, ge=0, le=2, description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        512, ge=1, description="Maximum tokens to generate"
    )
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    top_p: Optional[float] = Field(1.0, ge=0, le=1)
    n: Optional[int] = Field(1, ge=1)
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = Field(0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(0, ge=-2, le=2)
    user: Optional[str] = None


class ModerationRequest(BaseModel):
    input: Union[str, List[str]] = Field(..., description="Text to moderate")
    model: Optional[str] = Field(
        "text-moderation-latest", description="Moderation model"
    )


# API Endpoints


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "FreeGPT API Server",
        "version": "1.0.0",
        "endpoints": [
            "/v1/chat/completions",
            "/v1/completions",
            "/v1/models",
            "/v1/models/{model}",
            "/v1/moderations",
        ],
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/v1/chat/completions")
async def chat_completions(
    req: ChatCompletionRequest, authorization: Optional[str] = Header(None)
):
    """
    Create a chat completion (OpenAI-compatible).

    Supports both streaming and non-streaming responses.
    """
    # Check authentication
    if not check_auth(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                "Invalid API key provided", error_type="authentication_error"
            ),
        )

    # Generate unique request ID
    request_id = "chatcmpl-" + uuid.uuid4().hex[:24]
    created_at = int(time.time())

    # Convert messages to dict format
    messages_dict = [{"role": m.role, "content": m.content} for m in req.messages]

    # Handle non-streaming response
    if not req.stream:
        try:
            text, usage = generate_chat_response(
                messages_dict,
                model=req.model,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )

            return {
                "id": request_id,
                "object": "chat.completion",
                "created": created_at,
                "model": req.model,
                "usage": usage,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    f"Error generating completion: {str(e)}", error_type="server_error"
                ),
            )

    # Handle streaming response
    async def generate_stream():
        """Generate streaming response in OpenAI format."""
        try:
            for token in stream_chat_response(
                messages_dict,
                model=req.model,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            ):
                chunk = {
                    "id": request_id,
                    "object": "chat.completion.chunk",
                    "created": created_at,
                    "model": req.model,
                    "choices": [
                        {"index": 0, "delta": {"content": token}, "finish_reason": None}
                    ],
                }
                yield f"data: {json.dumps(chunk)}\n\n"

            # Send final chunk with finish_reason
            final_chunk = {
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": created_at,
                "model": req.model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            error_chunk = {"error": {"message": str(e), "type": "server_error"}}
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/v1/completions")
async def completions(
    req: CompletionRequest, authorization: Optional[str] = Header(None)
):
    """
    Create a text completion (OpenAI-compatible).

    Converts prompt to chat format internally.
    """
    # Check authentication
    if not check_auth(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                "Invalid API key provided", error_type="authentication_error"
            ),
        )

    # Generate unique request ID
    request_id = "cmpl-" + uuid.uuid4().hex[:24]
    created_at = int(time.time())

    # Convert prompt to chat format
    if isinstance(req.prompt, list):
        prompt_text = "\n".join(req.prompt)
    else:
        prompt_text = req.prompt

    messages = [{"role": "user", "content": prompt_text}]

    # Handle non-streaming response
    if not req.stream:
        try:
            text, usage = generate_chat_response(
                messages,
                model=req.model,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )

            return {
                "id": request_id,
                "object": "text_completion",
                "created": created_at,
                "model": req.model,
                "usage": usage,
                "choices": [
                    {
                        "index": 0,
                        "text": text,
                        "finish_reason": "stop",
                        "logprobs": None,
                    }
                ],
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_error_response(
                    f"Error generating completion: {str(e)}", error_type="server_error"
                ),
            )

    # Handle streaming response
    async def generate_stream():
        """Generate streaming response for completions."""
        try:
            for token in stream_chat_response(
                messages,
                model=req.model,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            ):
                chunk = {
                    "id": request_id,
                    "object": "text_completion",
                    "created": created_at,
                    "model": req.model,
                    "choices": [
                        {
                            "index": 0,
                            "text": token,
                            "finish_reason": None,
                            "logprobs": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(chunk)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            error_chunk = {"error": {"message": str(e), "type": "server_error"}}
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/v1/models")
async def list_models(authorization: Optional[str] = Header(None)):
    """
    List available models (OpenAI-compatible).
    """
    # Check authentication
    if not check_auth(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                "Invalid API key provided", error_type="authentication_error"
            ),
        )

    models = get_models()
    return {"object": "list", "data": models}


@app.get("/v1/models/{model}")
async def retrieve_model(model: str, authorization: Optional[str] = Header(None)):
    """
    Retrieve a specific model (OpenAI-compatible).
    """
    # Check authentication
    if not check_auth(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                "Invalid API key provided", error_type="authentication_error"
            ),
        )

    models = get_models()
    for m in models:
        if m["id"] == model:
            return m

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=create_error_response(
            f"Model '{model}' not found", error_type="invalid_request_error"
        ),
    )


@app.post("/v1/moderations")
async def moderations(
    req: ModerationRequest, authorization: Optional[str] = Header(None)
):
    """
    Create a moderation (stub endpoint for OpenAI compatibility).

    Returns a mock response indicating content is safe.
    """
    # Check authentication
    if not check_auth(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=create_error_response(
                "Invalid API key provided", error_type="authentication_error"
            ),
        )

    request_id = "modr-" + uuid.uuid4().hex[:24]

    # Handle both single string and list of strings
    if isinstance(req.input, str):
        inputs = [req.input]
    else:
        inputs = req.input

    results = []
    for _ in inputs:
        results.append(
            {
                "flagged": False,
                "categories": {
                    "sexual": False,
                    "hate": False,
                    "harassment": False,
                    "self-harm": False,
                    "sexual/minors": False,
                    "hate/threatening": False,
                    "violence/graphic": False,
                    "self-harm/intent": False,
                    "self-harm/instructions": False,
                    "harassment/threatening": False,
                    "violence": False,
                },
                "category_scores": {
                    "sexual": 0.0,
                    "hate": 0.0,
                    "harassment": 0.0,
                    "self-harm": 0.0,
                    "sexual/minors": 0.0,
                    "hate/threatening": 0.0,
                    "violence/graphic": 0.0,
                    "self-harm/intent": 0.0,
                    "self-harm/instructions": 0.0,
                    "harassment/threatening": 0.0,
                    "violence": 0.0,
                },
            }
        )

    return {"id": request_id, "model": req.model, "results": results}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            f"Internal server error: {str(exc)}", error_type="server_error"
        ),
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"Starting FreeGPT API server on {host}:{port}")
    if API_KEY:
        print("API key authentication is ENABLED")
    else:
        print(
            "API key authentication is DISABLED (set FREEGPT_API_KEY or OPENAI_API_KEY to enable)"
        )

    uvicorn.run(app, host=host, port=port)

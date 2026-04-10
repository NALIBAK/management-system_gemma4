import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
AI_MODE = os.getenv("AI_MODE", "local")

class AIClientError(Exception):
    pass

def _get_active_config() -> dict:
    """Read the active LLM config from the database, with env var fallback."""
    try:
        from app.db import query
        rows = query("SELECT selected_model, temperature, max_tokens FROM llm_config LIMIT 1")
        if rows:
            return {
                "model": rows[0].get("selected_model") or DEFAULT_MODEL,
                "temperature": float(rows[0].get("temperature") or 0.7),
                "max_tokens": int(rows[0].get("max_tokens") or 2048),
            }
    except Exception:
        pass
    return {"model": DEFAULT_MODEL, "temperature": 0.7, "max_tokens": 2048}

def check_ollama_status():
    """Verify if Ollama is running and accessible."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def check_model_exists(model_name: str) -> bool:
    """Check if a specific model is available in Ollama."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m.get("name") == model_name for m in models)
    except Exception:
        pass
    return False

def generate_response(system_prompt: str, messages: list, tools: list = None, temperature: float = None):
    """
    Generate response from the configured local model via Ollama /api/chat.
    Model is read dynamically from the DB llm_config table so settings changes
    take effect immediately without a server restart.
    Limits context window by strictly taking the last 5 messages + system prompt.
    """
    if AI_MODE != "local":
        return {"success": False, "error": "System strictly configured for Offline AIRA (local mode)."}

    # Load config from DB each call — lightweight single-row query
    cfg = _get_active_config()
    model = cfg["model"]
    temp = temperature if temperature is not None else cfg["temperature"]

    # Validate model exists to give a helpful error instead of a cryptic 404
    if not check_model_exists(model):
        available = []
        try:
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
            available = [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        hint = f"Available: {', '.join(available)}" if available else "Run `ollama list` to see available models."
        return {
            "success": False,
            "error": f"Model '{model}' not found in Ollama. {hint}"
        }

    # Slide window to prevent OOM on resource-constrained devices
    chat_history = messages[-5:]

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt}
        ] + chat_history,
        "stream": False,
        "options": {
            "temperature": temp,
            "num_ctx": 4096  # Cap token block limit to stay within memory
        }
    }

    if tools:
        # Convert to Ollama native tool format
        payload["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("inputSchema", t.get("parameters", {}))
                }
            }
            for t in tools
        ]

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        reply = data.get("message", {})

        # Check if model requested a tool call
        if "tool_calls" in reply and reply["tool_calls"]:
            return {
                "success": True,
                "message": reply.get("content", ""),
                "tool_calls": [
                    {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"]
                    }
                    for tc in reply["tool_calls"]
                ]
            }

        return {"success": True, "message": reply.get("content", "")}

    except requests.exceptions.Timeout:
        return {"success": False, "error": f"Model '{model}' took too long to respond. (Timeout 60s)"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to Ollama. Is it running at " + OLLAMA_HOST + "?"}
    except Exception as e:
        return {"success": False, "error": str(e)}

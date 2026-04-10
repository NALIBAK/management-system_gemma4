import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
AI_MODE = os.getenv("AI_MODE", "local")

class AIClientError(Exception):
    pass

def check_ollama_status():
    """Verify if Ollama is running and accessible."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def generate_response(system_prompt: str, messages: list, tools: list = None, temperature: float = 0.7):
    """
    Generate response from Gemma 4 via Ollama using the /api/chat endpoint.
    Limits context window by strictly taking the last 5 messages + system prompt.
    """
    if AI_MODE != "local":
        return {"success": False, "error": "System strictly configured for Offline AIRA (local mode)."}

    # Slide window to prevent OOM on low-resource devices (like Samsung Galaxy S22 via Termux)
    # We only take the last 5 messages from the history
    chat_history = messages[-5:]

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt}
        ] + chat_history,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": 4096 # Cap token block limit to stay well within resources
        }
    }
    
    if tools:
        # Convert standard tools format into Ollama format if necessary, 
        # Ollama supports native format: [{"type": "function", "function": {...}}]
        formatted_tools = []
        for t in tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("inputSchema", t.get("parameters", {}))
                }
            })
        payload["tools"] = formatted_tools

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30 # Timeout aggressively, this is an agent loop
        )
        response.raise_for_status()
        data = response.json()
        
        reply = data.get("message", {})
        
        # Check if model requested a tool call
        if "tool_calls" in reply and reply["tool_calls"]:
            return {
                "success": True, 
                "message": reply.get("content", ""),
                "tool_calls": [ {
                    "name": tc["function"]["name"],
                    "arguments": tc["function"]["arguments"]
                } for tc in reply["tool_calls"]]
            }
            
        return {"success": True, "message": reply.get("content", "")}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "AI Model took too long to respond. (Timeout)"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to local AI. Is Ollama running?"}
    except Exception as e:
        return {"success": False, "error": str(e)}

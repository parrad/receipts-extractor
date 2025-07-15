import requests
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

class OllamaClient:
    def __init__(self, host=OLLAMA_HOST, model=OLLAMA_MODEL):
        self.host = host.rstrip("/")
        self.model = model

    def generate(self, prompt, system=None, context=None):
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["response"]

    def mcp_chat(self, messages, context=None):
        """Send a chat using Model Context Protocol (MCP) if supported by the model."""
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        if context:
            payload["context"] = context
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["message"]["content"]

import os

from ollama import Client as OllamaClient


def get_ollama_client() -> OllamaClient:
    return OllamaClient(host=os.getenv("OLLAMA_URL", "http://localhost:11434"))

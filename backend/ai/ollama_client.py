import requests
from typing import Any, Dict
from backend.core.logging_config import setup_logging
import subprocess
import shlex

logger = setup_logging()

class OllamaClient:
    """Cliente mínimo para Ollama local (HTTP API).

    Requiere Ollama corriendo localmente. Por defecto Ollama expone
    su API en http://localhost:11434.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def generate(self, model: str, prompt: str, max_tokens: int = 512) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens}
        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.warning("HTTP Ollama failed, falling back to CLI: %s", e)
            # Fallback: use `ollama run` CLI with JSON format
            try:
                cmd = ["ollama", "run", model, prompt, "--format", "json"]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if proc.returncode != 0:
                    logger.error("ollama CLI failed: %s", proc.stderr)
                    raise
                # CLI returns JSON text
                import json as _json
                return _json.loads(proc.stdout)
            except Exception as e2:
                logger.exception("Error usando ollama CLI")
                raise

    def generate_json(self, model: str, prompt: str, max_tokens: int = 512) -> Dict[str, Any]:
        """Llama a Ollama esperando que la salida sea JSON. Devuelve dict.

        Lanza ValueError si no retorna JSON parseable.
        """
        data = self.generate(model, prompt, max_tokens=max_tokens)
        # Ollama devuelve estructura en 'output' o 'choices' según versión; intentamos localizar JSON
        text = None
        if isinstance(data, dict):
            if "output" in data and isinstance(data["output"], list):
                text = "".join(s for s in data["output"] if isinstance(s, str))
            elif "choices" in data and isinstance(data["choices"], list):
                text = "".join(c.get("message", {}).get("content", "") if isinstance(c, dict) else str(c) for c in data["choices"]) 
        if not text:
            # Fallback: string representation
            text = str(data)

        # Intentar parsear JSON desde el texto
        import json
        try:
            return json.loads(text)
        except Exception as e:
            logger.error("Respuesta de Ollama no es JSON parseable", exc_info=True)
            raise ValueError(f"Respuesta de Ollama no contiene JSON parseable: {e}\nRaw: {text}")

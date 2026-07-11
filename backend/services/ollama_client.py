"""
OllamaClient
------------
Abstracción del cliente HTTP hacia el servicio Ollama.

Se mantiene como un servicio independiente (no hardcodeado dentro de
LLMStrategy) para que:
    1. La URL/host y el modelo se configuren 100% por variables de
       entorno (.env), nunca quemados en el código.
    2. Pueda sustituirse fácilmente por otro proveedor LLM sin tocar
       LLMStrategy (cumple con el espíritu de bajo acoplamiento que
       pide el patrón Strategy).
"""

import os
import requests


class OllamaClient:
    """Cliente mínimo para el endpoint /api/generate de Ollama."""

    def __init__(self) -> None:
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        # Timeout configurable para evitar bloqueos indefinidos en I/O.
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30"))

    def generate(self, system_prompt: str, prompt: str) -> str:
        """
        Envía una petición de generación a Ollama y devuelve el texto
        de respuesta (ya sin streaming, una sola respuesta completa).

        Esta llamada es la operación "I/O-Bound" referida en la guía:
        el hilo que la ejecuta queda esperando la red/disco del
        servicio Ollama, por lo que NO retiene el GIL de forma activa
        durante la espera, permitiendo que otros hilos del
        ThreadPoolExecutor avancen en paralelo.
        """
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        }
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.exceptions.RequestException as exc:
            # Si Ollama no está disponible, devolvemos una señal clara
            # en vez de tumbar el hilo completo.
            print(f"[OllamaClient] Error de conexión con Ollama: {exc}")
            return ""

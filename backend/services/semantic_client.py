"""
SemanticClient
--------------
Cliente HTTP del backend Flask hacia el microservicio de análisis
semántico implementado en Java / Spring Boot.

Responsabilidad única: enviar el AST JSON al servicio Java y devolver
la respuesta semántica. No contiene ninguna lógica semántica propia.

Si el servicio Java no está disponible (error de conexión, timeout),
el cliente devuelve None y el pipeline continúa con un aviso en consola,
de modo que la fase léxica y sintáctica siguen siendo funcionales.
"""

import os
import requests


class SemanticClient:
    """Cliente HTTP hacia el microservicio semántico Java."""

    def __init__(self) -> None:
        # URL del servicio Java, leída de .env — nunca hardcodeada.
        # Dentro de Docker, el nombre de servicio es "semantic".
        self.base_url = os.getenv("SEMANTIC_SERVICE_URL", "http://localhost:8080")
        self.timeout  = float(os.getenv("SEMANTIC_TIMEOUT_SECONDS", "30"))

    def analizar(self, entrada: str, arbol_sintactico: dict) -> dict | None:
        """
        Envía el AST al microservicio Java y devuelve el resultado semántico.

        Args:
            entrada:           cadena original del usuario.
            arbol_sintactico:  AST JSON producido por el parser Python.

        Returns:
            dict con { valido, errores, tablaSimbolos, tiempoMs }
            o None si el servicio no está disponible.
        """
        url = f"{self.base_url}/semantic/analyze"
        payload = {
            "entrada": entrada,
            "arbol_sintactico": arbol_sintactico,
        }

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            resultado = response.json()
            print(f"[SemanticClient] Respuesta Java: valido={resultado.get('valido')} "
                  f"errores={len(resultado.get('errores', []))}")
            return resultado
        except requests.exceptions.ConnectionError:
            print(f"[SemanticClient] Servicio semántico Java no disponible en {url}")
            return None
        except requests.exceptions.Timeout:
            print(f"[SemanticClient] Timeout esperando al servicio semántico Java")
            return None
        except requests.exceptions.RequestException as exc:
            print(f"[SemanticClient] Error HTTP al llamar al servicio semántico: {exc}")
            return None

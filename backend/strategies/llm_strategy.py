"""
LLMStrategy
-----------
Implementa la fase de Análisis Léxico "blanda" (semántica/NLP) del
DSL mediante un LLM (vía Ollama). Cumple el rol de "Tokenizador
Normalizador" para el dominio elegido (Contexto 1: NLP-Math).

Recibe fragmentos de texto en lenguaje natural (ya identificados como
TEXTO_LN por el AutomataStrategy) y los traduce a tokens formales del
compilador, p. ej.:
    "más"        -> OP_SUMA
    "es igual a" -> OP_ASIGNACION
    "menos"      -> OP_RESTA

Si el LLM devuelve un token fuera del catálogo oficial, se marca como
DESCONOCIDO en vez de aceptarlo ciegamente, delegando la decisión de
qué hacer con él a una fase posterior (parser / manejo de errores),
tal como exige la pregunta de control 2 de la guía.
"""

import time
import threading
import json
import re

from models.token import Token, TipoToken, TokenOrigen
from strategies.base_strategy import TokenizerStrategy
from services.ollama_client import OllamaClient


# Catálogo oficial de tokens semánticos que el LLM puede emitir.
# Cualquier salida fuera de este conjunto se reclasifica como DESCONOCIDO.
_TOKENS_SEMANTICOS_VALIDOS = {
    "OP_SUMA",
    "OP_RESTA",
    "OP_ASIGNACION",
}

_SYSTEM_PROMPT = """Eres un Tokenizador Normalizador para un compilador de \
Ecuaciones de Primer Grado (DSL NLP-Math). Tu única tarea es clasificar una \
frase corta en español/inglés en EXACTAMENTE uno de estos tokens oficiales:

- OP_SUMA: para frases que indican suma (ej: "más", "sumado a", "plus").
- OP_RESTA: para frases que indican resta (ej: "menos", "restado de", "minus").
- OP_ASIGNACION: para frases que indican igualdad/asignación \
(ej: "es igual a", "equivale a", "equals").
- DESCONOCIDO: si la frase no corresponde a ninguno de los anteriores.

Responde ÚNICAMENTE con un objeto JSON de una sola línea, sin texto adicional, \
sin markdown, con el formato exacto:
{"token": "OP_SUMA"}

No expliques tu razonamiento. No agregues comentarios. Solo el JSON.
"""


class LLMStrategy(TokenizerStrategy):
    """Estrategia de tokenización semántica apoyada en un LLM (Ollama)."""

    def __init__(self, ollama_client: OllamaClient | None = None) -> None:
        # Inyección de dependencia: permite testear con un cliente mock
        # sin modificar esta clase (bajo acoplamiento, principio Strategy).
        self.cliente = ollama_client or OllamaClient()

    def tokenize(self, fragmento: str, posicion: int = 0) -> list[Token]:
        """
        Clasifica un único fragmento de texto natural mediante el LLM.

        Se ejecuta normalmente DENTRO de un hilo del ThreadPoolExecutor
        (ver lexer_engine.py), por lo que aquí registramos el nombre del
        hilo actual como evidencia de concurrencia en consola.
        """
        hilo_actual = threading.current_thread().name
        inicio = time.perf_counter()

        respuesta_cruda = self.cliente.generate(_SYSTEM_PROMPT, fragmento)
        tipo_token, valor = self._parsear_respuesta(respuesta_cruda, fragmento)

        fin = time.perf_counter()
        tiempo_ms = (fin - inicio) * 1000

        print(
            f"[LLM][{hilo_actual}] Fragmento='{fragmento}' -> {tipo_token.value} "
            f"({tiempo_ms:.1f} ms)"
        )

        token = Token(
            tipo=tipo_token,
            lexema=fragmento,
            valor=valor,
            origen=TokenOrigen.LLM,
            posicion=posicion,
            hilo=hilo_actual,
            tiempo_ms=tiempo_ms,
        )
        return [token]

    def _parsear_respuesta(self, respuesta_cruda: str, fragmento_original: str) -> tuple[TipoToken, str]:
        """
        Parsea de forma defensiva la respuesta del LLM. Si no es JSON
        válido, o el token no pertenece al catálogo oficial, se degrada
        a DESCONOCIDO en vez de fallar silenciosamente.
        """
        if not respuesta_cruda:
            return TipoToken.DESCONOCIDO, fragmento_original

        # Extrae el primer bloque JSON presente en la respuesta, por si
        # el modelo agrega texto extra pese a las instrucciones.
        match = re.search(r"\{.*?\}", respuesta_cruda, re.DOTALL)
        texto_json = match.group() if match else respuesta_cruda

        try:
            datos = json.loads(texto_json)
            token_str = str(datos.get("token", "")).strip().upper()
        except (json.JSONDecodeError, AttributeError):
            print(f"[LLM] Respuesta no parseable como JSON: '{respuesta_cruda}'")
            return TipoToken.DESCONOCIDO, fragmento_original

        if token_str not in _TOKENS_SEMANTICOS_VALIDOS:
            return TipoToken.DESCONOCIDO, fragmento_original

        try:
            tipo = TipoToken(token_str)
        except ValueError:
            tipo = TipoToken.DESCONOCIDO

        valor_simbolico = {
            "OP_SUMA": "+",
            "OP_RESTA": "-",
            "OP_ASIGNACION": "=",
        }.get(token_str, fragmento_original)

        return tipo, valor_simbolico

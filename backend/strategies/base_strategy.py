"""
Interfaz Strategy
-----------------
Define el contrato que deben cumplir TODAS las estrategias de
tokenización (AutomataStrategy y LLMStrategy).

Este es el corazón del patrón de diseño Strategy pedido en la guía:
desacopla el "cómo se tokeniza" (AFD vs LLM) del "quién lo usa"
(el motor léxico / LexerEngine). Así, cambiar de motor LLM
(p. ej. de Llama-3 a otro modelo) o modificar el AFD no impacta
al resto del sistema -> alta mantenibilidad (ver pregunta de
control 4 de la guía).
"""

from abc import ABC, abstractmethod
from models.token import Token


class TokenizerStrategy(ABC):
    """Contrato común para cualquier estrategia de tokenización."""

    @abstractmethod
    def tokenize(self, fragmento: str, posicion: int = 0) -> list[Token]:
        """
        Tokeniza un fragmento de texto y devuelve una lista de Token.

        Args:
            fragmento: porción de texto a analizar.
            posicion: índice de inicio del fragmento en la cadena original
                      (para trazabilidad).

        Returns:
            Lista de tokens reconocidos (puede ser vacía si el
            fragmento no aporta tokens válidos para esta estrategia).
        """
        raise NotImplementedError

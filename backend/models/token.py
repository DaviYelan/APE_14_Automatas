"""
Modelo de datos: Token
-----------------------
Representa una unidad léxica reconocida en el flujo de entrada,
ya sea por el AFD (expresiones regulares) o por el LLM (PLN).

Este modelo es el "contrato" común que usan ambas estrategias
(AutomataStrategy y LLMStrategy) para que el resto del sistema
(Parser, Reporte, API) no necesite saber de dónde vino cada token.
"""

from dataclasses import dataclass, field
from enum import Enum


class TokenOrigen(str, Enum):
    """Indica qué motor generó el token: el AFD (regex) o el LLM (NLP)."""
    AFD = "AFD"
    LLM = "LLM"


class TipoToken(str, Enum):
    """
    Catálogo OFICIAL de tokens del DSL de Ecuaciones de Primer Grado.

    Diseño de tokens (paso 2 de la guía):
        VAR              -> identificador/variable, ej: x, 2x
        NUMERO           -> entero o decimal, ej: 13, 3.5
        OP_SUMA          -> "más", "+"
        OP_RESTA         -> "menos", "-"
        OP_ASIGNACION    -> "es igual a", "="
        TEXTO_LN         -> fragmento de lenguaje natural no clasificado
                             aún (input crudo para el LLM)
        UNKNOWN          -> carácter o símbolo no reconocido por el lenguaje
                             (error léxico: ej. ".", "@", "?")
        DESCONOCIDO      -> el LLM no pudo clasificar el fragmento de texto natural
    """
    VAR = "VAR"
    NUMERO = "NUMERO"
    OP_SUMA = "OP_SUMA"
    OP_RESTA = "OP_RESTA"
    OP_ASIGNACION = "OP_ASIGNACION"
    TEXTO_LN = "TEXTO_LN"
    UNKNOWN = "UNKNOWN"
    DESCONOCIDO = "DESCONOCIDO"


@dataclass
class ErrorSintactico:
    """
    Representa un error sintáctico detectado durante el análisis.
    Ocurre cuando la secuencia de tokens no se ajusta a las reglas
    de producción de la gramática del DSL.

    Ejemplo: "2x es igual a" (falta la expresión derecha)
             "2x más más 5 es igual a 13" (dos operadores consecutivos)
    """
    fase: str       # Siempre "sintactico"
    token: str      # Lexema del token que causó el error (o "EOF")
    esperado: str   # Qué se esperaba encontrar según la gramática
    causa: str      # Descripción del problema en lenguaje natural
    posicion: int   # Índice en la cadena original

    def to_dict(self) -> dict:
        return {
            "fase": self.fase,
            "token": self.token,
            "esperado": self.esperado,
            "causa": self.causa,
            "posicion": self.posicion,
        }


@dataclass
class ErrorLexico:
    """
    Representa un error léxico detectado durante el análisis.
    Un error léxico ocurre cuando el AFD encuentra un carácter o símbolo
    que no pertenece al alfabeto definido para el lenguaje del DSL.
    """
    fase: str           # Siempre "lexical" para errores léxicos
    token: str          # El lexema que causó el error
    causa: str          # Descripción del problema
    sugerencia: str     # Acción recomendada al usuario

    def to_dict(self) -> dict:
        return {
            "fase": self.fase,
            "token": self.token,
            "causa": self.causa,
            "sugerencia": self.sugerencia,
        }


@dataclass
class Token:
    """Unidad léxica resultante del análisis."""
    tipo: TipoToken
    lexema: str                         # Texto original tal como apareció en la entrada
    valor: str | float | None = None    # Valor normalizado (ej. 2x -> 2.0, "más" -> "+")
    origen: TokenOrigen = TokenOrigen.AFD
    posicion: int = 0                   # Índice de inicio en la cadena original
    hilo: str = field(default="main")   # Nombre del hilo (evidencia de concurrencia)
    tiempo_ms: float = 0.0              # Tiempo de procesamiento de este token

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo.value,
            "lexema": self.lexema,
            "valor": self.valor,
            # "fuente" es el nombre que usa la convención del proyecto
            # (equivalente a "origen"), se expone con ambos nombres para
            # compatibilidad con el frontend y con Insomnia.
            "fuente": self.origen.value,
            "origen": self.origen.value,
            "posicion": self.posicion,
            "hilo": self.hilo,
            "tiempo_ms": round(self.tiempo_ms, 3),
        }

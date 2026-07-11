"""
ParserStrategy — Análisis Sintáctico Descendente Recursivo
----------------------------------------------------------
Implementa la fase de Análisis Sintáctico para el DSL de Ecuaciones
de Primer Grado mediante un parser LL(1) descendente recursivo.

GRAMÁTICA FORMAL del DSL (BNF):
─────────────────────────────────────────────────────────────────
    ecuacion   → expresion  OP_ASIGNACION  expresion
    expresion  → termino  ( (OP_SUMA | OP_RESTA)  termino )*
    termino    → NUMERO  VAR        # coeficiente·variable ej: 2x
               | NUMERO             # número solo           ej: 13
               | VAR                # variable sola         ej: x
─────────────────────────────────────────────────────────────────

El parser recibe la lista de tokens ya resuelta por LexerEngine (AFD
+ LLM) y produce un Árbol de Sintaxis Abstracta (AST) en forma de
diccionario JSON anidado, o una lista de ErrorSintactico si la entrada
no cumple la gramática.

Nodos del AST:
    ECUACION     { izq, op, der }
    EXPRESION    { terminos: [TERMINO | BINOP] }
    BINOP        { op, izq, der }
    TERMINO      { coeficiente?, variable?, valor }
    NUMERO       { valor }
    VAR          { nombre }
"""

import time
from models.token import Token, TipoToken, ErrorSintactico


# ─────────────────────────────────────────────────────────────────
# Tipos de nodo del AST (constantes de cadena, no Enum, para
# que se serialicen directamente a JSON sin conversión extra).
# ─────────────────────────────────────────────────────────────────
NODO_ECUACION  = "ECUACION"
NODO_EXPRESION = "EXPRESION"
NODO_BINOP     = "BINOP"
NODO_TERMINO   = "TERMINO"
NODO_NUMERO    = "NUMERO"
NODO_VAR       = "VAR"


class ParserStrategy:
    """
    Parser Descendente Recursivo (LL(1)) para el DSL NLP-Math.

    Uso:
        parser = ParserStrategy()
        arbol, errores, tiempo_ms = parser.parsear(tokens)
    """

    def parsear(
        self, tokens: list[Token]
    ) -> tuple[dict | None, list[ErrorSintactico], float]:
        """
        Punto de entrada del análisis sintáctico.

        Args:
            tokens: flujo de tokens producido por LexerEngine
                    (solo se usan los que tienen tipo conocido y
                     diferente de UNKNOWN/DESCONOCIDO).

        Returns:
            (arbol, errores, tiempo_ms)
              arbol    : dict con el AST completo, o None si hay errores.
              errores  : lista de ErrorSintactico (vacía si es válido).
              tiempo_ms: tiempo empleado en el parsing (float, ms).
        """
        inicio = time.perf_counter()

        # Filtramos tokens que no aportan información sintáctica.
        # TEXTO_LN no debería llegar aquí (ya fue resuelto por el LLM),
        # UNKNOWN y DESCONOCIDO son errores léxicos, no sintácticos.
        tokens_validos = [
            t for t in tokens
            if t.tipo not in (
                TipoToken.TEXTO_LN,
                TipoToken.UNKNOWN,
                TipoToken.DESCONOCIDO,
            )
        ]

        print(f"[Parser] Iniciando análisis sintáctico con "
              f"{len(tokens_validos)} tokens válidos")

        self._tokens  = tokens_validos
        self._pos     = 0          # cursor: índice del token actual
        self._errores: list[ErrorSintactico] = []

        arbol = self._parse_ecuacion()

        # Si hay tokens sin consumir al final, es un error sintáctico
        if arbol is not None and self._pos < len(self._tokens):
            tok_extra = self._token_actual()
            self._error(
                esperado="fin de expresión",
                causa=f"Token inesperado '{tok_extra.lexema}' después de una "
                      f"ecuación completa. La gramática no acepta más tokens.",
            )
            arbol = None

        fin = time.perf_counter()
        tiempo_ms = (fin - inicio) * 1000

        if self._errores:
            arbol = None  # árbol inválido si hay cualquier error sintáctico
            print(f"[Parser] Análisis sintáctico FALLIDO — "
                  f"{len(self._errores)} error(es) en {tiempo_ms:.3f} ms")
        else:
            print(f"[Parser] Análisis sintáctico EXITOSO en {tiempo_ms:.3f} ms")

        return arbol, self._errores, tiempo_ms

    # ──────────────────────────────────────────────────────────────
    # Reglas de producción (una función por no-terminal)
    # ──────────────────────────────────────────────────────────────

    def _parse_ecuacion(self) -> dict | None:
        """
        Regla: ecuacion → expresion  OP_ASIGNACION  expresion

        Una ecuación válida tiene exactamente:
          <expresión izquierda>  OP_ASIGNACION  <expresión derecha>
        """
        # 1. Expresión izquierda
        izq = self._parse_expresion()
        if izq is None:
            return None

        # 2. Operador de asignación / igualdad
        if not self._verificar(TipoToken.OP_ASIGNACION):
            self._error(
                esperado="OP_ASIGNACION ('es igual a' / '=')",
                causa="Se esperaba un operador de igualdad ('es igual a' o '=') "
                      "entre la expresión izquierda y la derecha.",
            )
            return None
        op_token = self._consumir()

        # 3. Expresión derecha
        der = self._parse_expresion()
        if der is None:
            self._error(
                esperado="expresión (NUMERO, VAR o NUMERO VAR)",
                causa="Falta la expresión del lado derecho del signo de igualdad.",
            )
            return None

        return {
            "nodo": NODO_ECUACION,
            "operador": op_token.lexema,
            "izquierda": izq,
            "derecha": der,
        }

    def _parse_expresion(self) -> dict | None:
        """
        Regla: expresion → termino ( (OP_SUMA | OP_RESTA) termino )*

        Una expresión es un término seguido de cero o más pares
        (operador, término). Esto maneja sumas y restas encadenadas.
        Ej: "2x + 5",  "x - 3 + y"
        """
        izq = self._parse_termino()
        if izq is None:
            return None

        # Mientras haya operadores aritméticos, seguimos consumiendo
        while self._verificar(TipoToken.OP_SUMA) or \
              self._verificar(TipoToken.OP_RESTA):
            op_token = self._consumir()
            der = self._parse_termino()
            if der is None:
                self._error(
                    esperado="término (NUMERO, VAR o NUMERO VAR)",
                    causa=f"Después del operador '{op_token.lexema}' se esperaba "
                          f"un término (número o variable).",
                )
                return None
            # Construimos un nodo binario que agrupa izq OP der
            izq = {
                "nodo": NODO_BINOP,
                "operador": op_token.lexema,
                "izquierda": izq,
                "derecha": der,
            }

        return izq

    def _parse_termino(self) -> dict | None:
        """
        Regla: termino → NUMERO VAR   (coeficiente × variable)
                        | NUMERO       (número solo)
                        | VAR          (variable sola)

        LOOKAHEAD de 1 token para elegir la producción correcta:
          - Si el token actual es NUMERO y el siguiente es VAR  → coeficiente·var
          - Si el token actual es NUMERO solo                   → número
          - Si el token actual es VAR                           → variable
          - Cualquier otro token                                → error
        """
        if self._verificar(TipoToken.NUMERO):
            num_token = self._consumir()

            # ¿El siguiente token es una variable? → término coeficiente·var
            if self._verificar(TipoToken.VAR):
                var_token = self._consumir()
                coef = num_token.valor   # float
                nombre_var = var_token.lexema
                return {
                    "nodo": NODO_TERMINO,
                    "tipo": "coeficiente_variable",
                    "coeficiente": coef,
                    "variable": nombre_var,
                    # valor simbólico para mostrar en el árbol
                    "representacion": f"{coef}·{nombre_var}",
                }

            # Solo número
            return {
                "nodo": NODO_NUMERO,
                "valor": num_token.valor,
                "lexema": num_token.lexema,
            }

        if self._verificar(TipoToken.VAR):
            var_token = self._consumir()
            return {
                "nodo": NODO_VAR,
                "nombre": var_token.lexema,
                "valor": var_token.valor,
            }

        # No encontramos ningún término válido
        tok = self._token_actual()
        if tok is None:
            self._error(
                esperado="término (NUMERO o VAR)",
                causa="Se llegó al final de la entrada esperando un término.",
            )
        else:
            self._error(
                esperado="término (NUMERO o VAR)",
                causa=f"Token '{tok.lexema}' (tipo {tok.tipo.value}) no es un "
                      f"término válido. Se esperaba un número o una variable.",
            )
        return None

    # ──────────────────────────────────────────────────────────────
    # Utilidades del parser
    # ──────────────────────────────────────────────────────────────

    def _token_actual(self) -> Token | None:
        """Devuelve el token en la posición actual sin consumirlo (peek)."""
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _verificar(self, tipo: TipoToken) -> bool:
        """True si el token actual es del tipo indicado (sin consumir)."""
        tok = self._token_actual()
        return tok is not None and tok.tipo == tipo

    def _consumir(self) -> Token:
        """Consume el token actual y avanza el cursor."""
        tok = self._tokens[self._pos]
        self._pos += 1
        print(f"[Parser] Consumido: [{tok.tipo.value}] '{tok.lexema}'")
        return tok

    def _error(self, esperado: str, causa: str) -> None:
        """Registra un error sintáctico con contexto completo."""
        tok = self._token_actual()
        lexema   = tok.lexema   if tok else "EOF"
        posicion = tok.posicion if tok else -1

        error = ErrorSintactico(
            fase="sintactico",
            token=lexema,
            esperado=esperado,
            causa=causa,
            posicion=posicion,
        )
        self._errores.append(error)
        print(f"[Parser] ERROR SINTÁCTICO: token='{lexema}' "
              f"esperado='{esperado}' | {causa}")

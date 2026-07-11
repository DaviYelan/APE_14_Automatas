"""
AutomataStrategy
-----------------
Implementa la fase de Análisis Léxico "dura" (formal) del DSL
mediante un Autómata Finito Determinista (AFD) simulado con
expresiones regulares (módulo `re` de Python).

Responsable de reconocer los tokens "puros" / simbólicos:
    - VAR            -> 2x, x, y3 (identificador con o sin coeficiente)
    - NUMERO         -> 13, 3.14
    - OP_SUMA        -> '+'
    - OP_RESTA       -> '-'
    - OP_ASIGNACION  -> '='

Todo lo que NO coincide con estos patrones (palabras en español/inglés
como "más", "es igual a", etc.) se etiqueta como TEXTO_LN y se delega
posteriormente al LLMStrategy. Esta separación es exactamente el
"desafío léxico" descrito en el Contexto 1 de la guía.
"""

import re
import time
import threading

from models.token import Token, TipoToken, TokenOrigen, ErrorLexico
from strategies.base_strategy import TokenizerStrategy


class AutomataStrategy(TokenizerStrategy):
    """
    AFD (simulado vía regex) para los tokens formales/simbólicos
    del compilador de Ecuaciones de Primer Grado.
    """

    # Especificación de tokens en orden de prioridad (como un AFD real:
    # el orden importa para evitar ambigüedades, p. ej. NUMERO antes
    # que un identificador suelto).
    # NOTA de diseño (AFD): una "variable" matemática válida en este DSL
    # es UNA sola letra (a-z), opcionalmente precedida por un coeficiente
    # numérico (ej. 2x, x, y3 no es válido como variable -> y3 sería
    # interpretado como identificador de una letra "y" seguida de dígito
    # solo si el dígito va ANTES). Restringimos a "coeficiente + letra
    # única" para evitar falsos positivos con palabras españolas como
    # "más", "es", "igual", que también empiezan con letras.
    _ESPECIFICACION_TOKENS: list[tuple[TipoToken, str]] = [
        (TipoToken.NUMERO, r"\d+(\.\d+)?"),                 # 13, 3.14 (probar antes que VAR)
        (TipoToken.VAR, r"(?<![a-zA-ZáéíóúÁÉÍÓÚñÑ])[a-zA-Z](?![a-zA-ZáéíóúÁÉÍÓÚñÑ])"),  # x, y -> letra aislada
        (TipoToken.OP_SUMA, r"\+"),
        (TipoToken.OP_RESTA, r"-"),
        (TipoToken.OP_ASIGNACION, r"="),
    ]

    # Palabras conectoras de una sola letra que, en español, casi nunca
    # representan una variable matemática real dentro de este DSL
    # (ej. "a" en "es igual a"). Se usan para des-ambiguar en la fase
    # de post-procesamiento, ya que un AFD basado en regex puro no
    # puede resolver esta ambigüedad léxica sin contexto adicional.
    _CONECTORES_UNA_LETRA = {"a", "e", "y", "o"}

    def __init__(self) -> None:
        # Compilamos un único patrón maestro combinando todos los
        # sub-patrones con grupos nombrados. Esto simula el comportamiento
        # de un AFD que, en cada estado, decide la siguiente transición
        # según el carácter actual. El orden importa: NUMERO antes que
        # VAR para que "2x" se reconozca como NUMERO(2) seguido de
        # VAR(x), y las palabras completas (>=2 letras seguidas) caigan
        # en TEXTO_LN en vez de en VAR.
        partes = []
        for tipo, patron in self._ESPECIFICACION_TOKENS:
            partes.append(f"(?P<{tipo.value}>{patron})")
        # Palabras completas en español/inglés (2+ letras juntas) ->
        # fragmento de lenguaje natural para el LLM.
        partes.append(
            r"(?P<TEXTO_LN>[a-zA-ZáéíóúÁÉÍÓÚñÑ]{2,}"
            r"(?:\s+[a-zA-ZáéíóúÁÉÍÓÚñÑ]{2,}){0,5})"
        )
        partes.append(r"(?P<WS>\s+)")  # espacios en blanco (se descartan)
        # Catch-all: cualquier carácter que NO haya sido reconocido por
        # ningún patrón anterior es un error léxico -> token UNKNOWN.
        # Esto incluye: ".", "@", "?", "#", "$", ";", etc.
        partes.append(r"(?P<UNKNOWN>.)")
        self._regex_maestro = re.compile("|".join(partes))

    def tokenize(self, fragmento: str, posicion: int = 0) -> tuple[list[Token], list[ErrorLexico]]:
        """
        Recorre el AFD carácter por carácter (vía el motor de regex,
        que internamente implementa la simulación de estados) y separa:
          - Tokens simbólicos puros (VAR, NUMERO, operadores)
          - Fragmentos de lenguaje natural (TEXTO_LN) para el LLM
          - Caracteres inválidos (UNKNOWN) -> errores léxicos con
            descripción de causa y sugerencia de corrección.

        Returns:
            Tupla (tokens, errores_lexicos).
        """
        hilo_actual = threading.current_thread().name
        inicio = time.perf_counter()

        tokens: list[Token] = []
        errores: list[ErrorLexico] = []

        for match in self._regex_maestro.finditer(fragmento):
            tipo_str = match.lastgroup
            lexema = match.group()
            pos_abs = posicion + match.start()

            if tipo_str == "WS":
                continue  # los espacios no generan token

            # --- Error léxico: carácter no pertenece al alfabeto del DSL ---
            if tipo_str == "UNKNOWN":
                # Registramos el token UNKNOWN para mostrarlo en el flujo
                tokens.append(Token(
                    tipo=TipoToken.UNKNOWN,
                    lexema=lexema,
                    valor=lexema,
                    origen=TokenOrigen.AFD,
                    posicion=pos_abs,
                    hilo=hilo_actual,
                ))
                # Y generamos el error léxico con contexto y sugerencia
                errores.append(ErrorLexico(
                    fase="lexical",
                    token=lexema,
                    causa=f"El token '{lexema}' no es válido en el lenguaje.",
                    sugerencia=f"Elimine el token inválido '{lexema}' de la expresión.",
                ))
                print(f"[AFD][{hilo_actual}] ERROR LÉXICO: carácter '{lexema}' "
                      f"no reconocido en posición {pos_abs}")
                continue

            # --- Tokens válidos ---
            if tipo_str == "TEXTO_LN":
                tipo = TipoToken.TEXTO_LN
                valor = lexema.strip().lower()
            elif tipo_str == TipoToken.VAR.value:
                tipo = TipoToken.VAR
                valor = lexema
            elif tipo_str == TipoToken.NUMERO.value:
                tipo = TipoToken.NUMERO
                valor = float(lexema)
            elif tipo_str == TipoToken.OP_SUMA.value:
                tipo = TipoToken.OP_SUMA
                valor = "+"
            elif tipo_str == TipoToken.OP_RESTA.value:
                tipo = TipoToken.OP_RESTA
                valor = "-"
            elif tipo_str == TipoToken.OP_ASIGNACION.value:
                tipo = TipoToken.OP_ASIGNACION
                valor = "="
            else:
                tipo = TipoToken.DESCONOCIDO
                valor = lexema

            tokens.append(Token(
                tipo=tipo,
                lexema=lexema,
                valor=valor,
                origen=TokenOrigen.AFD,
                posicion=pos_abs,
                hilo=hilo_actual,
            ))

        fin = time.perf_counter()
        tiempo_total_ms = (fin - inicio) * 1000

        tokens = self._fusionar_conectores_ambiguos(tokens)

        # Evidencia en consola del análisis léxico del AFD (requisito obligatorio)
        print(
            f"[AFD][{hilo_actual}] Tokenización formal completada en "
            f"{tiempo_total_ms:.3f} ms -> {len(tokens)} tokens "
            f"({len(errores)} errores léxicos)"
        )

        # Repartimos el tiempo total entre los tokens (solo informativo)
        if tokens:
            tiempo_por_token = tiempo_total_ms / len(tokens)
            for t in tokens:
                t.tiempo_ms = tiempo_por_token

        return tokens, errores

    def _fusionar_conectores_ambiguos(self, tokens: list[Token]) -> list[Token]:
        """
        Post-procesamiento sobre la salida cruda del AFD: cuando una
        letra suelta clasificada como VAR (ej. "a") es en realidad un
        conector español/inglés común Y está inmediatamente adyacente
        a un fragmento TEXTO_LN, se fusiona dentro de ese fragmento en
        lugar de quedar como variable matemática.

        Esto resuelve la ambigüedad léxica real entre "x" (variable)
        y "a" (preposición en "es igual a") sin necesidad de un AFD
        con estados de lookahead arbitrariamente complejos.
        """
        resultado: list[Token] = []
        for token in tokens:
            es_conector_ambiguo = (
                token.tipo == TipoToken.VAR
                and token.lexema.lower() in self._CONECTORES_UNA_LETRA
            )
            if (
                es_conector_ambiguo
                and resultado
                and resultado[-1].tipo == TipoToken.TEXTO_LN
            ):
                anterior = resultado[-1]
                anterior.lexema = f"{anterior.lexema} {token.lexema}".strip()
                anterior.valor = anterior.lexema.lower()
                continue
            resultado.append(token)
        return resultado

    def extraer_fragmentos_texto_natural(self, tokens: list[Token]) -> list[Token]:
        """
        Filtra y devuelve únicamente los tokens TEXTO_LN producidos por
        el AFD, que son los que requieren clasificación semántica
        adicional por parte del LLM.
        """
        return [t for t in tokens if t.tipo == TipoToken.TEXTO_LN]

    def tiene_errores_lexicos(self, tokens: list[Token]) -> bool:
        """Indica si el flujo de tokens contiene algún error léxico (UNKNOWN)."""
        return any(t.tipo == TipoToken.UNKNOWN for t in tokens)

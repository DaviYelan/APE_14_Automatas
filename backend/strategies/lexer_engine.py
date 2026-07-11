"""
LexerEngine
-----------
Orquestador del pipeline completo de compilación:
    Fase 1 — Análisis Léxico (AFD + LLM concurrente)
    Fase 2 — Análisis Sintáctico (Parser Descendente Recursivo Python)
    Fase 3 — Análisis Semántico (Microservicio Java / Spring Boot)

El motor léxico, el parser y el analizador semántico están desacoplados:
LexerEngine solo coordina el orden de ejecución y agrega los tiempos.
"""

import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.token import Token, TipoToken, ErrorLexico
from services.semantic_client import SemanticClient
from strategies.automata_strategy import AutomataStrategy
from strategies.llm_strategy import LLMStrategy
from strategies.parser_strategy import ParserStrategy


class LexerEngine:
    """Coordina AFD, LLM, Parser y Analizador Semántico."""

    def __init__(
        self,
        automata: AutomataStrategy | None = None,
        llm: LLMStrategy | None = None,
        parser: ParserStrategy | None = None,
        semantic_client: SemanticClient | None = None,
    ) -> None:
        self.automata        = automata        or AutomataStrategy()
        self.llm             = llm             or LLMStrategy()
        self.parser          = parser          or ParserStrategy()
        self.semantic_client = semantic_client or SemanticClient()
        self.max_workers = int(os.getenv("LLM_MAX_WORKERS", "4"))

    def analizar(self, entrada: str) -> dict:
        """
        Ejecuta el pipeline completo sobre `entrada`:
            1. AFD — tokenización formal (hilo principal)
            2. LLM — clasificación semántica NLP (ThreadPoolExecutor)
            3. Parser LL(1) — análisis sintáctico descendente recursivo
            4. Analizador Semántico Java — tabla de símbolos y solución
        """
        threading.current_thread().name = "Hilo-AFD"
        separador = "=" * 70
        print(f"\n{separador}")
        print(f"[Pipeline] Iniciando compilación: '{entrada}'")
        print(separador)

        inicio_total = time.perf_counter()
        hilos_evidenciados: set[str] = {threading.current_thread().name}

        # ── FASE 1: Análisis Léxico — AFD ────────────────────────────────
        inicio_lexer = time.perf_counter()
        tokens_brutos, errores_lexicos = self.automata.tokenize(entrada, posicion=0)
        fin_lexer = time.perf_counter()
        tiempo_lexer_ms = (fin_lexer - inicio_lexer) * 1000

        tokens_formales      = [t for t in tokens_brutos if t.tipo != TipoToken.TEXTO_LN]
        fragmentos_naturales = self.automata.extraer_fragmentos_texto_natural(tokens_brutos)

        print(
            f"[Léxico] AFD: {len(tokens_formales)} formales, "
            f"{len(fragmentos_naturales)} fragmentos NL, "
            f"{len(errores_lexicos)} errores léxicos"
        )

        # ── FASE 1b: Análisis Léxico — LLM concurrente ───────────────────
        tokens_semanticos: list[Token] = []
        inicio_llm = time.perf_counter()

        if fragmentos_naturales:
            with ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="ThreadPoolExecutor-0",
            ) as executor:
                futuros = {
                    executor.submit(self.llm.tokenize, frag.lexema, frag.posicion): frag
                    for frag in fragmentos_naturales
                }
                for futuro in as_completed(futuros):
                    resultado = futuro.result()
                    tokens_semanticos.extend(resultado)
                    for t in resultado:
                        hilos_evidenciados.add(t.hilo)

        fin_llm = time.perf_counter()
        tiempo_llm_ms = (fin_llm - inicio_llm) * 1000

        todos_los_tokens = sorted(
            tokens_formales + tokens_semanticos, key=lambda t: t.posicion
        )

        print(f"[Léxico] Hilos activos: {sorted(hilos_evidenciados)}")

        # ── FASE 2: Análisis Sintáctico ───────────────────────────────────
        arbol_sintactico    = None
        errores_sintacticos = []
        tiempo_parser_ms    = 0.0

        if not errores_lexicos:
            print("[Pipeline] Fase léxica OK — iniciando análisis sintáctico")
            arbol_sintactico, errores_sintacticos, tiempo_parser_ms = \
                self.parser.parsear(todos_los_tokens)
        else:
            print("[Pipeline] Fase léxica con errores — sintáctico omitido")

        # ── FASE 3: Análisis Semántico (Java) ────────────────────────────
        resultado_semantico = None
        tiempo_semantico_ms = 0.0
        errores_semanticos  = []

        if arbol_sintactico is not None and not errores_sintacticos:
            print("[Pipeline] Fase sintáctica OK — iniciando análisis semántico (Java)")
            inicio_sem = time.perf_counter()
            resultado_semantico = self.semantic_client.analizar(entrada, arbol_sintactico)
            fin_sem = time.perf_counter()
            tiempo_semantico_ms = (fin_sem - inicio_sem) * 1000

            if resultado_semantico:
                errores_semanticos = resultado_semantico.get("errores", [])
                # El servicio Java ya devuelve errores con la clave "fase"="semantico"
                print(
                    f"[Semántico] Java: valido={resultado_semantico.get('valido')} "
                    f"errores={len(errores_semanticos)}"
                )
            else:
                print("[Semántico] Servicio Java no disponible — fase omitida")
        elif arbol_sintactico is None:
            print("[Pipeline] Árbol nulo — análisis semántico omitido")

        # ── Consolidar todos los errores ──────────────────────────────────
        todos_los_errores = (
            [e.to_dict() for e in errores_lexicos]
            + [e.to_dict() for e in errores_sintacticos]
            + errores_semanticos
        )

        fin_total = time.perf_counter()
        tiempo_total_ms = (fin_total - inicio_total) * 1000
        hilos_evidenciados.add(threading.current_thread().name)

        print(f"[Pipeline] Total: {tiempo_total_ms:.2f} ms | "
              f"Errores: {len(todos_los_errores)}")
        print(f"{separador}\n")

        # Tabla de símbolos y solución del analizador semántico Java
        tabla_simbolos = None
        solucion       = None
        if resultado_semantico:
            tabla_simbolos = resultado_semantico.get("tablaSimbolos")
            if tabla_simbolos:
                solucion = tabla_simbolos.get("solucion")

        return {
            "entrada":          entrada,
            "tokens":           [t.to_dict() for t in todos_los_tokens],
            "errores":          todos_los_errores,
            "arbol_sintactico": arbol_sintactico,
            "tabla_simbolos":   tabla_simbolos,
            "solucion":         solucion,
            "semantico_valido": resultado_semantico.get("valido") if resultado_semantico else None,
            "tiempos": {
                "total_ms":    round(tiempo_total_ms,    3),
                "lexer_ms":    round(tiempo_lexer_ms,    3),
                "llm_ms":      round(tiempo_llm_ms,      3),
                "parser_ms":   round(tiempo_parser_ms,   3),
                "semantic_ms": round(tiempo_semantico_ms, 3),
            },
            "hilos_activos":    sorted(hilos_evidenciados),
            "tokens_afd_count": len(tokens_formales),
            "tokens_llm_count": len(tokens_semanticos),
        }

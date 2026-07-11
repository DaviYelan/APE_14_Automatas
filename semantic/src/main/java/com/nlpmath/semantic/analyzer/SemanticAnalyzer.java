package com.nlpmath.semantic.analyzer;

import com.fasterxml.jackson.databind.JsonNode;
import com.nlpmath.semantic.model.ErrorSemantico;
import com.nlpmath.semantic.model.SemanticResponse;
import com.nlpmath.semantic.model.TablaSimbolos;
import com.nlpmath.semantic.service.OllamaService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * SemanticAnalyzer
 * ----------------
 * Núcleo del análisis semántico. Aplica las reglas semánticas del DSL
 * de Ecuaciones de Primer Grado sobre la tabla de símbolos construida
 * por {@link AstVisitor}.
 *
 * REGLAS SEMÁNTICAS IMPLEMENTADAS:
 * ─────────────────────────────────────────────────────────────────────
 * R1. VARIABLE_AUSENTE    → La ecuación no contiene ninguna variable.
 *                           "5 = 13" no tiene incógnita → sin solución o imposible.
 *
 * R2. MULTIPLES_VARIABLES → Aparecen más de una variable distinta.
 *                           "x + y = 5" → sistema indeterminado (fuera del DSL).
 *
 * R3. COEFICIENTE_CERO    → El coeficiente neto de la variable es 0.
 *                           "2x - 2x = 5" → la variable se cancela.
 *
 * R4. ECUACION_IMPOSIBLE  → Sin variable y con constantes distintas.
 *                           "3 = 7" → imposible, nunca es verdad.
 *
 * R5. ECUACION_TAUTOLOGIA → Sin variable y con misma constante en ambos lados.
 *                           "5 = 5" → siempre verdad, infinitas soluciones.
 * ─────────────────────────────────────────────────────────────────────
 *
 * Cuando hay un error, se invoca {@link OllamaService} para generar
 * la explicación en lenguaje natural. La lógica de detección es Java puro.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class SemanticAnalyzer {

    private final OllamaService ollamaService;

    /**
     * Ejecuta el análisis semántico completo sobre el AST.
     *
     * @param arbol   nodo raíz del AST JSON (tipo "ECUACION")
     * @param entrada cadena original del usuario (para contexto en errores)
     * @return SemanticResponse con validez, errores, tabla de símbolos y solución
     */
    public SemanticResponse analizar(JsonNode arbol, String entrada) {
        long inicio = System.nanoTime();

        // ── Paso 1: Recorrer el AST y construir la tabla de símbolos ─────
        AstVisitor visitor = new AstVisitor();
        visitor.visitEcuacion(arbol);

        Map<String, Double> coeficientes  = visitor.getCoeficientes();
        double              constanteNeta = visitor.getConstanteNeta();
        List<String>        varsUnicas    = visitor.getVariablesUnicas();

        log.debug("[Semántico] Coeficientes: {} | Constante neta: {} | Vars: {}",
                  coeficientes, constanteNeta, varsUnicas);

        // ── Paso 2: Aplicar reglas semánticas ────────────────────────────
        List<ErrorSemantico> errores = new ArrayList<>();

        // R4/R5 primero: ecuación sin variables (casos degenerados)
        if (varsUnicas.isEmpty()) {
            if (Math.abs(constanteNeta) > 1e-9) {
                // R4: constantes distintas → imposible
                agregarError(errores, "ECUACION_IMPOSIBLE",
                    "La ecuación no contiene ninguna variable y sus constantes son " +
                    "distintas (contradicción): " + entrada,
                    entrada);
            } else {
                // R5: constantes iguales → tautología
                agregarError(errores, "ECUACION_TAUTOLOGIA",
                    "La ecuación no contiene ninguna variable y es siempre " +
                    "verdadera (tautología): ambos lados son iguales.",
                    entrada);
            }
        }

        // R2: más de una variable distinta
        if (varsUnicas.size() > 1) {
            agregarError(errores, "MULTIPLES_VARIABLES",
                "La ecuación contiene más de una variable distinta: " +
                String.join(", ", varsUnicas) +
                ". Este DSL solo acepta ecuaciones de una incógnita.",
                entrada);
        }

        // R3: coeficiente neto de la variable es cero (variable se cancela)
        if (varsUnicas.size() == 1) {
            String varNombre = varsUnicas.get(0);
            double coef      = coeficientes.getOrDefault(varNombre, 0.0);
            if (Math.abs(coef) < 1e-9) {
                agregarError(errores, "COEFICIENTE_CERO",
                    "El coeficiente neto de la variable '" + varNombre +
                    "' es 0 (se cancela en ambos lados). La ecuación no " +
                    "tiene solución única o es una contradicción.",
                    entrada);
            }
        }

        // ── Paso 3: Si no hay errores, calcular la solución ──────────────
        Double solucion     = null;
        String tipoEcuacion = "desconocida";

        if (errores.isEmpty() && varsUnicas.size() == 1) {
            String varNombre = varsUnicas.get(0);
            double coef      = coeficientes.getOrDefault(varNombre, 0.0);
            // ax + b = 0  →  x = -b / a
            // constanteNeta ya es (lado_izq - lado_der), por lo que:
            // coef·x + constanteNeta = 0 → x = -constanteNeta / coef
            solucion     = -constanteNeta / coef;
            tipoEcuacion = "ecuacion_primer_grado_una_variable";

            log.info("[Semántico] Solución: {} = {}", varNombre, solucion);
        }

        // ── Paso 4: Construir tabla de símbolos ───────────────────────────
        TablaSimbolos tabla = TablaSimbolos.builder()
                .variables(coeficientes)
                .terminoIndependiente(constanteNeta)
                .variablesUnicas(varsUnicas)
                .solucion(solucion)
                .tipoEcuacion(tipoEcuacion)
                .build();

        long fin        = System.nanoTime();
        double tiempoMs = (fin - inicio) / 1_000_000.0;

        log.info("[Semántico] Análisis completado en {:.3f} ms — {} error(es)",
                 tiempoMs, errores.size());

        return SemanticResponse.builder()
                .valido(errores.isEmpty())
                .errores(errores)
                .tablaSimbolos(tabla)
                .tiempoMs(Math.round(tiempoMs * 1000.0) / 1000.0)
                .build();
    }

    /**
     * Crea un ErrorSemantico con lógica Java y enriquece el mensaje
     * mediante una consulta a Ollama para la explicación didáctica.
     */
    private void agregarError(
            List<ErrorSemantico> errores,
            String codigo,
            String causaTecnica,
            String entradaOriginal) {

        log.warn("[Semántico] Error detectado: {} — {}", codigo, causaTecnica);

        // Ollama genera SOLO el mensaje explicativo en lenguaje natural.
        // Si Ollama no está disponible, se usa el mensaje técnico como fallback.
        String mensajeLLM = ollamaService.generarExplicacionError(
                codigo, causaTecnica, entradaOriginal);

        errores.add(ErrorSemantico.builder()
                .fase("semantico")
                .codigo(codigo)
                .causa(causaTecnica)
                .mensajeLLM(mensajeLLM)
                .build());
    }
}

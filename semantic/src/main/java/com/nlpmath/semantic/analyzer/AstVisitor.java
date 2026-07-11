package com.nlpmath.semantic.analyzer;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

import java.util.*;

/**
 * AstVisitor
 * ----------
 * Recorre el AST JSON producido por el parser Python y extrae
 * la información semántica necesaria para el análisis:
 *
 *   - Variables encontradas con sus coeficientes por lado de la ecuación
 *   - Constantes numéricas por lado
 *
 * Patrón de diseño: Visitor sobre el árbol JSON.
 * Cada método visit* corresponde a un tipo de nodo del AST.
 *
 * Nomenclatura:
 *   lado = +1 → lado izquierdo de la ecuación (antes del '=')
 *   lado = -1 → lado derecho (al pasar al otro lado, el signo se invierte)
 */
@Slf4j
@Getter
public class AstVisitor {

    /**
     * Mapa de variable → coeficiente NETO en la forma ax + b = 0.
     * Al procesar el lado derecho multiplicamos por -1 para llevar
     * todo al lado izquierdo: izq = der ⟹ izq - der = 0.
     */
    private final Map<String, Double> coeficientes = new LinkedHashMap<>();

    /**
     * Constante neta (término independiente) en la forma ax + b = 0.
     * Ejemplo: 2x + 5 = 13  ⟹  b = 5 - 13 = -8
     */
    private double constanteNeta = 0.0;

    /** Todas las variables encontradas (con duplicados por aparición). */
    private final List<String> variablesEncontradas = new ArrayList<>();

    /**
     * Visita el nodo raíz ECUACION del AST.
     * Delega recursivamente al lado izquierdo (signo +1)
     * y al lado derecho (signo -1, ya que pasamos al otro lado).
     */
    public void visitEcuacion(JsonNode nodo) {
        log.debug("[AstVisitor] Visitando ECUACION");
        JsonNode izquierda = nodo.get("izquierda");
        JsonNode derecha   = nodo.get("derecha");

        if (izquierda != null) visitExpresion(izquierda, +1);
        if (derecha   != null) visitExpresion(derecha,   -1);
    }

    /**
     * Visita un nodo de expresión (puede ser BINOP, TERMINO, NUMERO o VAR).
     *
     * @param nodo  nodo JSON del AST
     * @param signo +1 para lado izquierdo, -1 para lado derecho
     */
    private void visitExpresion(JsonNode nodo, int signo) {
        if (nodo == null) return;
        String tipo = nodo.path("nodo").asText("");

        switch (tipo) {
            case "BINOP"   -> visitBinop(nodo, signo);
            case "TERMINO" -> visitTermino(nodo, signo);
            case "NUMERO"  -> visitNumero(nodo, signo);
            case "VAR"     -> visitVar(nodo, signo);
            default        -> log.warn("[AstVisitor] Nodo desconocido: {}", tipo);
        }
    }

    /**
     * Visita una operación binaria (BINOP): distribuye el signo
     * según el operador (suma mantiene signo, resta lo invierte).
     *
     * Ejemplo: 2x - 3 con signo +1:
     *   izquierda(2x) → signo +1
     *   derecha(3)    → signo -1  (porque el operador es resta)
     */
    private void visitBinop(JsonNode nodo, int signo) {
        String op = nodo.path("operador").asText("");
        log.debug("[AstVisitor] BINOP op='{}' signo={}", op, signo);

        JsonNode izq = nodo.get("izquierda");
        JsonNode der = nodo.get("derecha");

        // Para la resta, el término de la derecha se resta → signo invertido
        int signoDer = (op.equals("menos") || op.equals("-")) ? -signo : signo;

        visitExpresion(izq, signo);
        visitExpresion(der, signoDer);
    }

    /**
     * Visita un TERMINO de tipo coeficiente·variable (ej: 2x).
     * Registra el coeficiente en el mapa de variables.
     */
    private void visitTermino(JsonNode nodo, int signo) {
        double coef    = nodo.path("coeficiente").asDouble(1.0);
        String varNombre = nodo.path("variable").asText("");

        log.debug("[AstVisitor] TERMINO {}·{} signo={}", coef, varNombre, signo);

        if (!varNombre.isEmpty()) {
            double valorEfectivo = coef * signo;
            coeficientes.merge(varNombre, valorEfectivo, Double::sum);
            variablesEncontradas.add(varNombre);
        }
    }

    /**
     * Visita un nodo NUMERO (constante pura).
     * Lo suma a la constante neta con el signo correspondiente.
     */
    private void visitNumero(JsonNode nodo, int signo) {
        double valor = nodo.path("valor").asDouble(0.0);
        log.debug("[AstVisitor] NUMERO {} signo={}", valor, signo);
        constanteNeta += valor * signo;
    }

    /**
     * Visita un nodo VAR (variable sin coeficiente explícito → coef=1).
     */
    private void visitVar(JsonNode nodo, int signo) {
        String nombre = nodo.path("nombre").asText("");
        log.debug("[AstVisitor] VAR {} signo={}", nombre, signo);

        if (!nombre.isEmpty()) {
            coeficientes.merge(nombre, (double) signo, Double::sum);
            variablesEncontradas.add(nombre);
        }
    }

    /** Devuelve la lista de variables únicas encontradas. */
    public List<String> getVariablesUnicas() {
        return new ArrayList<>(new LinkedHashSet<>(variablesEncontradas));
    }
}

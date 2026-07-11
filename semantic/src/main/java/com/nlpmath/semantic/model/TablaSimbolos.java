package com.nlpmath.semantic.model;

import lombok.Builder;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * Tabla de Símbolos construida por el analizador semántico.
 *
 * En el contexto de este DSL (ecuaciones de primer grado) la tabla
 * de símbolos registra:
 *   - Variables encontradas en la ecuación (nombre → coeficiente total)
 *   - Constantes numéricas detectadas
 *   - Lado de la ecuación en que aparece cada símbolo (izquierdo/derecho)
 *
 * Esta tabla es la estructura central del análisis semántico: permite
 * detectar ecuaciones con múltiples variables, coeficientes nulos, etc.
 */
@Data
@Builder
public class TablaSimbolos {

    /**
     * Variables encontradas → coeficiente efectivo en la ecuación.
     * Ejemplo para "2x + 3 = x + 7":
     *   { "x": 1.0 }   (2x del lado izquierdo - x del lado derecho = 1x neto)
     */
    private Map<String, Double> variables;

    /** Término constante neto (lado izquierdo − lado derecho). */
    private double terminoIndependiente;

    /** Lista de variables únicas detectadas (sin duplicados). */
    private List<String> variablesUnicas;

    /** Solución numérica de la ecuación, si existe y es única. */
    private Double solucion;

    /** Descripción del tipo de ecuación detectado. */
    private String tipoEcuacion;
}

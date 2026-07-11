package com.nlpmath.semantic.model;

import lombok.Builder;
import lombok.Data;

import java.util.List;

/**
 * DTO de respuesta del servicio semántico.
 *
 * Flask recibe este JSON y lo incorpora en la respuesta final del
 * pipeline, añadiendo los campos semánticos al resultado existente
 * (que ya contiene tokens, árbol sintáctico, errores léxicos/sintácticos).
 */
@Data
@Builder
public class SemanticResponse {

    /** true si la ecuación es semánticamente válida. */
    private boolean valido;

    /**
     * Lista de errores semánticos encontrados.
     * Vacía cuando {@code valido == true}.
     */
    private List<ErrorSemantico> errores;

    /**
     * Tabla de símbolos construida durante el análisis.
     * Contiene las variables, coeficientes y la solución (si existe).
     */
    private TablaSimbolos tablaSimbolos;

    /** Tiempo empleado en el análisis semántico (ms). */
    private double tiempoMs;
}

package com.nlpmath.semantic.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.databind.JsonNode;
import lombok.Data;

/**
 * DTO de entrada: el payload que Flask envía al servicio semántico.
 *
 * Contiene el AST JSON completo producido por el parser Python
 * y la cadena original de entrada (para contexto en mensajes de error).
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class SemanticRequest {

    /** Cadena original tal como la escribió el usuario. */
    private String entrada;

    /**
     * AST (Árbol de Sintaxis Abstracta) en formato JSON producido por
     * el Parser Descendente Recursivo de Python.
     * Estructura esperada:
     * <pre>
     * {
     *   "nodo": "ECUACION",
     *   "operador": "es igual a",
     *   "izquierda": { ... },
     *   "derecha": { ... }
     * }
     * </pre>
     */
    private JsonNode arbol_sintactico;
}

package com.nlpmath.semantic.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Representa un error semántico detectado durante el análisis.
 *
 * Un error semántico ocurre cuando la estructura de la ecuación es
 * sintácticamente correcta pero carece de sentido matemático/lógico.
 * Ejemplos:
 *   - Variable no definida: "x + y = 5" (dos incógnitas, indeterminado)
 *   - Coeficiente cero: "0x + 3 = 7" (la variable desaparece)
 *   - Ecuación sin variable: "5 = 13" (no hay incógnita, imposible)
 *   - Ecuación trivial: "5 = 5" (tautología, infinitas soluciones vacías)
 *
 * El campo {@code mensajeLLM} es generado por Ollama SOLO cuando hay error,
 * para ofrecer una explicación didáctica al usuario. La lógica que detecta
 * el error está 100% en Java.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ErrorSemantico {

    /** Siempre "semantico" para distinguirlo de errores léxicos/sintácticos. */
    private String fase;

    /** Código corto del tipo de error (para el frontend). */
    private String codigo;

    /** Descripción técnica generada por la lógica Java. */
    private String causa;

    /** Explicación didáctica generada por Ollama en lenguaje natural. */
    private String mensajeLLM;
}

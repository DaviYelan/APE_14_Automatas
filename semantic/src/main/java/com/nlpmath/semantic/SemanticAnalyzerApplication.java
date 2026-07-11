package com.nlpmath.semantic;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Punto de entrada del microservicio de Análisis Semántico.
 *
 * Responsabilidad única: verificar la coherencia semántica del AST
 * producido por el parser Python. Este servicio NO procesa texto plano
 * ni realiza tokenización — solo trabaja sobre el árbol JSON ya construido.
 *
 * Ollama se usa aquí EXCLUSIVAMENTE para enriquecer los mensajes de error
 * con explicaciones en lenguaje natural. Toda la lógica semántica
 * (tabla de símbolos, validaciones, resolución) está en Java puro.
 */
@SpringBootApplication
public class SemanticAnalyzerApplication {

    public static void main(String[] args) {
        SpringApplication.run(SemanticAnalyzerApplication.class, args);
    }
}

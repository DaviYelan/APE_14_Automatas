package com.nlpmath.semantic.controller;

import com.nlpmath.semantic.analyzer.SemanticAnalyzer;
import com.nlpmath.semantic.model.SemanticRequest;
import com.nlpmath.semantic.model.SemanticResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * SemanticController
 * ------------------
 * Controlador REST del microservicio de análisis semántico.
 *
 * Expone un único endpoint POST /semantic/analyze que recibe el AST
 * JSON producido por el parser Python y devuelve el resultado del
 * análisis semántico (tabla de símbolos, errores y solución).
 *
 * Flask (Python) llama a este endpoint como Fase 3 del pipeline
 * de compilación, después de que el parser ya produjo el AST.
 */
@Slf4j
@RestController
@RequestMapping("/semantic")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")   // CORS para peticiones desde Flask en Docker
public class SemanticController {

    private final SemanticAnalyzer semanticAnalyzer;

    /**
     * Endpoint de análisis semántico.
     *
     * @param request JSON con { "entrada": "...", "arbol_sintactico": {...} }
     * @return SemanticResponse con validez, errores, tabla de símbolos y tiempos
     */
    @PostMapping("/analyze")
    public ResponseEntity<SemanticResponse> analyze(
            @RequestBody SemanticRequest request) {

        log.info("[SemanticController] POST /semantic/analyze — entrada: '{}'",
                 request.getEntrada());

        if (request.getArbol_sintactico() == null
                || request.getArbol_sintactico().isNull()) {
            log.warn("[SemanticController] AST nulo recibido — " +
                     "análisis semántico no puede ejecutarse");
            return ResponseEntity.badRequest().build();
        }

        SemanticResponse response = semanticAnalyzer.analizar(
                request.getArbol_sintactico(),
                request.getEntrada() != null ? request.getEntrada() : ""
        );

        log.info("[SemanticController] Resultado: valido={}, errores={}",
                 response.isValido(), response.getErrores().size());

        return ResponseEntity.ok(response);
    }

    /** Health check del microservicio Java. */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("{\"status\":\"ok\",\"servicio\":\"semantic-analyzer-java\"}");
    }
}

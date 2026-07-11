package com.nlpmath.semantic.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * OllamaService
 * -------------
 * Cliente HTTP hacia el servicio Ollama. Se usa EXCLUSIVAMENTE para
 * generar mensajes de error en lenguaje natural cuando el analizador
 * semántico Java detecta un problema.
 *
 * IMPORTANTE: Este servicio NO contiene lógica semántica. Solo toma
 * un error ya detectado por {@code SemanticAnalyzer} y le pide al LLM
 * que genere una explicación didáctica para el usuario.
 *
 * Si Ollama no está disponible, el método devuelve el mensaje técnico
 * como fallback — el pipeline no falla por falta del LLM.
 */
@Slf4j
@Service
public class OllamaService {

    @Value("${ollama.host}")
    private String ollamaHost;

    @Value("${ollama.model}")
    private String ollamaModel;

    @Value("${ollama.timeout-seconds}")
    private int timeoutSegundos;

    private static final String SYSTEM_PROMPT =
        "Eres un asistente didáctico de matemáticas para estudiantes universitarios. " +
        "Tu tarea es explicar errores semánticos encontrados en ecuaciones de primer grado " +
        "escritas en lenguaje natural en español. " +
        "El error ya fue detectado automáticamente por el compilador; tú solo debes " +
        "explicarlo de forma clara y didáctica en 2-3 oraciones en español. " +
        "No uses markdown, no uses listas, solo texto plano. " +
        "Sé específico con la ecuación del usuario.";

    /**
     * Genera una explicación en lenguaje natural para un error semántico.
     *
     * @param codigoError     código del error (ej: COEFICIENTE_CERO)
     * @param causaTecnica    descripción técnica Java del error
     * @param entradaOriginal ecuación original que escribió el usuario
     * @return explicación generada por el LLM, o fallback si Ollama no responde
     */
    public String generarExplicacionError(
            String codigoError,
            String causaTecnica,
            String entradaOriginal) {

        String prompt = String.format(
            "El usuario escribió esta ecuación: \"%s\"\n" +
            "El compilador detectó el siguiente error semántico:\n" +
            "- Código: %s\n" +
            "- Causa técnica: %s\n\n" +
            "Explica al usuario qué significa este error en su ecuación y " +
            "cómo podría corregirla.",
            entradaOriginal, codigoError, causaTecnica
        );

        try {
            String respuesta = llamarOllama(prompt);
            if (respuesta != null && !respuesta.isBlank()) {
                log.debug("[OllamaService] Mensaje generado para {}: {}",
                          codigoError, respuesta);
                return respuesta.trim();
            }
        } catch (Exception e) {
            log.warn("[OllamaService] Ollama no disponible ({}), usando fallback.", e.getMessage());
        }

        // Fallback: si Ollama no responde, devolvemos la causa técnica
        return causaTecnica;
    }

    /**
     * Realiza la petición HTTP al endpoint /api/generate de Ollama.
     * Usa el cliente HTTP nativo de Java 11+ (sin dependencias extra).
     */
    private String llamarOllama(String prompt) throws IOException, InterruptedException {
        String url  = ollamaHost + "/api/generate";
        // Serialización manual del JSON para evitar dependencia de Jackson
        // en esta capa de servicio pura.
        String body = String.format(
            "{\"model\":\"%s\",\"system\":\"%s\",\"prompt\":\"%s\"," +
            "\"stream\":false,\"options\":{\"temperature\":0}}",
            ollamaModel,
            escaparJson(SYSTEM_PROMPT),
            escaparJson(prompt)
        );

        HttpClient  client  = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(timeoutSegundos))
                .build();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(timeoutSegundos))
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        HttpResponse<String> response =
                client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            log.warn("[OllamaService] HTTP {} desde Ollama", response.statusCode());
            return null;
        }

        // Extraemos solo el campo "response" del JSON de respuesta de Ollama
        // sin usar Jackson para mantener esta clase sin estado de serialización.
        String responseBody = response.body();
        int inicio = responseBody.indexOf("\"response\":\"");
        if (inicio == -1) return null;
        inicio += "\"response\":\"".length();
        int fin = responseBody.indexOf("\",", inicio);
        if (fin == -1) fin = responseBody.indexOf("\"}", inicio);
        if (fin == -1) return null;

        return responseBody.substring(inicio, fin)
                .replace("\\n", "\n")
                .replace("\\\"", "\"");
    }

    /** Escapa caracteres especiales para embeber texto en un string JSON. */
    private String escaparJson(String texto) {
        return texto
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}

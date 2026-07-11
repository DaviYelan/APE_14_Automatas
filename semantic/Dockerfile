# Dockerfile — Servicio Semántico Java (Spring Boot)
# Multi-stage: Stage 1 compila con Maven, Stage 2 ejecuta con JRE mínimo.
# La imagen final no contiene Maven ni el código fuente, solo el JAR.

# ── Stage 1: BUILD ────────────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-21 AS build

WORKDIR /app

# Copiamos pom.xml primero para aprovechar la caché de dependencias Maven.
# Si solo cambia el código fuente y no el pom.xml, Maven no re-descarga
# las dependencias en builds posteriores.
COPY pom.xml .
RUN mvn dependency:go-offline -q

# Ahora copiamos el código fuente y compilamos
COPY src ./src
RUN mvn package -DskipTests -q

# ── Stage 2: RUN ──────────────────────────────────────────────────────
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Solo copiamos el JAR ejecutable desde el stage de build
COPY --from=build /app/target/semantic-analyzer-1.0.0.jar app.jar

# El puerto se configura en application.properties via variable de entorno
EXPOSE 8080

# Variables de entorno por defecto (sobreescritas por docker-compose / .env)
ENV SEMANTIC_PORT=8080
ENV OLLAMA_HOST=http://ollama:11434
ENV OLLAMA_MODEL=llama3.2:1b
ENV OLLAMA_TIMEOUT_SECONDS=30

ENTRYPOINT ["java", "-jar", "app.jar"]

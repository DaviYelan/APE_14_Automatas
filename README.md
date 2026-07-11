# Mini-Compilador NLP-Math

Analizador léxico híbrido para un DSL de **ecuaciones de primer grado en
lenguaje natural**, combinando un Autómata Finito Determinista (AFD vía
expresiones regulares) con un LLM (Ollama) para clasificar fragmentos de
lenguaje natural en tokens formales — ejecutados de forma concurrente
mediante `ThreadPoolExecutor`.

> **Práctica Nro. 12 — Teoría de Autómatas y Computabilidad Avanzada — UNL**
> Contexto elegido: **1. Compilador de Ecuaciones de Primer Grado (NLP-Math)**

**Stack tecnológico:**
- Backend: **Flask** (Python 3.11) + `flask-cors` + `python-dotenv`
- Frontend: **React 18** + **Vite** servido por Nginx
- LLM local: **Ollama** (llama3 u otro modelo configurable)
- Contenedores: **Docker Compose**

---

## Tabla de contenidos

1. [Requisitos previos](#1-requisitos-previos)
2. [Instalación de Docker y Docker Compose](#2-instalación-de-docker-y-docker-compose)
3. [Configuración del archivo .env](#3-configuración-del-archivo-env)
4. [Descarga del modelo de Ollama](#4-descarga-del-modelo-de-ollama)
5. [Construcción y ejecución](#5-construcción-y-ejecución)
6. [Detener los servicios](#6-detener-los-servicios)
7. [Estructura del proyecto](#7-estructura-del-proyecto)
8. [Ejemplos de prueba y uso](#8-ejemplos-de-prueba-y-uso)
9. [Solución de problemas](#9-solución-de-problemas)

---

## 1. Requisitos previos

- Docker Desktop (Windows/macOS) o Docker Engine + Docker Compose plugin (Linux).
- Mínimo **8 GB de RAM** y ~5 GB de espacio en disco para el modelo LLM.
- Puertos libres: `8000` (backend Flask), `3000` (frontend React), `11434` (Ollama).

No se necesita instalar Python, Node.js ni ninguna dependencia adicional
en el sistema anfitrión — **todo corre en contenedores Docker.**

---

## 2. Instalación de Docker y Docker Compose

### Windows / macOS
Instalar [Docker Desktop](https://www.docker.com/products/docker-desktop/) y verificar:
```bash
docker --version
docker compose version
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # cerrar sesión y volver a entrar
```

---

## 3. Configuración del archivo .env

```bash
cp .env.example .env
```

El archivo `.env` por defecto funciona para la mayoría de los casos:

```env
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT_SECONDS=30
BACKEND_PORT=8000
LLM_MAX_WORKERS=4
FRONTEND_PORT=3000
VITE_BACKEND_URL=http://localhost:8000
OLLAMA_VOLUME_NAME=ollama_data
```

> **Nota sobre `VITE_BACKEND_URL`:** esta URL la usa el **navegador**
> para conectarse al backend Flask. En un servidor remoto, cambia
> `localhost` por la IP pública del servidor.

---

## 4. Descarga del modelo de Ollama

Tras levantar los contenedores (paso 5), en otra terminal ejecuta:

```bash
docker exec -it nlp-math-ollama ollama pull llama3
```

El modelo (~4.7 GB) se persiste en el volumen `ollama_data` y no
necesita descargarse de nuevo en futuros arranques.

Verificar instalación:
```bash
docker exec -it nlp-math-ollama ollama list
```

Para un modelo más ligero (si tienes menos de 8 GB de RAM):
```bash
docker exec -it nlp-math-ollama ollama pull llama3.2:1b
# Y actualiza OLLAMA_MODEL=llama3.2:1b en tu .env
```

---

## 5. Construcción y ejecución

```bash
docker compose up --build
```

Este comando construye las tres imágenes (Flask backend, React frontend
con Vite, Ollama) y levanta todos los servicios. La primera vez puede
tardar varios minutos por la descarga de imágenes base.

Una vez en marcha:

| Servicio | URL |
|---|---|
| Frontend React | http://localhost:3000 |
| Backend Flask (API) | http://localhost:8000 |
| Ollama (API directa) | http://localhost:11434 |

Para ejecutar en segundo plano:
```bash
docker compose up --build -d
```

Ver logs del backend Flask (evidencia de hilos en consola):
```bash
docker compose logs -f backend
```

---

## 6. Detener los servicios

```bash
docker compose down          # detiene y elimina contenedores (conserva modelos)
docker compose down -v       # elimina también el volumen de modelos Ollama
```

---

## 7. Estructura del proyecto

```
nlp-math-compiler/
├── backend/
│   ├── strategies/
│   │   ├── base_strategy.py      # Interfaz del patrón Strategy
│   │   ├── automata_strategy.py  # AFD vía expresiones regulares (re)
│   │   ├── llm_strategy.py       # Tokenizador semántico vía Ollama
│   │   └── lexer_engine.py       # Orquesta AFD + ThreadPoolExecutor
│   ├── services/
│   │   └── ollama_client.py      # Cliente HTTP hacia Ollama
│   ├── models/
│   │   └── token.py              # Dataclass Token (contrato común)
│   ├── main.py                   # API Flask (punto de entrada)
│   ├── requirements.txt          # flask, flask-cors, python-dotenv, requests
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Componente raíz React
│   │   ├── main.jsx              # Punto de entrada React/Vite
│   │   ├── index.css             # Estilos globales
│   │   ├── components/
│   │   │   ├── EntradaPanel.jsx  # Textarea + botones de acción
│   │   │   ├── ResultadoPanel.jsx# Tarjetas + tabla + lista de hilos
│   │   │   └── TablaTokens.jsx   # Tabla de tokens con badges AFD/LLM
│   │   └── hooks/
│   │       └── useAnalisis.js    # Hook: lógica HTTP y estado global
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── Dockerfile                # Multi-stage: Node build + Nginx serve
├── docker-compose.yml
├── .env.example
├── README.md
└── informe_tecnico.md
```

---

## 8. Ejemplos de prueba y uso

### Desde la interfaz React (http://localhost:3000)
1. Escribe una ecuación: `2x más 5 es igual a 13`
2. Pulsa **Analizar** (o `Ctrl+Enter`).
3. Observa la tabla de tokens (badge verde = AFD, dorado = LLM),
   las tarjetas de métricas y la lista de hilos concurrentes.

### Desde curl
```bash
# Health check
curl http://localhost:8000/health

# Análisis léxico
curl -X POST http://localhost:8000/api/analizar \
  -H "Content-Type: application/json" \
  -d '{"entrada": "2x más 5 es igual a 13"}'
```

Respuesta (resumen):
```json
{
  "tokens": [
    {"tipo": "NUMERO", "lexema": "2",          "origen": "AFD", "hilo": "Hilo-AFD"},
    {"tipo": "VAR",    "lexema": "x",          "origen": "AFD", "hilo": "Hilo-AFD"},
    {"tipo": "OP_SUMA","lexema": "más",        "origen": "LLM", "hilo": "ThreadPoolExecutor-0_0"},
    {"tipo": "NUMERO", "lexema": "5",          "origen": "AFD", "hilo": "Hilo-AFD"},
    {"tipo": "OP_ASIGNACION","lexema":"es igual a","origen":"LLM","hilo":"ThreadPoolExecutor-0_1"},
    {"tipo": "NUMERO", "lexema": "13",         "origen": "AFD", "hilo": "Hilo-AFD"}
  ],
  "tiempo_total_ms": 108.4,
  "hilos_activos": ["Hilo-AFD", "ThreadPoolExecutor-0_0", "ThreadPoolExecutor-0_1"]
}
```

Otras entradas de prueba:
```
x menos 3 es igual a 7
3y más 4 es igual a 22
10x menos 2 es igual a 18
```

---

## 9. Solución de problemas

**Tokens LLM salen como `DESCONOCIDO`:**
El modelo no está descargado o `OLLAMA_MODEL` en `.env` no coincide
con el nombre en `ollama list`. Ejecuta:
```bash
docker exec -it nlp-math-ollama ollama pull llama3
```

**Error al conectar al backend desde el frontend:**
Verifica que `VITE_BACKEND_URL` en `.env` use `localhost` (no
`ollama` ni otro nombre de servicio Docker interno) y que coincida
con `BACKEND_PORT`. Tras cambiar `.env`, reconstruye con
`docker compose up --build`.

**Puerto ocupado:**
Cambia `BACKEND_PORT` o `FRONTEND_PORT` en `.env` y vuelve a
ejecutar `docker compose up --build`.

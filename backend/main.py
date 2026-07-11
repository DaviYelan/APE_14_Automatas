"""
main.py — Backend Flask
------------------------
Punto de entrada del backend. Expone una API HTTP usando Flask,
reemplazando FastAPI pero manteniendo exactamente la misma lógica
de negocio: LexerEngine, AutomataStrategy y LLMStrategy no cambian.

Rutas:
  GET  /health         -> verificación de salud del servicio
  POST /api/analizar   -> análisis léxico híbrido (AFD + LLM)

Todas las configuraciones (puerto, modelo, etc.) se leen desde .env
mediante python-dotenv. Nada está hardcodeado aquí.
"""

import os

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

from strategies.lexer_engine import LexerEngine

# Carga .env antes de construir cualquier objeto que dependa de él
load_dotenv()

app = Flask(__name__)

# CORS abierto para que el frontend React (puerto distinto) pueda
# consumir la API sin bloqueos durante el desarrollo y en Docker.
CORS(app)

# Instancia única del motor léxico (reutilizada en todas las peticiones)
lexer_engine = LexerEngine()


@app.get("/health")
def health():
    """Verificación de salud del backend."""
    return jsonify({
        "status": "ok",
        "framework": "Flask",
        "modelo_llm": os.getenv("OLLAMA_MODEL", "no-configurado"),
    })


def _procesar_analisis():
    """
    Lógica compartida entre /api/analizar y /compiler/analyze.
    Acepta 'entrada' (español) o 'input' (inglés) como campo del body.
    """
    datos = request.get_json(silent=True)

    if not datos or not isinstance(datos, dict):
        return jsonify({"error": "Se requiere un body JSON con el campo 'entrada' o 'input'."}), 400

    # Acepta tanto "entrada" (nuestro DSL) como "input" (convención del compañero)
    texto = datos.get("entrada") or datos.get("input") or ""
    entrada = texto.strip()
    if not entrada:
        return jsonify({"error": "El campo 'entrada' / 'input' no puede estar vacío."}), 400

    try:
        resultado = lexer_engine.analizar(entrada)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Error en el análisis léxico: {exc}"}), 500

    return jsonify(resultado)


@app.post("/api/analizar")
def analizar():
    """
    Endpoint principal en español.
    Body JSON: { "entrada": "2x más 5 es igual a 13" }
    """
    return _procesar_analisis()


@app.post("/compiler/analyze")
def compiler_analyze():
    """
    Endpoint alternativo en inglés (compatible con la convención del
    compañero de equipo para facilitar comparación de resultados).
    Body JSON: { "input": "2x más 5 es igual a 13" }
              o { "entrada": "2x más 5 es igual a 13" }
    """
    return _procesar_analisis()


if __name__ == "__main__":
    puerto = int(os.getenv("BACKEND_PORT", "8000"))
    # debug=False en producción/Docker; el reload automático lo maneja
    # el propio contenedor si se necesita.
    app.run(host="0.0.0.0", port=puerto, debug=False)

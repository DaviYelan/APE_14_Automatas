// src/App.jsx
// Componente raíz. Compone EntradaPanel + ResultadoPanel usando el
// hook useAnalisis como única fuente de estado de la aplicación.
import React from "react";
import EntradaPanel   from "./components/EntradaPanel";
import ResultadoPanel from "./components/ResultadoPanel";
import { useAnalisis } from "./hooks/useAnalisis";

const estilos = {
  contenedor: {
    maxWidth: 900,
    margin: "0 auto",
    padding: "48px 24px 64px",
  },
  encabezado: {
    borderBottom: "1px solid var(--linea)",
    paddingBottom: 24,
    marginBottom: 32,
  },
  h1: {
    fontFamily: "var(--mono)",
    fontSize: "clamp(1.5rem, 4vw, 2.1rem)",
    fontWeight: 700,
    marginBottom: 8,
    color: "var(--texto)",
    letterSpacing: "-0.01em",
  },
  prefijo: {
    color: "var(--acento)",
  },
  subtitulo: {
    color: "var(--texto-muted)",
    fontSize: "0.98rem",
    marginBottom: 4,
  },
  meta: {
    fontFamily: "var(--mono)",
    fontSize: "0.74rem",
    color: "var(--texto-muted)",
    opacity: 0.7,
  },
  pie: {
    marginTop: 40,
    textAlign: "center",
    fontFamily: "var(--mono)",
    fontSize: "0.72rem",
    color: "var(--texto-muted)",
    opacity: 0.6,
  },
};

export default function App() {
  const {
    entrada, setEntrada,
    resultado, cargando, error,
    analizar, cargarEjemplo,
  } = useAnalisis();

  return (
    <div style={estilos.contenedor}>
      {/* Encabezado */}
      <header style={estilos.encabezado}>
        <h1 style={estilos.h1}>
          <span style={estilos.prefijo}>&gt; </span>
          Mini-Compilador NLP-Math
        </h1>
        <p style={estilos.subtitulo}>
          Analizador léxico híbrido: Autómata Finito Determinista (AFD) + LLM
        </p>
        <p style={estilos.meta}>
          Práctica 12 · Teoría de Autómatas y Computabilidad Avanzada · UNL ·
          Backend: Flask (Python) · Frontend: React + Vite
        </p>
      </header>

      <main>
        {/* Panel de entrada */}
        <EntradaPanel
          entrada={entrada}
          onCambio={setEntrada}
          onAnalizar={analizar}
          onEjemplo={cargarEjemplo}
          cargando={cargando}
        />

        {/* Panel de resultados / error */}
        <ResultadoPanel resultado={resultado} error={error} />
      </main>

      <footer style={estilos.pie}>
        <p>
          Backend: Flask + Python (re · threading · ThreadPoolExecutor) ·
          Frontend: React 18 + Vite
        </p>
      </footer>
    </div>
  );
}

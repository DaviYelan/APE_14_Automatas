// src/components/EntradaPanel.jsx
// Panel de entrada: textarea para la ecuación + botones de acción.
// Recibe todo por props; no tiene estado propio.
import React from "react";

const estilos = {
  panel: {
    background: "var(--bg-panel)",
    border: "1px solid var(--linea)",
    borderRadius: 10,
    padding: 24,
    marginBottom: 24,
  },
  label: {
    display: "block",
    fontFamily: "var(--mono)",
    fontSize: "0.78rem",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    color: "var(--texto-muted)",
    marginBottom: 10,
  },
  textarea: {
    width: "100%",
    background: "var(--bg-base)",
    border: "1px solid var(--linea)",
    borderRadius: 6,
    color: "var(--texto)",
    fontFamily: "var(--mono)",
    fontSize: "1rem",
    padding: "14px",
    resize: "vertical",
    outline: "none",
    transition: "border-color 0.15s",
  },
  acciones: {
    display: "flex",
    gap: 12,
    marginTop: 16,
    flexWrap: "wrap",
  },
  btnPrimario: {
    fontFamily: "var(--mono)",
    fontSize: "0.88rem",
    fontWeight: 700,
    padding: "11px 20px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    background: "var(--acento)",
    color: "#062014",
    transition: "transform 0.1s, background 0.15s",
  },
  btnSecundario: {
    fontFamily: "var(--mono)",
    fontSize: "0.88rem",
    fontWeight: 600,
    padding: "11px 20px",
    borderRadius: 6,
    border: "1px solid var(--linea)",
    cursor: "pointer",
    background: "transparent",
    color: "var(--texto-muted)",
    transition: "border-color 0.15s, color 0.15s",
  },
  estado: {
    marginTop: 14,
    fontFamily: "var(--mono)",
    fontSize: "0.8rem",
    color: "var(--acento)",
    minHeight: "1.2em",
  },
};

export default function EntradaPanel({
  entrada, onCambio, onAnalizar, onEjemplo, cargando,
}) {
  // Ctrl+Enter / Cmd+Enter para analizar sin salir del textarea
  function manejarTecla(e) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      onAnalizar();
    }
  }

  return (
    <section style={estilos.panel}>
      <label style={estilos.label}>Ecuación en lenguaje natural</label>

      <textarea
        rows={3}
        value={entrada}
        onChange={(e) => onCambio(e.target.value)}
        onKeyDown={manejarTecla}
        placeholder="Ej: 2x más 5 es igual a 13"
        style={estilos.textarea}
      />

      <div style={estilos.acciones}>
        <button
          onClick={onAnalizar}
          disabled={cargando}
          style={{
            ...estilos.btnPrimario,
            opacity: cargando ? 0.6 : 1,
            cursor: cargando ? "not-allowed" : "pointer",
          }}
        >
          {cargando ? "Analizando..." : "Analizar"}
        </button>

        <button
          onClick={onEjemplo}
          disabled={cargando}
          style={estilos.btnSecundario}
        >
          Cargar otro ejemplo
        </button>
      </div>

      {cargando && (
        <p style={estilos.estado}>
          ● Ejecutando AFD + LLM concurrente…
        </p>
      )}
    </section>
  );
}

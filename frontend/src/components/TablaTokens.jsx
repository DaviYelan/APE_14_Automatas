// src/components/TablaTokens.jsx
// Tabla que renderiza el flujo de tokens producido por el análisis
// léxico híbrido, distinguiendo visualmente origen AFD vs LLM.
import React from "react";

const estilos = {
  tabla: {
    width: "100%",
    borderCollapse: "collapse",
    fontFamily: "var(--mono)",
    fontSize: "0.84rem",
  },
  th: {
    textAlign: "left",
    padding: "8px 10px",
    color: "var(--texto-muted)",
    borderBottom: "1px solid var(--linea)",
    fontWeight: 600,
    fontSize: "0.71rem",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  td: {
    padding: "9px 10px",
    borderBottom: "1px solid var(--linea)",
    color: "var(--texto)",
    verticalAlign: "middle",
  },
};

// Badge de color según el origen del token (AFD = verde, LLM = dorado)
function BadgeOrigen({ origen }) {
  const estaAFD = origen === "AFD";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 4,
        fontSize: "0.71rem",
        fontWeight: 700,
        background: estaAFD ? "var(--acento-bg)" : "var(--llm-bg)",
        color: estaAFD ? "var(--acento)" : "var(--llm)",
      }}
    >
      {origen}
    </span>
  );
}

export default function TablaTokens({ tokens }) {
  if (!tokens || tokens.length === 0) return null;

  return (
    <table style={estilos.tabla}>
      <thead>
        <tr>
          {["#", "Lexema", "Token", "Valor", "Origen", "Hilo", "ms"].map(
            (col) => (
              <th key={col} style={estilos.th}>{col}</th>
            )
          )}
        </tr>
      </thead>
      <tbody>
        {tokens.map((tok, i) => {
          const esError = tok.tipo === "UNKNOWN";
          const bgFila  = esError
            ? "rgba(227,92,92,0.08)"
            : i % 2 === 0 ? "transparent" : "var(--bg-panel-alt, #161b17)";
          return (
            <tr key={i} style={{ background: bgFila }}>
              <td style={estilos.td}>{i + 1}</td>
              <td style={{
                ...estilos.td,
                color: esError ? "var(--error, #e35c5c)" : "var(--acento)",
                fontWeight: 700,
              }}>
                {tok.lexema}
              </td>
              <td style={{
                ...estilos.td,
                color: esError ? "var(--error, #e35c5c)" : "inherit",
                fontWeight: esError ? 700 : "normal",
              }}>
                {tok.tipo}
              </td>
              <td style={estilos.td}>{String(tok.valor)}</td>
              <td style={estilos.td}>
                <BadgeOrigen origen={tok.fuente || tok.origen} />
              </td>
              <td style={{ ...estilos.td, color: "var(--texto-muted)", fontSize: "0.78rem" }}>
                {tok.hilo}
              </td>
              <td style={estilos.td}>{tok.tiempo_ms}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

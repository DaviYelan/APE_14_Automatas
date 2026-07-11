// src/components/PanelSemantico.jsx
// Muestra el resultado del análisis semántico Java:
//   - Tabla de símbolos (variables, coeficientes)
//   - Solución de la ecuación (si existe)
//   - Errores semánticos con explicación del LLM
import React from "react";

const mono = { fontFamily: "var(--mono)" };

const estilos = {
  wrapper: {
    marginTop: 4,
  },
  exitoso: {
    background: "rgba(92,227,154,0.07)",
    border: "1px solid rgba(92,227,154,0.4)",
    borderRadius: 8,
    padding: "18px 20px",
    marginBottom: 12,
  },
  exitosoTitulo: {
    ...mono,
    fontSize: "0.82rem",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: "var(--acento)",
    marginBottom: 14,
    fontWeight: 700,
  },
  solucionBox: {
    display: "inline-flex",
    alignItems: "center",
    gap: 10,
    background: "rgba(92,227,154,0.12)",
    border: "1px solid var(--acento)",
    borderRadius: 8,
    padding: "10px 20px",
    marginBottom: 16,
  },
  solucionLabel: {
    ...mono,
    fontSize: "0.78rem",
    color: "var(--texto-muted)",
    textTransform: "uppercase",
  },
  solucionValor: {
    ...mono,
    fontSize: "1.6rem",
    fontWeight: 700,
    color: "var(--acento)",
  },
  tablaWrapper: {
    overflowX: "auto",
  },
  tabla: {
    width: "100%",
    borderCollapse: "collapse",
    ...mono,
    fontSize: "0.82rem",
  },
  th: {
    textAlign: "left",
    padding: "7px 12px",
    color: "var(--texto-muted)",
    borderBottom: "1px solid var(--linea)",
    fontSize: "0.7rem",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  td: {
    padding: "8px 12px",
    borderBottom: "1px solid var(--linea)",
    color: "var(--texto)",
  },
  errorWrapper: {
    background: "rgba(180,92,227,0.06)",
    border: "1px solid rgba(180,92,227,0.4)",
    borderRadius: 8,
    padding: "16px 18px",
  },
  errorTitulo: {
    ...mono,
    fontSize: "0.78rem",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: "#b45ce3",
    marginBottom: 12,
    fontWeight: 700,
  },
  errorItem: {
    ...mono,
    fontSize: "0.82rem",
    borderBottom: "1px solid rgba(180,92,227,0.2)",
    paddingBottom: 10,
    marginBottom: 10,
  },
  noDisponible: {
    ...mono,
    fontSize: "0.82rem",
    color: "var(--texto-muted)",
    padding: "10px 14px",
    background: "var(--bg-panel-alt,#161b17)",
    borderRadius: 6,
    border: "1px solid var(--linea)",
  },
};

function TablaSimbolos({ tabla }) {
  if (!tabla) return null;
  const { variables, variablesUnicas, terminoIndependiente, tipoEcuacion } = tabla;

  return (
    <div style={estilos.tablaWrapper}>
      <table style={estilos.tabla}>
        <thead>
          <tr>
            {["Variable", "Coeficiente neto", "Tipo"].map(h => (
              <th key={h} style={estilos.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {variablesUnicas && variablesUnicas.map(v => (
            <tr key={v}>
              <td style={{ ...estilos.td, color: "var(--acento)", fontWeight: 700 }}>{v}</td>
              <td style={estilos.td}>{variables?.[v] ?? "?"}</td>
              <td style={{ ...estilos.td, color: "var(--texto-muted)" }}>variable</td>
            </tr>
          ))}
          <tr>
            <td style={{ ...estilos.td, color: "var(--texto-muted)" }}>constante neta</td>
            <td style={estilos.td}>{terminoIndependiente ?? 0}</td>
            <td style={{ ...estilos.td, color: "var(--texto-muted)" }}>
              {tipoEcuacion ?? "—"}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export default function PanelSemantico({ semanticoValido, tablaSimbolos, solucion, erroresSemanticos }) {
  // No renderizar nada si el análisis semántico no se ejecutó
  if (semanticoValido === null || semanticoValido === undefined) {
    return (
      <div style={estilos.noDisponible}>
        Análisis semántico no ejecutado — requiere fase léxica y sintáctica sin errores.
      </div>
    );
  }

  // Caso error semántico
  if (!semanticoValido && erroresSemanticos && erroresSemanticos.length > 0) {
    return (
      <div style={estilos.errorWrapper}>
        <div style={estilos.errorTitulo}>
          ✗ {erroresSemanticos.length} error{erroresSemanticos.length > 1 ? "es" : ""} semántico{erroresSemanticos.length > 1 ? "s" : ""} detectado{erroresSemanticos.length > 1 ? "s" : ""}
        </div>
        {erroresSemanticos.map((err, i) => (
          <div key={i} style={{
            ...estilos.errorItem,
            borderBottom: i < erroresSemanticos.length - 1
              ? "1px solid rgba(180,92,227,0.2)" : "none",
          }}>
            <div style={{ marginBottom: 4 }}>
              <span style={{ color: "var(--texto-muted)", fontSize: "0.7rem",
                textTransform: "uppercase", marginRight: 8 }}>
                Código:
              </span>
              <span style={{ color: "#b45ce3", fontWeight: 700 }}>{err.codigo}</span>
            </div>
            <div style={{ color: "var(--texto-muted)", marginBottom: 6 }}>
              ↳ {err.causa}
            </div>
            {err.mensajeLLM && err.mensajeLLM !== err.causa && (
              <div style={{
                background: "rgba(180,92,227,0.08)",
                border: "1px solid rgba(180,92,227,0.2)",
                borderRadius: 5,
                padding: "8px 12px",
                color: "var(--texto)",
                fontSize: "0.82rem",
              }}>
                <span style={{ color: "#b45ce3", fontSize: "0.69rem",
                  textTransform: "uppercase", marginRight: 6 }}>LLM →</span>
                {err.mensajeLLM}
              </div>
            )}
          </div>
        ))}
        {tablaSimbolos && (
          <>
            <div style={{ ...estilos.errorTitulo, marginTop: 14 }}>
              Tabla de símbolos (parcial)
            </div>
            <TablaSimbolos tabla={tablaSimbolos} />
          </>
        )}
      </div>
    );
  }

  // Caso exitoso
  return (
    <div style={estilos.exitoso}>
      <div style={estilos.exitosoTitulo}>✓ Ecuación semánticamente válida</div>

      {solucion !== null && solucion !== undefined && tablaSimbolos?.variablesUnicas?.length > 0 && (
        <div style={estilos.solucionBox}>
          <span style={estilos.solucionLabel}>Solución:</span>
          <span style={estilos.solucionValor}>
            {tablaSimbolos.variablesUnicas[0]} = {Number(solucion).toFixed(4).replace(/\.?0+$/, "")}
          </span>
        </div>
      )}

      <div style={{ ...mono, fontSize: "0.78rem", color: "var(--texto-muted)", marginBottom: 10 }}>
        Tabla de símbolos
      </div>
      <TablaSimbolos tabla={tablaSimbolos} />
    </div>
  );
}

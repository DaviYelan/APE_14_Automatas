// src/components/ArbolSintactico.jsx
// Renderiza el AST JSON como un árbol visual indentado con colores
// por tipo de nodo. Sin librerías externas, solo CSS en JS.
import React, { useState } from "react";

const COLORES_NODO = {
  ECUACION:  { bg: "rgba(92,227,154,0.15)",  border: "var(--acento)",         label: "ECUACIÓN" },
  BINOP:     { bg: "rgba(227,196,92,0.15)",  border: "var(--llm,#e3c45c)",    label: "OP. BINARIA" },
  TERMINO:   { bg: "rgba(92,154,227,0.15)",  border: "#5c9ae3",               label: "TÉRMINO" },
  NUMERO:    { bg: "rgba(154,92,227,0.12)",  border: "#9a5ce3",               label: "NÚMERO" },
  VAR:       { bg: "rgba(92,227,196,0.12)",  border: "#5ce3c4",               label: "VARIABLE" },
  DEFAULT:   { bg: "rgba(255,255,255,0.05)", border: "var(--linea)",          label: "NODO" },
};

function NodoArbol({ nodo, nivel = 0 }) {
  const [expandido, setExpandido] = useState(true);
  if (!nodo || typeof nodo !== "object") return null;

  const cfg = COLORES_NODO[nodo.nodo] || COLORES_NODO.DEFAULT;
  const sangria = nivel * 24;
  const tieneHijos = nodo.izquierda || nodo.derecha || nodo.terminos;

  return (
    <div style={{ marginLeft: sangria, marginBottom: 6 }}>
      {/* Cabecera del nodo */}
      <div
        onClick={() => tieneHijos && setExpandido(!expandido)}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          background: cfg.bg,
          border: `1px solid ${cfg.border}`,
          borderRadius: 6,
          padding: "5px 12px",
          cursor: tieneHijos ? "pointer" : "default",
          fontFamily: "var(--mono)",
          fontSize: "0.8rem",
          userSelect: "none",
        }}
      >
        {tieneHijos && (
          <span style={{ color: cfg.border, fontSize: "0.7rem" }}>
            {expandido ? "▼" : "▶"}
          </span>
        )}
        <span style={{ color: cfg.border, fontWeight: 700 }}>
          {cfg.label}
        </span>
        {/* Datos inline del nodo según su tipo */}
        {nodo.operador && (
          <span style={{ color: "var(--texto-muted)" }}>
            op: <span style={{ color: "var(--texto)" }}>"{nodo.operador}"</span>
          </span>
        )}
        {nodo.valor !== undefined && (
          <span style={{ color: "var(--texto-muted)" }}>
            val: <span style={{ color: "var(--texto)" }}>{nodo.valor}</span>
          </span>
        )}
        {nodo.nombre && (
          <span style={{ color: "var(--texto-muted)" }}>
            nombre: <span style={{ color: "var(--texto)" }}>{nodo.nombre}</span>
          </span>
        )}
        {nodo.representacion && (
          <span style={{ color: "var(--texto-muted)" }}>
            → <span style={{ color: cfg.border }}>{nodo.representacion}</span>
          </span>
        )}
      </div>

      {/* Hijos recursivos */}
      {expandido && (
        <div style={{ marginTop: 4 }}>
          {nodo.izquierda && (
            <div>
              <span style={{
                fontFamily: "var(--mono)", fontSize: "0.69rem",
                color: "var(--texto-muted)", marginLeft: 24 + sangria,
                display: "block", marginBottom: 2,
              }}>
                izquierda →
              </span>
              <NodoArbol nodo={nodo.izquierda} nivel={nivel + 1} />
            </div>
          )}
          {nodo.derecha && (
            <div style={{ marginTop: 4 }}>
              <span style={{
                fontFamily: "var(--mono)", fontSize: "0.69rem",
                color: "var(--texto-muted)", marginLeft: 24 + sangria,
                display: "block", marginBottom: 2,
              }}>
                derecha →
              </span>
              <NodoArbol nodo={nodo.derecha} nivel={nivel + 1} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ArbolSintactico({ arbol, erroresSintacticos }) {
  const mono = { fontFamily: "var(--mono)" };

  if (erroresSintacticos && erroresSintacticos.length > 0) {
    return (
      <div style={{
        background: "rgba(227,92,92,0.06)",
        border: "1px solid rgba(227,92,92,0.4)",
        borderRadius: 8, padding: "14px 18px",
      }}>
        <div style={{
          ...mono, fontSize: "0.78rem", textTransform: "uppercase",
          letterSpacing: "0.05em", color: "var(--error,#e35c5c)", marginBottom: 10,
        }}>
          ✗ Árbol no generado — errores sintácticos
        </div>
        {erroresSintacticos.map((e, i) => (
          <div key={i} style={{
            ...mono, fontSize: "0.82rem",
            borderBottom: i < erroresSintacticos.length - 1
              ? "1px solid rgba(227,92,92,0.2)" : "none",
            paddingBottom: 8, marginBottom: 8,
          }}>
            <span style={{ color: "var(--error,#e35c5c)", fontWeight: 700 }}>
              token '{e.token}'
            </span>
            <span style={{ color: "var(--texto-muted)" }}> — esperado: </span>
            <span style={{ color: "var(--texto)" }}>{e.esperado}</span>
            <div style={{ color: "var(--texto-muted)", marginTop: 2 }}>
              ↳ {e.causa}
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!arbol) {
    return (
      <div style={{
        ...mono, fontSize: "0.82rem",
        color: "var(--texto-muted)",
        padding: "10px 14px",
        background: "var(--bg-panel-alt,#161b17)",
        borderRadius: 6, border: "1px solid var(--linea)",
      }}>
        null — árbol no disponible
      </div>
    );
  }

  return (
    <div style={{
      background: "var(--bg-panel-alt,#161b17)",
      border: "1px solid var(--linea)",
      borderRadius: 8, padding: "16px",
      overflowX: "auto",
    }}>
      <NodoArbol nodo={arbol} nivel={0} />
      <div style={{
        fontFamily: "var(--mono)", fontSize: "0.69rem",
        color: "var(--texto-muted)", marginTop: 12,
        borderTop: "1px solid var(--linea)", paddingTop: 8,
      }}>
        Haz clic en los nodos para expandir/contraer. 
        Gramática: ecuacion → expresion OP_ASIGNACION expresion
      </div>
    </div>
  );
}

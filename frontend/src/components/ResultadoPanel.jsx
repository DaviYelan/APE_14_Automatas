// src/components/ResultadoPanel.jsx
// Panel de resultados: métricas, errores léxicos, sintácticos y semánticos,
// tabla de tokens, AST interactivo, análisis semántico, tiempos y hilos.
import React from "react";
import TablaTokens from "./TablaTokens";
import ArbolSintactico from "./ArbolSintactico";
import PanelSemantico from "./PanelSemantico";

const estilos = {
  panel: {
    background: "var(--bg-panel)",
    border: "1px solid var(--linea)",
    borderRadius: 10,
    padding: 24,
  },
  h2: {
    fontFamily: "var(--mono)",
    fontSize: "1.05rem",
    marginBottom: 20,
    color: "var(--texto)",
  },
  h3: {
    fontFamily: "var(--mono)",
    fontSize: "0.82rem",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: "var(--texto-muted)",
    margin: "28px 0 12px",
  },
  grid4: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 12,
  },
  grid5: {
    display: "grid",
    gridTemplateColumns: "repeat(5, 1fr)",
    gap: 10,
    marginTop: 12,
  },
  tarjeta: {
    background: "var(--bg-panel-alt, #161b17)",
    border: "1px solid var(--linea)",
    borderRadius: 8,
    padding: "14px 16px",
    display: "flex",
    flexDirection: "column",
    gap: 6,
  },
  tarjetaLabel: {
    fontFamily: "var(--mono)",
    fontSize: "0.69rem",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: "var(--texto-muted)",
  },
  tarjetaValor: {
    fontFamily: "var(--mono)",
    fontSize: "1.3rem",
    fontWeight: 700,
    color: "var(--acento)",
  },
  tarjetaValorSmall: {
    fontFamily: "var(--mono)",
    fontSize: "1rem",
    fontWeight: 700,
    color: "var(--llm, #e3c45c)",
  },
  // Panel de errores léxicos (se muestra solo si hay errores)
  erroresWrapper: {
    background: "rgba(227,92,92,0.06)",
    border: "1px solid rgba(227,92,92,0.4)",
    borderRadius: 8,
    padding: "16px 18px",
    marginTop: 20,
  },
  erroresTitulo: {
    fontFamily: "var(--mono)",
    fontSize: "0.78rem",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: "var(--error, #e35c5c)",
    marginBottom: 12,
  },
  errorItem: {
    fontFamily: "var(--mono)",
    fontSize: "0.82rem",
    borderBottom: "1px solid rgba(227,92,92,0.2)",
    paddingBottom: 10,
    marginBottom: 10,
  },
  errorToken: {
    color: "var(--error, #e35c5c)",
    fontWeight: 700,
  },
  errorCausa: {
    color: "var(--texto-muted)",
    marginTop: 2,
  },
  errorSugerencia: {
    color: "var(--texto)",
    marginTop: 2,
  },
  listaHilos: {
    listStyle: "none",
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
  },
  itemHilo: {
    fontFamily: "var(--mono)",
    fontSize: "0.78rem",
    background: "var(--bg-panel-alt, #161b17)",
    border: "1px solid var(--linea)",
    borderRadius: 5,
    padding: "5px 10px",
    color: "var(--texto)",
  },
  fetchError: {
    background: "rgba(227,92,92,0.08)",
    border: "1px solid rgba(227,92,92,0.35)",
    borderRadius: 10,
    padding: "18px 20px",
    fontFamily: "var(--mono)",
    fontSize: "0.88rem",
    color: "var(--error, #e35c5c)",
  },
};

function Tarjeta({ label, valor, pequeño = false }) {
  return (
    <div style={estilos.tarjeta}>
      <span style={estilos.tarjetaLabel}>{label}</span>
      <span style={pequeño ? estilos.tarjetaValorSmall : estilos.tarjetaValor}>
        {valor}
      </span>
    </div>
  );
}

function PanelErrores({ errores }) {
  if (!errores || errores.length === 0) return null;
  return (
    <div style={estilos.erroresWrapper}>
      <div style={estilos.erroresTitulo}>
        ⚠ {errores.length} error{errores.length > 1 ? "es" : ""} léxico{errores.length > 1 ? "s" : ""} detectado{errores.length > 1 ? "s" : ""}
      </div>
      {errores.map((err, i) => (
        <div key={i} style={estilos.errorItem}>
          <div>
            <span style={estilos.tarjetaLabel}>Fase: </span>
            <span style={{ fontFamily: "var(--mono)", fontSize: "0.82rem" }}>{err.fase}</span>
            {"  "}
            <span style={estilos.tarjetaLabel}>Token: </span>
            <span style={estilos.errorToken}>'{err.token}'</span>
          </div>
          <div style={estilos.errorCausa}>↳ {err.causa}</div>
          <div style={estilos.errorSugerencia}>💡 {err.sugerencia}</div>
        </div>
      ))}
    </div>
  );
}

export default function ResultadoPanel({ resultado, error }) {
  if (error) {
    return <div style={estilos.fetchError}>Error de conexión: {error}</div>;
  }
  if (!resultado) return null;

  const tiempos = resultado.tiempos || {};

  // Separar errores por fase
  const erroresLexicos     = (resultado.errores || []).filter(e => e.fase === "lexical");
  const erroresSintacticos = (resultado.errores || []).filter(e => e.fase === "sintactico");
  const erroresSemanticos  = (resultado.errores || []).filter(e => e.fase === "semantico");

  const etiquetaEstado = erroresLexicos.length > 0
    ? "— errores léxicos"
    : erroresSintacticos.length > 0
      ? "— errores sintácticos"
      : erroresSemanticos.length > 0
        ? "— errores semánticos"
        : resultado.arbol_sintactico
          ? resultado.semantico_valido
            ? "— ✓ compilación exitosa"
            : "— análisis semántico pendiente"
          : "";

  return (
    <section style={estilos.panel}>
      <h2 style={estilos.h2}>
        Resultado del Análisis
        {etiquetaEstado && (
          <span style={{
            fontSize: "0.85rem", marginLeft: 12,
            color: resultado.arbol_sintactico
              ? "var(--acento)"
              : "var(--error, #e35c5c)",
          }}>
            {etiquetaEstado}
          </span>
        )}
      </h2>

      {/* Tarjetas de métricas principales */}
      <div style={estilos.grid4}>
        <Tarjeta label="Tiempo total"  valor={`${tiempos.total_ms ?? "-"} ms`} />
        <Tarjeta label="Tokens AFD"    valor={resultado.tokens_afd_count} />
        <Tarjeta label="Tokens LLM"    valor={resultado.tokens_llm_count} />
        <Tarjeta label="Hilos activos" valor={resultado.hilos_activos.length} />
      </div>

      {/* Errores léxicos */}
      <PanelErrores errores={erroresLexicos} />

      {/* Errores sintácticos (panel separado, color diferente) */}
      {erroresSintacticos.length > 0 && (
        <div style={{ ...estilos.erroresWrapper, marginTop: 12,
          background: "rgba(227,150,92,0.06)",
          border: "1px solid rgba(227,150,92,0.4)" }}>
          <div style={{ ...estilos.erroresTitulo, color: "#e3965c" }}>
            ⚠ {erroresSintacticos.length} error{erroresSintacticos.length > 1 ? "es" : ""} sintáctico{erroresSintacticos.length > 1 ? "s" : ""} detectado{erroresSintacticos.length > 1 ? "s" : ""}
          </div>
          {erroresSintacticos.map((err, i) => (
            <div key={i} style={{ ...estilos.errorItem, borderColor: "rgba(227,150,92,0.2)" }}>
              <div>
                <span style={estilos.tarjetaLabel}>Fase: </span>
                <span style={{ fontFamily: "var(--mono)", fontSize: "0.82rem" }}>{err.fase}</span>
                {"  "}
                <span style={estilos.tarjetaLabel}>Token: </span>
                <span style={{ ...estilos.errorToken, color: "#e3965c" }}>'{err.token}'</span>
                {"  "}
                <span style={estilos.tarjetaLabel}>Esperado: </span>
                <span style={{ fontFamily: "var(--mono)", fontSize: "0.82rem",
                  color: "var(--texto)" }}>{err.esperado}</span>
              </div>
              <div style={estilos.errorCausa}>↳ {err.causa}</div>
            </div>
          ))}
        </div>
      )}

      {/* Flujo de Tokens */}
      <h3 style={estilos.h3}>Flujo de Tokens</h3>
      <TablaTokens tokens={resultado.tokens} />

      {/* Árbol Sintáctico interactivo */}
      <h3 style={estilos.h3}>Árbol Sintáctico (AST)</h3>
      <ArbolSintactico
        arbol={resultado.arbol_sintactico}
        erroresSintacticos={erroresSintacticos}
      />

      {/* Análisis Semántico (Java) */}
      <h3 style={estilos.h3}>Análisis Semántico</h3>
      <PanelSemantico
        semanticoValido={resultado.semantico_valido}
        tablaSimbolos={resultado.tabla_simbolos}
        solucion={resultado.solucion}
        erroresSemanticos={erroresSemanticos}
      />

      {/* Desglose de tiempos por fase */}
      <h3 style={estilos.h3}>Tiempos por fase (ms)</h3>
      <div style={estilos.grid5}>
        <Tarjeta pequeño label="Total"     valor={tiempos.total_ms  ?? "-"} />
        <Tarjeta pequeño label="Lexer"     valor={tiempos.lexer_ms  ?? "-"} />
        <Tarjeta pequeño label="LLM"       valor={tiempos.llm_ms    ?? "-"} />
        <Tarjeta pequeño label="Parser"    valor={tiempos.parser_ms ?? "-"} />
        <Tarjeta pequeño label="Semántico" valor={tiempos.semantic_ms ?? "-"} />
      </div>

      {/* Hilos concurrentes evidenciados */}
      <h3 style={estilos.h3}>Hilos concurrentes evidenciados</h3>
      <ul style={estilos.listaHilos}>
        {resultado.hilos_activos.map((hilo) => (
          <li key={hilo} style={estilos.itemHilo}>⚡ {hilo}</li>
        ))}
      </ul>
    </section>
  );
}

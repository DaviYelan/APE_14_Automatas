// src/hooks/useAnalisis.js
// Hook personalizado que encapsula toda la lógica de comunicación
// con el backend Flask. Los componentes solo consumen estado y callbacks,
// sin saber nada del protocolo HTTP o de la URL del backend.
import { useState, useCallback } from "react";

// La URL del backend viene de la variable de entorno embebida por Vite
// en tiempo de build (VITE_BACKEND_URL en .env). Nunca hardcodeada.
const BACKEND_URL =
  typeof __BACKEND_URL__ !== "undefined"
    ? __BACKEND_URL__
    : import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const EJEMPLOS = [
  "2x más 5 es igual a 13",
  "x menos 3 es igual a 7",
  "3y más 4 es igual a 22",
  "10x menos 2 es igual a 18",
];

export function useAnalisis() {
  const [entrada, setEntrada]       = useState(EJEMPLOS[0]);
  const [resultado, setResultado]   = useState(null);
  const [cargando, setCargando]     = useState(false);
  const [error, setError]           = useState(null);
  const [ejemploIdx, setEjemploIdx] = useState(0);

  const analizar = useCallback(async () => {
    const texto = entrada.trim();
    if (!texto) return;

    setCargando(true);
    setError(null);
    setResultado(null);

    try {
      const res = await fetch(`${BACKEND_URL}/api/analizar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entrada: texto }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}`);
      }

      setResultado(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }, [entrada]);

  const cargarEjemplo = useCallback(() => {
    const siguiente = (ejemploIdx + 1) % EJEMPLOS.length;
    setEjemploIdx(siguiente);
    setEntrada(EJEMPLOS[siguiente]);
    setResultado(null);
    setError(null);
  }, [ejemploIdx]);

  return {
    entrada, setEntrada,
    resultado, cargando, error,
    analizar, cargarEjemplo,
  };
}

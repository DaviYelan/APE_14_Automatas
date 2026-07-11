// vite.config.js
// La URL del backend se lee de la variable de entorno VITE_BACKEND_URL
// que docker-compose inyecta en tiempo de build desde el .env.
// Durante desarrollo local, el proxy redirige /api/* al backend Flask.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    proxy: {
      // En desarrollo local, redirige las llamadas al backend Flask
      "/api": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  // En producción (docker build), el BACKEND_URL se embebe como variable
  // de entorno estática accesible mediante import.meta.env.VITE_BACKEND_URL
  define: {
    __BACKEND_URL__: JSON.stringify(
      process.env.VITE_BACKEND_URL || "http://localhost:8000"
    ),
  },
});

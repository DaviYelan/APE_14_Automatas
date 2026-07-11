# Dockerfile — Frontend React (Multi-stage build)
#
# Stage 1 — BUILD: compila la app React con Vite.
# La variable VITE_BACKEND_URL se inyecta en tiempo de build desde
# docker-compose (--build-arg), de modo que Vite la embebe en el
# bundle estático. Nunca hardcodeada en el código fuente.
FROM node:20-alpine AS build

WORKDIR /app

# Argumento de build que viene de docker-compose (variable .env)
ARG VITE_BACKEND_URL=http://localhost:8000
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

COPY package.json .
RUN npm install

COPY . .
RUN npm run build

# Stage 2 — SERVE: sirve los archivos estáticos compilados con Nginx.
# La imagen final no contiene Node.js ni el código fuente, solo el
# bundle optimizado (dist/), reduciendo la superficie de la imagen.
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# Dockerfile — Backend Flask (Mini-Compilador NLP-Math)
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencias primero para aprovechar caché de capas Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente del backend
COPY . .

EXPOSE 8000

CMD ["python", "main.py"]

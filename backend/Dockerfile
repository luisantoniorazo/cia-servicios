# ==========================================
# Dockerfile para Backend (FastAPI + Python)
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Copiar código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 8001

# Comando para iniciar
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]

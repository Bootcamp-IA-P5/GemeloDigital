# Usar una imagen oficial de Python compatible con Debian
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin/:$PATH"

# Copiar archivos de dependencias
COPY pyproject.toml .
RUN uv sync --no-dev

# El código se montará vía volumen en docker-compose, pero establecemos el PYTHONPATH
ENV PYTHONPATH="/app"

# Comando por defecto
CMD ["uv", "run", "python", "livekit_agent.py", "dev"]

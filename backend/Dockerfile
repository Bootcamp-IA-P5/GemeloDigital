# ============================================================
# Gemelo Cognitivo — Backend Dockerfile
# ============================================================
# Multi-stage: instala deps del sistema + Python deps + app
# ============================================================

FROM python:3.11-slim

# No generar .pyc y mostrar prints al instante
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ── Dependencias del sistema ──────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencias Python ──────────────────────
# Copiar ambos requirements (raíz para agents, backend para el API)
COPY requirements.txt /app/requirements.txt
COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# ── Código fuente ─────────────────────────────
COPY backend/ /app/backend/
COPY agents/ /app/agents/
COPY ml/ /app/ml/
COPY data/ /app/data/

# ── Exponer puerto ────────────────────────────
EXPOSE 8000

# ── Comando de arranque ──────────────────────
# --host 0.0.0.0 permite conexiones desde fuera del contenedor
# --reload para desarrollo (quitar en producción)
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

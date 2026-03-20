# Imagen base ligera de Python
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias para PostgreSQL y herramientas básicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y el resto del código
# Nota: docker-compose suele montar los volúmenes, pero esto es para una build limpia
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer el puerto del backend (según docker-compose es el 8000)
EXPOSE 8000

# Script de arranque (ajustado para que encuentre 'app')
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

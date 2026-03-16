#!/bin/bash
# Script para arrancar el backend con el PYTHONPATH correcto
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
echo "🚀 Iniciando el backend con el path: $PYTHONPATH"
uvicorn app.main:app --reload --port 8888

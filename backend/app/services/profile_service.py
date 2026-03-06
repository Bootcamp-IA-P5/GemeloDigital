"""
Profile Service — Lógica de negocio del perfil cognitivo
========================================================
Funciones para crear y consultar perfiles cognitivos.
Actualmente usa datos stub en memoria; en producción delegará
al Profiling Agent via el orchestrator.

Para uso del compañero de backend:
  - Reemplazar PROFILES_DB por queries a la tabla `profiles`
  - Integrar la llamada al Profiling Agent (agents/profiling_agent.py)
  - Conectar con el orchestrator para la pipeline completa
"""

import uuid

# ──────────────────────────────────────────────
# BASE DE DATOS STUB (en memoria)
# ──────────────────────────────────────────────
PROFILES_DB: dict[str, dict] = {}


# ──────────────────────────────────────────────
# CREAR PERFIL COGNITIVO
# ──────────────────────────────────────────────

def create_profile(user_id: str, respuestas: dict) -> dict:
    """
    Crea un perfil cognitivo a partir de las respuestas del cuestionario.

    En producción:
      1. Envía raw_answers al Profiling Agent (LLM)
      2. El agente analiza y genera un competency_profile
      3. Se persiste en la tabla `profiles`

    Actualmente devuelve un perfil stub con competencias de ejemplo.
    """
    perfil_id = str(uuid.uuid4())

    # Perfil stub — simula la salida del Profiling Agent
    profile = {
        "user_id": user_id,
        "perfil_id": perfil_id,
        "competencias": [
            {
                "competencia_id": "comp-python",
                "nombre": "Programación en Python",
                "nivel": "medio",
                "puntuacion": 0.65,
            },
            {
                "competencia_id": "comp-ml",
                "nombre": "Machine Learning",
                "nivel": "bajo",
                "puntuacion": 0.30,
            },
            {
                "competencia_id": "comp-data",
                "nombre": "Análisis de Datos",
                "nivel": "alto",
                "puntuacion": 0.85,
            },
        ],
        "enfoque_recomendado": "GENERALISTA",
        "resumen": (
            "El usuario muestra fortalezas en análisis de datos y un nivel "
            "intermedio en Python. Se recomienda una trayectoria generalista "
            "para reforzar las competencias de ML antes de especializar."
        ),
    }

    PROFILES_DB[user_id] = profile
    return profile


# ──────────────────────────────────────────────
# OBTENER PERFIL
# ──────────────────────────────────────────────

def get_profile(user_id: str) -> dict | None:
    """
    Obtiene el perfil cognitivo de un usuario.
    Devuelve None si no existe.

    TODO: Consultar tabla `profiles` en PostgreSQL.
    """
    return PROFILES_DB.get(user_id)

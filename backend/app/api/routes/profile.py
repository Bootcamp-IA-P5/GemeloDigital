"""
Profile API Routes — Perfil Cognitivo
======================================
Endpoints FastAPI para la gestión del perfil cognitivo del usuario.
Orquesta el Profiling Agent para analizar las respuestas del cuestionario
y generar un competency_profile personalizado.

Para uso del compañero de backend:
  - Importar este router en main.py:
    from app.api.routes.profile import router as profile_router
    app.include_router(profile_router, prefix="/api/profile")
  - Configurar la dependencia get_db() para inyectar la sesión de BD
  - Conectar con el orchestrator para la pipeline del Profiling Agent
"""

from fastapi import APIRouter, HTTPException

from ..schemas import (
    QuestionnaireAnswers,
    CompetencyProfile,
)
from ...services import profile_service

router = APIRouter(tags=["Perfil"])


# ──────────────────────────────────────────────
# CREAR — Generar perfil cognitivo
# ──────────────────────────────────────────────

@router.post(
    "/",
    response_model=CompetencyProfile,
    status_code=201,
    summary="Crear perfil cognitivo",
)
def create_profile(body: QuestionnaireAnswers):
    """
    Recibe las respuestas del cuestionario del frontend y genera
    el perfil cognitivo del usuario.

    Pipeline:
      1. Recibe raw_answers del cuestionario
      2. Envía al Profiling Agent (LLM) via orchestrator
      3. El agente analiza competencias y genera puntuaciones
      4. Devuelve el competency_profile con enfoque recomendado

    Respuestas:
      - 201: Perfil creado → CompetencyProfile
      - 400: Datos del cuestionario inválidos
    """
    profile = profile_service.create_profile(
        user_id=body.user_id,
        answers=body,
    )
    return profile


# ──────────────────────────────────────────────
# CONSULTAR — Obtener perfil de un usuario
# ──────────────────────────────────────────────

@router.get(
    "/{user_id}",
    response_model=CompetencyProfile,
    summary="Obtener perfil cognitivo de un usuario",
)
def get_profile(user_id: str):
    """
    Obtiene el perfil cognitivo almacenado de un usuario.

    Respuestas:
      - 200: Perfil encontrado → CompetencyProfile
      - 404: Usuario sin perfil cognitivo
    """
    profile = profile_service.get_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró perfil cognitivo para el usuario '{user_id}'",
        )
    return profile

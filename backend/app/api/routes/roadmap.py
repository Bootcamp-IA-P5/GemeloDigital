"""
Roadmap API Routes — Roadmap Personalizado
============================================
Endpoints FastAPI para la generación y gestión de roadmaps
de aprendizaje personalizados.

Orquesta la pipeline completa:
  Profiling Agent → RAG (ChromaDB) → Planning Agent → ML Predict → Explanatory Agent

Para uso del compañero de backend:
  - Importar este router en main.py:
    from app.api.routes.roadmap import router as roadmap_router
    app.include_router(roadmap_router, prefix="/api/roadmap")
  - Configurar la dependencia get_db() para inyectar la sesión de BD
  - Conectar con el orchestrator para la pipeline completa
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.models import User

from ..schemas import (
    RoadmapGenerateRequest,
    RoadmapResponse,
    AlternativesResponse,
    BlockProgressUpdate,
    MessageResponse,
)
from ...services import roadmap_service

router = APIRouter(tags=["Roadmap"])


@router.get(
    "",
    response_model=RoadmapResponse,
    summary="Obtener roadmap del usuario actual (Usado por Dashboard)",
)
def get_current_user_roadmap(current_user: User = Depends(get_current_user)):
    """
    Obtiene el roadmap activo del usuario que tiene la sesión iniciada.
    """
    profile = roadmap_service.get_current_roadmap(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No se encontró un roadmap activo. Datum te creará uno pronto."
        )
    return profile


# ──────────────────────────────────────────────
# GENERAR — Crear roadmap personalizado
# ──────────────────────────────────────────────

@router.post(
    "",
    response_model=RoadmapResponse,
    status_code=201,
    summary="Generar roadmap personalizado",
)
def create_roadmap(body: RoadmapGenerateRequest, current_user: User = Depends(get_current_user)):
    """
    Orquesta la pipeline completa para generar un roadmap personalizado:
      1. Profiling Agent → obtiene el competency_profile del usuario
      2. RAG (ChromaDB) → busca cursos relevantes del catálogo
      3. Planning Agent → estructura las fases y bloques del roadmap
      4. ML Predict → clasifica la trayectoria (generalista/especialista)
      5. Explanatory Agent → genera explicación personalizada

    Respuestas:
      - 201: Roadmap generado → RoadmapResponse
      - 400: Datos de entrada inválidos
    """
    roadmap = roadmap_service.generate_roadmap(
        user_id=current_user.id,
        approach=body.approach,
    )
    return roadmap


# ──────────────────────────────────────────────
# ALTERNATIVAS — Trayectorias A y B
# ──────────────────────────────────────────────

@router.get(
    "/{roadmap_id}/alternatives",
    response_model=AlternativesResponse,
    summary="Obtener trayectorias A y B",
)
def get_alternatives(roadmap_id: str):
    """
    Devuelve ambas trayectorias (generalista y especialista) para
    un roadmap existente. Permite al usuario comparar y elegir.

    Respuestas:
      - 200: Ambas trayectorias → AlternativesResponse
      - 404: Roadmap no encontrado
    """
    alternatives = roadmap_service.get_alternatives(roadmap_id)
    if not alternatives:
        raise HTTPException(
            status_code=404,
            detail=f"Roadmap '{roadmap_id}' no encontrado",
        )
    return alternatives


# ──────────────────────────────────────────────
# PROGRESO — Marcar bloque completado
# ──────────────────────────────────────────────

@router.patch(
    "/{roadmap_id}/block/{block_id}",
    response_model=MessageResponse,
    summary="Marcar bloque completado",
)
def update_block_progress(roadmap_id: str, block_id: str, body: BlockProgressUpdate):
    """
    Marca un bloque del roadmap como completado o pendiente.

    Respuestas:
      - 200: Progreso actualizado → MessageResponse
      - 404: Roadmap o bloque no encontrado
    """
    updated = roadmap_service.update_block_progress(
        roadmap_id=roadmap_id,
        block_id=block_id,
        completed=body.completed,
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Roadmap '{roadmap_id}' o bloque '{block_id}' no encontrado",
        )

    estado = "completado" if body.completed else "pendiente"
    return MessageResponse(
        message=f"Bloque '{block_id}' marcado como {estado}",
    )

"""
Internal API Routes — Endpoints internos para IA/ML
=====================================================
Endpoints que NO se exponen al frontend, solo los usan
otros servicios del backend (orquestador, admin).

Incluye:
  - POST /predict-path → clasificación de trayectoria con el modelo ML
  - POST /reindex-course/{course_id} → re-indexar embedding en ChromaDB

Para uso del compañero de backend:
  - Importar este router en main.py:
    from app.api.routes.internal import router as internal_router
    app.include_router(internal_router, prefix="/api/internal")
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Asegurar que el directorio raíz esté en el path para importar ml/
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent  # GemeloDigital/
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

router = APIRouter(tags=["Internal — ML/IA"])


# ──────────────────────────────────────────────
# Schemas específicos de este endpoint
# ──────────────────────────────────────────────

class PredictPathRequest(BaseModel):
    """Datos del perfil cognitivo para predecir trayectoria."""
    experience_years: float = Field(..., ge=0, description="Años de experiencia profesional")
    avg_current_level: float = Field(..., ge=0, le=5, description="Nivel medio actual (0-5)")
    avg_gap: float = Field(..., ge=0, description="Gap medio respecto al nivel objetivo")
    n_competencies: int = Field(..., ge=1, description="Número de competencias evaluadas")
    dominant_domain: str = Field(
        ...,
        description=(
            "Dominio principal: 'Datos e IA', 'Programación y Desarrollo', "
            "'Cloud e Infraestructura', 'Gestión y Producto', 'Habilidades Transversales'"
        ),
    )
    objetivo_profesional: str = Field(..., description="Objetivo profesional declarado por el usuario")


class PredictPathResponse(BaseModel):
    """Resultado de la predicción de trayectoria."""
    trajectory: str = Field(..., description="GENERALIST o SPECIALIST")
    confidence: float = Field(..., ge=0, le=1, description="Confianza de la predicción (0-1)")
    raw_label: str = Field(..., description="Etiqueta ML cruda: A o B")


class ReindexResponse(BaseModel):
    """Resultado de la operación de re-indexación."""
    status: str = Field(..., description="'ok' o 'error'")
    course_id: Optional[str] = None
    detail: Optional[str] = None


# ──────────────────────────────────────────────
# PREDICT PATH — Clasificación de trayectoria ML
# ──────────────────────────────────────────────

@router.post(
    "/predict-path",
    response_model=PredictPathResponse,
    summary="Predecir trayectoria formativa (ML)",
)
def predict_path(body: PredictPathRequest):
    """
    Carga el modelo entrenado (path_predictor.pkl) y predice
    la trayectoria recomendada: GENERALIST o SPECIALIST.

    Este endpoint es llamado internamente por el orquestador
    durante la generación del roadmap (paso 4 del pipeline).

    Responses:
      - 200: Predicción exitosa → PredictPathResponse
      - 503: Modelo no entrenado (ejecutar python ml/train.py)
      - 500: Error interno de predicción
    """
    try:
        from ml.predict import predict_trajectory

        result = predict_trajectory(
            experience_years=body.experience_years,
            avg_current_level=body.avg_current_level,
            avg_gap=body.avg_gap,
            n_competencies=body.n_competencies,
            dominant_domain=body.dominant_domain,
            objetivo_profesional=body.objetivo_profesional,
        )
        return result

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Modelo ML no disponible: {e}. "
                "Ejecuta 'python ml/train.py' para entrenarlo."
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en la predicción: {e}",
        )


# ──────────────────────────────────────────────
# REINDEX COURSE — Re-indexar embedding individual
# ──────────────────────────────────────────────

@router.post(
    "/reindex-course/{course_id}",
    response_model=ReindexResponse,
    summary="Re-indexar embedding de un curso en ChromaDB",
)
def reindex_course(course_id: str):
    """
    Busca el curso por ID en courses.json, recalcula su embedding
    y lo actualiza en ChromaDB.

    Este endpoint es llamado por el panel de admin cuando se edita
    un curso (subtarea 2 — re-embedding automático).

    Responses:
      - 200: Re-indexación exitosa → ReindexResponse
      - 404: Curso no encontrado en el catálogo
      - 500: Error al re-indexar
    """
    try:
        from backend.app.services.admin_service import get_course
        from ml.reindex_service import reindex_single_course

        # Buscar el curso en el catálogo
        course = get_course(course_id)
        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Curso '{course_id}' no encontrado en el catálogo",
            )

        # Re-indexar
        result = reindex_single_course(course)

        if result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("detail", "Error desconocido al re-indexar"),
            )

        return result

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al re-indexar curso: {e}",
        )

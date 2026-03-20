"""
Courses API Routes — Catálogo público
=====================================

Endpoints de solo lectura para que el frontend pueda listar
los cursos disponibles en la plataforma, agrupándolos por temática
si lo desea.
"""

from typing import Optional

from fastapi import APIRouter, Query

from ..schemas import CourseResponse
from ...services import courses_service

router = APIRouter(tags=["Cursos"])


@router.get(
    "",
    summary="Listar cursos públicos del catálogo",
)
def list_public_courses(
    category: Optional[str] = Query(
        None,
        description="Categoría temática (programming/data/soft-skills/devops/product)",
    ),
    level: Optional[str] = Query(
        None,
        description="Filtrar por nivel: beginner/intermediate/advanced",
    ),
    affinity: Optional[str] = Query(
        None,
        description="Filtrar por afinidad: generalist/specialist/both",
    ),
):
    """
    Lista cursos del catálogo usados por el RAG.

    Respuesta:
      {
        "items": [CourseResponse, ...],
        "total":  N
      }
    """
    courses = courses_service.list_courses(
        category=category,
        level=level,
        affinity=affinity,
    )
    # Hacemos cast lógico a CourseResponse para documentar correctamente el esquema.
    typed_items = [CourseResponse(**c) for c in courses]
    return {"items": typed_items, "total": len(typed_items)}


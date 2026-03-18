"""
Course Generator API — Generar curso desde fuente (link o PDF)
==============================================================
Fase 1: contrato del endpoint. Acepta prompt + url (o en el futuro PDF).
Solo admin. Por ahora devuelve "no implementado".
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["Generador de cursos"])


class GenerateCourseFromSourceRequest(BaseModel):
    """Entrada para generar un curso desde una fuente (link o, en el futuro, PDF)."""
    prompt: Optional[str] = Field(None, description="Instrucciones o tema del curso (ej: 'Introducción a Python para no técnicos')")
    url: Optional[str] = Field(None, description="Enlace a un artículo o recurso para usar como base del contenido")


@router.post(
    "/from-source",
    summary="Generar curso desde URL o PDF (stub)",
)
def generate_course_from_source(body: GenerateCourseFromSourceRequest):
    """
    Fase 1: solo valida que venga al menos una fuente (url por ahora; PDF después).
    Devuelve 501 hasta implementar la generación real.
    """
    if not body.url:
        raise HTTPException(
            status_code=400,
            detail="Indica al menos una fuente: 'url' (por ahora). Subida de PDF en un siguiente paso.",
        )
    # Stub: aún no extraemos contenido ni generamos slides
    raise HTTPException(
        status_code=501,
        detail="Generación de curso desde fuente no implementada aún. Próximo paso: extraer contenido de la URL.",
    )

"""
Course Generator API — Generar curso desde fuente (link o PDF)
==============================================================
Fase 1: extracción de contenido desde URL. Próximamente PDF y generación de slides.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services import course_generator_service

router = APIRouter(tags=["Generador de cursos"])

PREVIEW_CHARS = 500


class GenerateCourseFromSourceRequest(BaseModel):
    """Entrada para generar un curso desde una fuente (link o, en el futuro, PDF)."""
    prompt: Optional[str] = Field(None, description="Instrucciones o tema del curso (ej: 'Introducción a Python para no técnicos')")
    url: Optional[str] = Field(None, description="Enlace a un artículo o recurso para usar como base del contenido")


@router.post(
    "/from-source",
    summary="Generar curso desde URL (extrae contenido y genera slides)",
)
def generate_course_from_source(body: GenerateCourseFromSourceRequest):
    """
    Extrae el texto de la URL, genera diapositivas + guion con un LLM y devuelve el curso.
    """
    if not body.url:
        raise HTTPException(
            status_code=400,
            detail="Indica al menos una fuente: 'url' (por ahora). Subida de PDF en un siguiente paso.",
        )
    text, err = course_generator_service.extract_text_from_url(body.url)
    if err:
        raise HTTPException(status_code=422, detail=err)
    preview = text[:PREVIEW_CHARS] + ("..." if len(text) > PREVIEW_CHARS else "")

    # Fase 2-1: generación de slides + guion usando el texto extraído.
    course_dict, course_err = course_generator_service.generate_course_slides_and_script(
        text,
        body.prompt,
    )
    if course_err:
        raise HTTPException(status_code=502, detail=course_err)

    return {
        "status": "generated",
        "source": "url",
        "content_length": len(text),
        "content_preview": preview,
        "course": course_dict,
    }

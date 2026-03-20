"""
Course Generator API — Generar curso desde fuente (prompt y/o url)
==================================================================
Genera un curso completo (slides + guion + metadata) a partir de un prompt
del administrador, una URL fuente, o ambos.

Endpoints:
 - POST /from-source       → preview rápido (no guarda en BD)
 - POST /save-from-source  → genera, guarda en BD y devuelve curso completo
"""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...services import course_generator_service
from ...services import pptx_deck_service

from ...database import SessionLocal
from ...models import Course, CourseDeck

router = APIRouter(tags=["Generador de cursos"])

PREVIEW_CHARS = 500


class GenerateCourseFromSourceRequest(BaseModel):
    """Entrada para generar un curso desde `prompt`, `url` o ambos."""
    prompt: Optional[str] = Field(
        None,
        description="Instrucciones o tema del curso (ej: 'Introducción a Python para no técnicos'). Si no hay url, se usa como fuente base.",
    )
    url: Optional[str] = Field(
        None,
        description="Enlace a un artículo o recurso para usar como base del contenido.",
    )


def _resolve_source(body: GenerateCourseFromSourceRequest):
    """Extrae texto fuente y prompt de usuario a partir del body."""
    if not (body.url or body.prompt):
        raise HTTPException(
            status_code=400,
            detail="Indica al menos una fuente: 'url' o 'prompt'.",
        )

    if body.url:
        text, err = course_generator_service.extract_text_from_url(body.url)
        if err:
            raise HTTPException(status_code=422, detail=err)
        user_prompt = body.prompt
        source = "url"
    else:
        text = body.prompt or ""
        user_prompt = None
        source = "prompt"

    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="No hay texto para generar el curso")

    return text, user_prompt, source


@router.post(
    "/from-source",
    summary="Preview: generar curso desde prompt/url (no guarda en BD)",
)
def generate_course_from_source(body: GenerateCourseFromSourceRequest):
    """
    Genera un preview del curso (slides + guion) sin persistir en BD.
    Útil para que el admin vea cómo quedaría antes de guardar.
    """
    text, user_prompt, source = _resolve_source(body)
    preview = text[:PREVIEW_CHARS] + ("..." if len(text) > PREVIEW_CHARS else "")

    course_dict, course_err = course_generator_service.generate_course_slides_and_script(
        text,
        user_prompt,
    )
    if course_err:
        raise HTTPException(status_code=502, detail=course_err)

    return {
        "status": "generated",
        "source": source,
        "content_length": len(text),
        "content_preview": preview,
        "course": course_dict,
    }


@router.post(
    "/save-from-source",
    summary="Generar y guardar curso completo (admin)",
)
def save_generated_course_from_source(body: GenerateCourseFromSourceRequest, request: Request):
    """
    Pipeline completo:
      1) Extrae texto de URL (si existe) o usa el prompt como fuente
      2) LLM genera slides + guion + metadata de catálogo
      3) Construye un `.pptx` descargable
      4) Guarda `Course` + `CourseDeck` en BD
      5) Re-indexa para RAG
      6) Devuelve el curso completo en JSON para revisión del admin
    """
    text, user_prompt, source = _resolve_source(body)

    # 1) Slides + metadata via LLM
    course_dict, course_err = course_generator_service.generate_course_slides_and_script(
        text,
        user_prompt,
    )
    if course_err:
        raise HTTPException(status_code=502, detail=course_err)

    # 2) ID del curso
    generated_course_id = f"crs-gen-{uuid.uuid4().hex[:8]}"

    # 3) Construir PPTX descargable (sin imágenes por ahora)
    deck_url, pptx_err = pptx_deck_service.build_pptx_deck(
        course_id=generated_course_id,
        slides=course_dict.get("slides", []),
        images_by_slide_number=[],
        deck_title=course_dict.get("course_title"),
        course_description=course_dict.get("description"),
        learning_objectives=course_dict.get("learning_objectives", []),
    )
    deck_download_url = f"{str(request.base_url).rstrip('/')}{deck_url}" if deck_url else None
    if pptx_err:
        deck_download_url = None

    # 4) Persistir en BD
    db = SessionLocal()
    try:
        db_course = Course(
            id=generated_course_id,
            title=course_dict.get("course_title", ""),
            description=course_dict.get("description", ""),
            url=body.url,
            competencies=course_dict.get("competencies", []),
            level=course_dict.get("level", "beginner"),
            duration_hours=course_dict.get("duration_hours", 0) or 0,
            trajectory_affinity=course_dict.get("trajectory_affinity", "both"),
        )
        db.add(db_course)
        db.commit()
        db.refresh(db_course)

        db_deck = CourseDeck(
            course_id=generated_course_id,
            source_url=body.url,
            prompt=body.prompt,
            slides_json=course_dict.get("slides", []),
            image_urls=[],
            deck_format="pptx",
            deck_file_url=deck_download_url,
        )
        db.add(db_deck)
        db.commit()
        db.refresh(db_deck)

    except Exception as db_err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error: {str(db_err)}")
    finally:
        db.close()

    # 5) Re-index en ChromaDB para RAG
    try:
        from agents.rag.indexer import reindex_course

        course_dict_for_rag = {
            "id": db_course.id,
            "title": db_course.title,
            "description": db_course.description,
            "competencies": db_course.competencies,
            "level": db_course.level,
            "url": db_course.url,
        }
        _ = reindex_course(course_dict_for_rag)
    except Exception:
        pass

    # 6) Respuesta completa con todo el contenido del curso
    return {
        "status": "saved",
        "source": source,
        "course_id": generated_course_id,
        "course": {
            "title": course_dict.get("course_title", ""),
            "description": course_dict.get("description", ""),
            "level": course_dict.get("level", ""),
            "trajectory_affinity": course_dict.get("trajectory_affinity", ""),
            "target_audience": course_dict.get("target_audience", ""),
            "competencies": course_dict.get("competencies", []),
            "learning_objectives": course_dict.get("learning_objectives", []),
            "slides": course_dict.get("slides", []),
        },
        "deck_download_url": deck_download_url,
    }

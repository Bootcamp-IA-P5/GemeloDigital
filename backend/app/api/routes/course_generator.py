"""
Course Generator API — Generar curso desde fuente (link o PDF)
==============================================================
Fase 1: extracción de contenido desde URL. Próximamente PDF y generación de slides.

Incluye endpoints admin:
 - /from-source: devuelve preview + slides/imágenes (prompts) para debug
 - /save-from-source: genera imágenes reales, construye un deck PPTX, lo guarda y reindexa RAG
"""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...services import course_generator_service
from ...services import hf_image_service, pptx_deck_service

from ...database import SessionLocal
from ...models import Course, CourseDeck

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

    # Fase 2-2: generar prompts de imagen por slide
    image_dict, image_err = course_generator_service.generate_course_image_prompts(
        course_dict.get("slides", []),
        body.prompt,
    )
    if image_err:
        raise HTTPException(status_code=502, detail=image_err)

    # Normalizamos la estructura para el frontend
    course_dict["image_style"] = image_dict.get("image_style", "")
    course_dict["image_prompts"] = image_dict.get("slides_image_prompts", [])

    return {
        "status": "generated",
        "source": "url",
        "content_length": len(text),
        "content_preview": preview,
        "course": course_dict,
    }


@router.post(
    "/save-from-source",
    summary="Generar y guardar curso generado (PPTX + imágenes) (admin)",
)
def save_generated_course_from_source(body: GenerateCourseFromSourceRequest):
    """
    Genera un curso completo desde URL:
      1) Slides + guion + metadata de catálogo
      2) Image prompts -> imágenes reales (HF)
      3) Construye un `.pptx` con la imagen embebida por slide
      4) Guarda `Course` + `CourseDeck` en BD y devuelve URLs
      5) Re-indexa para RAG
    """
    if not body.url:
        raise HTTPException(
            status_code=400,
            detail="Indica al menos una fuente: 'url'. Subida de PDF en un siguiente paso.",
        )

    text, err = course_generator_service.extract_text_from_url(body.url)
    if err:
        raise HTTPException(status_code=422, detail=err)

    # 1) Slides + metadata
    course_dict, course_err = course_generator_service.generate_course_slides_and_script(
        text,
        body.prompt,
    )
    if course_err:
        raise HTTPException(status_code=502, detail=course_err)

    # 2) Prompts de imagen
    image_dict, image_err = course_generator_service.generate_course_image_prompts(
        course_dict.get("slides", []),
        body.prompt,
    )
    if image_err:
        raise HTTPException(status_code=502, detail=image_err)

    image_style = image_dict.get("image_style", "")
    slide_image_prompts = image_dict.get("slides_image_prompts", [])

    # ID del curso generado (catálogo)
    generated_course_id = f"crs-gen-{uuid.uuid4().hex[:8]}"

    # 3) Generar imágenes reales con HF (guardadas en disco)
    images, hf_err = hf_image_service.generate_images_from_prompts(
        slide_image_prompts,
        image_style,
        course_id=generated_course_id,
    )
    if hf_err:
        raise HTTPException(status_code=502, detail=hf_err)

    # 4) Construir PPTX
    deck_url, pptx_err = pptx_deck_service.build_pptx_deck(
        course_id=generated_course_id,
        slides=course_dict.get("slides", []),
        images_by_slide_number=images,
        deck_title=course_dict.get("course_title"),
    )
    if pptx_err:
        raise HTTPException(status_code=502, detail=pptx_err)

    # 5) Persistir en BD
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
            image_urls=[
                {"slide_number": i.get("slide_number"), "image_url": i.get("image_url")} for i in images
            ],
            deck_format="pptx",
            deck_file_url=deck_url,
        )
        db.add(db_deck)
        db.commit()
        db.refresh(db_deck)

    except Exception as db_err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB error: {str(db_err)}")
    finally:
        db.close()

    # 6) Re-index en ChromaDB para RAG (usar los metadatos del catálogo)
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
        # No bloqueamos el flujo si falla el reindex.
        pass

    return {
        "status": "saved",
        "course_id": generated_course_id,
        "deck_file_url": deck_url,
    }

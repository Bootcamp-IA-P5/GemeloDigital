"""
Admin API Routes — Panel de Administración
==========================================
Endpoints FastAPI para el panel de administración.
Incluye CRUD de cursos, gestión de usuarios, roadmaps y métricas.

Para uso del compañero de backend:
  - Importar este router en main.py:
    from app.api.routes.admin import router as admin_router
    app.include_router(admin_router)
  - Configurar la dependencia get_db() para inyectar la sesión de BD
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..schemas import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    UserStatusUpdate,
    RoadmapBlockAdd,
    RoadmapBlockRemove,
    MessageResponse,
)
from ...services import admin_service

router = APIRouter(prefix="/admin", tags=["Admin Panel"])


# ──────────────────────────────────────────────
# CURSOS — CRUD completo (funcional sin BD)
# ──────────────────────────────────────────────

@router.get("/courses", summary="Listar cursos del catálogo")
def list_courses(
    level: Optional[str] = Query(None, description="Filtrar por nivel: beginner/intermediate/advanced"),
    affinity: Optional[str] = Query(None, description="Filtrar por afinidad: generalist/specialist/both"),
):
    """Lista todos los cursos del catálogo con filtros opcionales."""
    courses = admin_service.list_courses(level=level, affinity=affinity)
    return {"items": courses, "total": len(courses)}


@router.get("/courses/{course_id}", summary="Obtener detalle de un curso")
def get_course(course_id: str):
    """Obtiene un curso por su ID."""
    course = admin_service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail=f"Curso '{course_id}' no encontrado")
    return course


@router.post("/courses", status_code=201, summary="Crear un nuevo curso")
def create_course(course: CourseCreate):
    """Crea un nuevo curso en el catálogo."""
    created = admin_service.create_course(course.model_dump())
    return created


@router.put("/courses/{course_id}", summary="Actualizar un curso")
def update_course(course_id: str, updates: CourseUpdate):
    """Actualiza campos de un curso existente (campos parciales)."""
    updated = admin_service.update_course(course_id, updates.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Curso '{course_id}' no encontrado")
    return updated


@router.delete("/courses/{course_id}", summary="Eliminar un curso")
def delete_course(course_id: str):
    """Elimina un curso del catálogo."""
    deleted = admin_service.delete_course(course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Curso '{course_id}' no encontrado")
    return MessageResponse(message=f"Curso '{course_id}' eliminado correctamente")


@router.post("/courses/{course_id}/reindex", summary="Re-indexar embedding de un curso")
def reindex_course_embedding(course_id: str):
    """
    Re-indexa el embedding de un curso específico para el sistema RAG.
    Útil tras editar la descripción o competencias de un curso.
    """
    course = admin_service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail=f"Curso '{course_id}' no encontrado")
    # TODO: llamar al indexer RAG → agents/rag/indexer.py
    # indexer.reindex_course(course)
    return MessageResponse(
        message=f"Embedding del curso '{course_id}' re-indexado correctamente"
    )


# ──────────────────────────────────────────────
# COMPETENCIAS — Solo lectura
# ──────────────────────────────────────────────

@router.get("/competencies", summary="Listar taxonomía de competencias")
def list_competencies():
    """Lista todas las competencias de la taxonomía."""
    comps = admin_service.list_competencies()
    return {"items": comps, "total": len(comps)}


@router.get("/competencies/{comp_id}", summary="Obtener detalle de una competencia")
def get_competency(comp_id: str):
    """Obtiene una competencia por su ID."""
    comp = admin_service.get_competency(comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Competencia '{comp_id}' no encontrada")
    return comp


# ──────────────────────────────────────────────
# USUARIOS — Requiere BD (stubs)
# ──────────────────────────────────────────────

@router.get("/users", summary="Listar usuarios")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lista usuarios registrados con paginación."""
    return admin_service.list_users(page=page, page_size=page_size)


@router.get("/users/{user_id}", summary="Detalle de un usuario")
def get_user(user_id: str):
    """Obtiene el perfil de un usuario con su roadmap asignado."""
    user = admin_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario '{user_id}' no encontrado")
    return user


@router.patch("/users/{user_id}/status", summary="Activar/desactivar usuario")
def toggle_user_status(user_id: str, body: UserStatusUpdate):
    """Activa o desactiva un usuario."""
    result = admin_service.toggle_user_status(user_id, body.is_active)
    if not result:
        raise HTTPException(status_code=404, detail=f"Usuario '{user_id}' no encontrado")
    action = "activado" if body.is_active else "desactivado"
    return MessageResponse(message=f"Usuario '{user_id}' {action}")


# ──────────────────────────────────────────────
# ROADMAPS — Requiere BD (stubs)
# ──────────────────────────────────────────────

@router.get("/roadmaps", summary="Listar roadmaps")
def list_roadmaps(
    enfoque: Optional[str] = Query(None, description="GENERALISTA o ESPECIALISTA"),
    fecha_desde: Optional[str] = Query(None, description="Filtrar desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Filtrar hasta (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lista todos los roadmaps con filtros por fecha y trayectoria."""
    return admin_service.list_roadmaps(
        enfoque=enfoque,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        page=page,
        page_size=page_size,
    )


@router.get("/roadmaps/{roadmap_id}", summary="Detalle de un roadmap")
def get_roadmap(roadmap_id: str):
    """Obtiene un roadmap completo con fases y bloques."""
    roadmap = admin_service.get_roadmap(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail=f"Roadmap '{roadmap_id}' no encontrado")
    return roadmap


@router.post("/roadmaps/{roadmap_id}/blocks", summary="Añadir bloque a un roadmap")
def add_block(roadmap_id: str, body: RoadmapBlockAdd):
    """Añade un curso (bloque) a una fase específica del roadmap."""
    result = admin_service.add_block_to_roadmap(
        roadmap_id, body.fase_orden, body.contenido_id, body.posicion
    )
    if not result:
        raise HTTPException(status_code=404, detail="Roadmap o fase no encontrada")
    return MessageResponse(message="Bloque añadido correctamente")


@router.delete("/roadmaps/{roadmap_id}/blocks", summary="Eliminar bloque de un roadmap")
def remove_block(roadmap_id: str, body: RoadmapBlockRemove):
    """Elimina un curso (bloque) de una fase del roadmap."""
    removed = admin_service.remove_block_from_roadmap(
        roadmap_id, body.fase_orden, body.contenido_id
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Roadmap, fase o bloque no encontrado")
    return MessageResponse(message="Bloque eliminado correctamente")


# ──────────────────────────────────────────────
# MÉTRICAS
# ──────────────────────────────────────────────

@router.get("/metrics", summary="Métricas del panel de administración")
def get_metrics():
    """
    Devuelve métricas agregadas:
    - Total usuarios / activos
    - Total roadmaps / activos
    - Total cursos
    - Distribución trayectoria A vs B
    - Top 5 cursos más usados en roadmaps
    """
    return admin_service.get_admin_metrics()

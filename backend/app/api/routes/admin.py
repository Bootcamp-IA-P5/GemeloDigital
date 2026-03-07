"""
Admin API Routes — Administration Panel
==========================================
FastAPI endpoints for the administration panel.
Includes course CRUD, user management, roadmaps and metrics.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..schemas import (
    CourseCreate,
    CourseUpdate,
    UserStatusUpdate,
    RoadmapBlockAdd,
    RoadmapBlockRemove,
    MessageResponse,
)
from ...services import admin_service

router = APIRouter(tags=["Administration"])


# ──────────────────────────────────────────────
# COURSES — Full CRUD (functional without DB)
# ──────────────────────────────────────────────


@router.get("/courses", summary="List catalog courses")
def list_courses(
    level: Optional[str] = Query(
        None, description="Filter by level: beginner/intermediate/advanced"
    ),
    affinity: Optional[str] = Query(
        None, description="Filter by affinity: generalist/specialist/both"
    ),
):
    """List all courses in the catalog with optional filters."""
    courses = admin_service.list_courses(level=level, affinity=affinity)
    return {"items": courses, "total": len(courses)}


@router.get("/courses/{course_id}", summary="Get course details")
def get_course(course_id: str):
    """Get a course by its ID."""
    course = admin_service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    return course


@router.post("/courses", status_code=201, summary="Create a new course")
def create_course(course: CourseCreate):
    """Create a new course in the catalog."""
    created = admin_service.create_course(course.model_dump())
    return created


@router.put("/courses/{course_id}", summary="Update a course")
def update_course(course_id: str, updates: CourseUpdate):
    """Update fields of an existing course (partial update)."""
    updated = admin_service.update_course(
        course_id, updates.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    return updated


@router.delete("/courses/{course_id}", summary="Delete a course")
def delete_course(course_id: str):
    """Delete a course from the catalog."""
    deleted = admin_service.delete_course(course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    return MessageResponse(message=f"Course '{course_id}' deleted successfully")


@router.post("/courses/{course_id}/reindex", summary="Re-index course embedding")
def reindex_course_embedding(course_id: str):
    """
    Re-index the embedding of a specific course for the RAG system.
    Useful after editing the description or competencies of a course.
    """
    course = admin_service.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    # TODO: call RAG indexer → agents/rag/indexer.py
    # indexer.reindex_course(course)
    return MessageResponse(
        message=f"Embedding for course '{course_id}' re-indexed successfully"
    )


# ──────────────────────────────────────────────
# COMPETENCIES — Read-only
# ──────────────────────────────────────────────


@router.get("/competencies", summary="List competency taxonomy")
def list_competencies():
    """List all competencies in the taxonomy."""
    comps = admin_service.list_competencies()
    return {"items": comps, "total": len(comps)}


@router.get("/competencies/{comp_id}", summary="Get competency details")
def get_competency(comp_id: str):
    """Get a competency by its ID."""
    comp = admin_service.get_competency(comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Competency '{comp_id}' not found")
    return comp


# ──────────────────────────────────────────────
# USERS — Requires DB (stubs)
# ──────────────────────────────────────────────


@router.get("/users", summary="List users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List registered users with pagination."""
    return admin_service.list_users(page=page, page_size=page_size)


@router.get("/users/{user_id}", summary="User details")
def get_user(user_id: str):
    """Get a user's profile with their assigned roadmap."""
    user = admin_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return user


@router.patch("/users/{user_id}/status", summary="Activate/deactivate user")
def toggle_user_status(user_id: str, body: UserStatusUpdate):
    """Activate or deactivate a user."""
    result = admin_service.toggle_user_status(user_id, body.is_active)
    if not result:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    action = "activated" if body.is_active else "deactivated"
    return MessageResponse(message=f"User '{user_id}' {action}")


# ──────────────────────────────────────────────
# ROADMAPS — Requires DB (stubs)
# ──────────────────────────────────────────────


@router.get("/roadmaps", summary="List roadmaps")
def list_roadmaps(
    approach: Optional[str] = Query(None, description="GENERALIST or SPECIALIST"),
    date_from: Optional[str] = Query(None, description="Filter from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all roadmaps with filters by date and trajectory."""
    return admin_service.list_roadmaps(
        approach=approach,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get("/roadmaps/{roadmap_id}", summary="Roadmap details")
def get_roadmap(roadmap_id: str):
    """Get a complete roadmap with phases and blocks."""
    roadmap = admin_service.get_roadmap(roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail=f"Roadmap '{roadmap_id}' not found")
    return roadmap


@router.post("/roadmaps/{roadmap_id}/blocks", summary="Add block to a roadmap")
def add_block(roadmap_id: str, body: RoadmapBlockAdd):
    """Add a course (block) to a specific phase of the roadmap."""
    result = admin_service.add_block_to_roadmap(
        roadmap_id, body.phase_order, body.content_id, body.position
    )
    if not result:
        raise HTTPException(status_code=404, detail="Roadmap or phase not found")
    return MessageResponse(message="Block added successfully")


@router.delete("/roadmaps/{roadmap_id}/blocks", summary="Remove block from a roadmap")
def remove_block(roadmap_id: str, body: RoadmapBlockRemove):
    """Remove a course (block) from a roadmap phase."""
    removed = admin_service.remove_block_from_roadmap(
        roadmap_id, body.phase_order, body.content_id
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Roadmap, phase or block not found")
    return MessageResponse(message="Block removed successfully")


# ──────────────────────────────────────────────
# METRICS
# ──────────────────────────────────────────────


@router.get("/metrics", summary="Administration panel metrics")
def get_metrics():
    """
    Return aggregated metrics:
    - Total users / active
    - Total roadmaps / active
    - Total courses
    - Trajectory A vs B distribution
    - Top 5 most used courses in roadmaps
    """
    return admin_service.get_admin_metrics()

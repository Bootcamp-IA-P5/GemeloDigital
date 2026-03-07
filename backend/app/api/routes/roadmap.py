"""
Roadmap API Routes — Personalized Roadmap
============================================
FastAPI endpoints for generating and managing personalized
learning roadmaps.

Orchestrates the full pipeline:
  Profiling Agent → RAG (ChromaDB) → Planning Agent → ML Predict → Explanatory Agent

For backend companion usage:
  - Import this router in main.py:
    from app.api.routes.roadmap import router as roadmap_router
    app.include_router(roadmap_router, prefix="/api/roadmap")
  - Configure the dependency get_db() to inject the DB session
  - Connect with the orchestrator for the full pipeline
"""

from fastapi import APIRouter, HTTPException

from ..schemas import (
    RoadmapGenerateRequest,
    RoadmapResponse,
    AlternativesResponse,
    BlockProgressUpdate,
    MessageResponse,
)
from ...services import roadmap_service

router = APIRouter(tags=["Roadmap"])


# ──────────────────────────────────────────────
# GENERATE — Create personalized roadmap
# ──────────────────────────────────────────────


@router.post(
    "/",
    response_model=RoadmapResponse,
    status_code=201,
    summary="Generate personalized roadmap",
)
def create_roadmap(body: RoadmapGenerateRequest):
    """
    Orchestrate the full pipeline to generate a personalized roadmap:
      1. Profiling Agent → get the user's competency_profile
      2. RAG (ChromaDB) → search relevant courses from the catalog
      3. Planning Agent → structure phases and blocks
      4. ML Predict → classify trajectory (generalist/specialist)
      5. Explanatory Agent → generate personalized explanation

    Responses:
      - 201: Roadmap generated → RoadmapResponse
      - 400: Invalid input data
    """
    roadmap = roadmap_service.generate_roadmap(
        user_id=body.user_id,
        approach=body.approach,
    )
    return roadmap


# ──────────────────────────────────────────────
# ALTERNATIVES — Trajectories A and B
# ──────────────────────────────────────────────


@router.get(
    "/{roadmap_id}/alternatives",
    response_model=AlternativesResponse,
    summary="Get trajectories A and B",
)
def get_alternatives(roadmap_id: str):
    """
    Return both trajectories (generalist and specialist) for
    an existing roadmap. Allows the user to compare and choose.

    Responses:
      - 200: Both trajectories → AlternativesResponse
      - 404: Roadmap not found
    """
    alternatives = roadmap_service.get_alternatives(roadmap_id)
    if not alternatives:
        raise HTTPException(
            status_code=404,
            detail=f"Roadmap '{roadmap_id}' not found",
        )
    return alternatives


# ──────────────────────────────────────────────
# PROGRESS — Mark block as completed
# ──────────────────────────────────────────────


@router.patch(
    "/{roadmap_id}/block/{block_id}",
    response_model=MessageResponse,
    summary="Mark block as completed",
)
def update_block_progress(roadmap_id: str, block_id: str, body: BlockProgressUpdate):
    """
    Mark a roadmap block as completed or pending.

    Responses:
      - 200: Progress updated → MessageResponse
      - 404: Roadmap or block not found
    """
    updated = roadmap_service.update_block_progress(
        roadmap_id=roadmap_id,
        block_id=block_id,
        completed=body.completed,
    )
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Roadmap '{roadmap_id}' or block '{block_id}' not found",
        )

    status = "completed" if body.completed else "pending"
    return MessageResponse(
        message=f"Block '{block_id}' marked as {status}",
    )

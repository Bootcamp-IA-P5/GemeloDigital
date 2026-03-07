"""
Profile API Routes — Cognitive Profile
========================================
FastAPI endpoints for managing user cognitive profiles.
Orchestrates the Profiling Agent to analyze questionnaire answers
and generate a personalized competency_profile.
"""

from fastapi import APIRouter, HTTPException

from ..schemas import (
    QuestionnaireAnswers,
    CompetencyProfile,
)
from ...services import profile_service

router = APIRouter(tags=["Profile"])


# ──────────────────────────────────────────────
# CREATE — Generate cognitive profile
# ──────────────────────────────────────────────


@router.post(
    "/",
    response_model=CompetencyProfile,
    status_code=201,
    summary="Create cognitive profile",
)
def create_profile(body: QuestionnaireAnswers):
    """
    Receive questionnaire answers from the frontend and generate
    the user's cognitive profile.

    Pipeline:
      1. Receive raw_answers from questionnaire
      2. Send to Profiling Agent (LLM) via orchestrator
      3. Agent analyzes competencies and generates scores
      4. Return competency_profile with recommended approach

    Responses:
      - 201: Profile created → CompetencyProfile
      - 400: Invalid questionnaire data
    """
    profile = profile_service.create_profile(
        user_id=body.user_id,
        answers=body.answers,
    )
    return profile


# ──────────────────────────────────────────────
# READ — Get user profile
# ──────────────────────────────────────────────


@router.get(
    "/{user_id}",
    response_model=CompetencyProfile,
    summary="Get user cognitive profile",
)
def get_profile(user_id: str):
    """
    Get the stored cognitive profile for a user.

    Responses:
      - 200: Profile found → CompetencyProfile
      - 404: User has no cognitive profile
    """
    profile = profile_service.get_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No cognitive profile found for user '{user_id}'",
        )
    return profile

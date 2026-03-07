"""
Profile Service — Cognitive Profile Business Logic
====================================================
Functions to create and query cognitive profiles.
Currently uses stub data in memory; will delegate to the
Profiling Agent via the orchestrator in production.

TODO:
  - Replace PROFILES_DB with queries to the `profiles` table
  - Integrate the Profiling Agent call (agents/profiling_agent.py)
  - Connect with the orchestrator for the full pipeline
"""

import uuid

# ──────────────────────────────────────────────
# STUB DATABASE (in-memory)
# ──────────────────────────────────────────────
PROFILES_DB: dict[str, dict] = {}


# ──────────────────────────────────────────────
# CREATE COGNITIVE PROFILE
# ──────────────────────────────────────────────


def create_profile(user_id: str, answers: dict) -> dict:
    """
    Create a cognitive profile from questionnaire answers.

    In production:
      1. Send raw_answers to the Profiling Agent (LLM)
      2. Agent analyzes and generates a competency_profile
      3. Persist in the `profiles` table

    Currently returns a stub profile with example competencies.
    """
    profile_id = str(uuid.uuid4())

    # Stub profile — simulates Profiling Agent output
    profile = {
        "user_id": user_id,
        "profile_id": profile_id,
        "competencies": [
            {
                "competency_id": "comp-python",
                "name": "Python Programming",
                "level": "medium",
                "score": 0.65,
            },
            {
                "competency_id": "comp-ml",
                "name": "Machine Learning",
                "level": "low",
                "score": 0.30,
            },
            {
                "competency_id": "comp-data",
                "name": "Data Analysis",
                "level": "high",
                "score": 0.85,
            },
        ],
        "recommended_approach": "GENERALIST",
        "summary": (
            "The user shows strengths in data analysis and an intermediate "
            "level in Python. A generalist trajectory is recommended to "
            "strengthen ML competencies before specializing."
        ),
    }

    PROFILES_DB[user_id] = profile
    return profile


# ──────────────────────────────────────────────
# GET PROFILE
# ──────────────────────────────────────────────


def get_profile(user_id: str) -> dict | None:
    """
    Get the cognitive profile for a user.
    Returns None if not found.

    TODO: Query `profiles` table in PostgreSQL.
    """
    return PROFILES_DB.get(user_id)

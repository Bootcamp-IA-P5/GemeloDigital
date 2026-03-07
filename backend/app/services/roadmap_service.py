"""
Roadmap Service — Roadmap Business Logic
==========================================
Functions to generate, query and update roadmaps.
Currently uses stub data in memory; will orchestrate the full
pipeline in production: Profiling → RAG → Planning → ML → Explanatory.

TODO:
  - Replace ROADMAPS_DB with queries to `roadmaps` and `progress` tables
  - Integrate the orchestrator call for the full pipeline
  - Connect with the ML model for trajectory classification
"""

import uuid

# ──────────────────────────────────────────────
# STUB DATABASE (in-memory)
# ──────────────────────────────────────────────
ROADMAPS_DB: dict[str, dict] = {}


# ──────────────────────────────────────────────
# GENERATE ROADMAP
# ──────────────────────────────────────────────


def generate_roadmap(user_id: str, approach: str) -> dict:
    """
    Generate a personalized roadmap for the user.

    Production pipeline:
      1. Profiling Agent → get competency_profile
      2. RAG (ChromaDB) → search relevant courses
      3. Planning Agent → structure phases and blocks
      4. ML Predict → classify trajectory A/B
      5. Explanatory Agent → generate explanation

    Currently returns a stub roadmap with example phases.
    """
    roadmap_id = str(uuid.uuid4())

    roadmap = {
        "roadmap_id": roadmap_id,
        "user_id": user_id,
        "approach": approach,
        "phases": [
            {
                "phase_order": 1,
                "name": "Fundamentals",
                "blocks": [
                    {
                        "block_id": f"blk-{uuid.uuid4().hex[:8]}",
                        "content_id": "course-python-101",
                        "title": "Python for Beginners",
                        "order": 1,
                        "completed": False,
                    },
                    {
                        "block_id": f"blk-{uuid.uuid4().hex[:8]}",
                        "content_id": "course-stats-101",
                        "title": "Basic Statistics",
                        "order": 2,
                        "completed": False,
                    },
                ],
            },
            {
                "phase_order": 2,
                "name": "Intermediate",
                "blocks": [
                    {
                        "block_id": f"blk-{uuid.uuid4().hex[:8]}",
                        "content_id": "course-ml-201",
                        "title": "Introduction to Machine Learning",
                        "order": 1,
                        "completed": False,
                    },
                ],
            },
            {
                "phase_order": 3,
                "name": "Advanced",
                "blocks": [
                    {
                        "block_id": f"blk-{uuid.uuid4().hex[:8]}",
                        "content_id": "course-dl-301",
                        "title": "Applied Deep Learning",
                        "order": 1,
                        "completed": False,
                    },
                ],
            },
        ],
        "explanation": (
            f"A {approach} roadmap has been generated based on your cognitive "
            "profile. Phases progress from fundamentals to advanced topics, "
            "adapted to your strengths and areas for improvement."
        ),
    }

    ROADMAPS_DB[roadmap_id] = roadmap
    return roadmap


# ──────────────────────────────────────────────
# GET ALTERNATIVES (Trajectory A and B)
# ──────────────────────────────────────────────


def get_alternatives(roadmap_id: str) -> dict | None:
    """
    Return both trajectories (generalist and specialist) for a roadmap.

    TODO:
      - Query DB to get both versions of the roadmap
      - If only one exists, generate the alternative with the Planning Agent
    """
    roadmap = ROADMAPS_DB.get(roadmap_id)
    if not roadmap:
        return None

    # Stub: build inverted alternative
    return {
        "roadmap_id": roadmap_id,
        "generalist": (
            roadmap
            if roadmap["approach"] == "GENERALIST"
            else {
                **roadmap,
                "approach": "GENERALIST",
                "explanation": "Alternative generalist trajectory (stub).",
            }
        ),
        "specialist": (
            roadmap
            if roadmap["approach"] == "SPECIALIST"
            else {
                **roadmap,
                "approach": "SPECIALIST",
                "explanation": "Alternative specialist trajectory (stub).",
            }
        ),
    }


# ──────────────────────────────────────────────
# UPDATE BLOCK PROGRESS
# ──────────────────────────────────────────────


def update_block_progress(roadmap_id: str, block_id: str, completed: bool) -> bool:
    """
    Mark a block as completed or pending.
    Returns True if found and updated, False otherwise.

    TODO: Update `progress` table in PostgreSQL.
    """
    roadmap = ROADMAPS_DB.get(roadmap_id)
    if not roadmap:
        return False

    for phase in roadmap.get("phases", []):
        for block in phase.get("blocks", []):
            if block["block_id"] == block_id:
                block["completed"] = completed
                return True
    return False

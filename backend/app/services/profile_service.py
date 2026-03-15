"""
Profile Service — Lógica de negocio del perfil cognitivo
========================================================
Funciones para crear y consultar perfiles cognitivos.
Actualmente usa datos stub en memoria; en producción delegará
al Profiling Agent via el orchestrator.

Para uso del compañero de backend:
  - Reemplazar PROFILES_DB por queries a la tabla `profiles`
  - Integrar la llamada al Profiling Agent (agents/profiling_agent.py)
  - Conectar con el orchestrator para la pipeline completa
"""

import uuid

from agents.nodes.profiling_node import generate_cognitive_profile
from backend.app.api.schemas import QuestionnaireAnswers

# ──────────────────────────────────────────────
# CREAR PERFIL COGNITIVO
# ──────────────────────────────────────────────

def create_profile(user_id: str, answers: QuestionnaireAnswers) -> dict:
    """
    Creates a cognitive profile by invoking the Profiling Agent.
    """
    print(f"[Service] Requesting real profiling for user: {user_id}")
    
    # 1. Transform Pydantic model to JSON for the agent
    # The agent expects a JSON string of the answers
    answers_dict = answers.dict()
    import json
    answers_json = json.dumps(answers_dict)

    # 2. Invoke the actual Agent Node
    # This will return a dict with {competencies, recommended_approach, summary}
    # and it internally saves to the Database via our new tool.
    profile_dict = generate_cognitive_profile(
        user_answers_json=answers_json,
        original_user_id=user_id
    )

    return profile_dict


from backend.app.database import SessionLocal
from backend.app.models import Profile

# ──────────────────────────────────────────────
# OBTENER PERFIL
# ──────────────────────────────────────────────

def get_profile(user_id: str) -> dict | None:
    """
    Retrieves the cognitive profile of a user from PostgreSQL.
    Returns None if it doesn't exist.
    """
    print(f"[Service] Searching for profile in DB for user: {user_id}")
    
    db = SessionLocal()
    try:
        db_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not db_profile:
            return None
            
        # Map the DB model (JSON column) to the dictionary format expected by schemas
        # The tool saves it as {'competencies': [...], 'recommended_approach': "...", 'summary': "..."}
        profile_data = db_profile.competency_profile
        
        # Add basic IDs needed for the CompetencyProfile schema
        competencies = []
        for c in profile_data.get("competencies", []):
            # Map score logic (normalized to 1-4 for frontend)
            score_val = c.get("score", 0.5)
            curr_level = int(score_val * 3) + 1 # 0.0->1, 1.0->4
            
            competencies.append({
                "competency_id": c.get("competency_id"),
                "name": c.get("name"),
                "domain": "Default", # We could infer this later
                "current_level": curr_level,
                "target_level": 4, # Hardcoded target for now
                "gap": max(0, 4 - curr_level),
                "score": score_val
            })

        return {
            "user_id": str(db_profile.user_id),
            "profile_id": str(db_profile.id),
            "competencies": competencies,
            "recommended_approach": profile_data.get("recommended_approach", "GENERALISTA"),
            "summary": profile_data.get("summary", "")
        }
    finally:
        db.close()

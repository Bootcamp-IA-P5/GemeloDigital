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
import json as _json
import os
import time as _time

from agents.nodes.profiling_node import generate_cognitive_profile
from app.api.schemas import QuestionnaireAnswers
from app.database import SessionLocal
from app.models import Profile, User, Roadmap

def _load_domain_map() -> dict:
    """Build competency_id → domain from competencies.json + fallback heuristics."""
    mapping = {}
    comp_file = os.path.join(os.path.dirname(__file__), "..", "..", "agents", "data", "competencies.json")
    try:
        with open(comp_file) as f:
            for c in _json.load(f):
                mapping[c["id"]] = c.get("domain", "general")
    except Exception:
        pass
    extras = {
        "ml-fundamentals": "data", "deep-learning": "data", "statistics": "data",
        "data-viz": "data", "html-css": "programming", "react": "programming",
        "ux-design": "product", "responsive": "programming", "testing-fe": "programming",
        "rest-api": "programming", "docker": "devops", "databases": "data",
        "ci-cd": "devops", "security": "devops", "digital-literacy": "soft-skills",
        "teamwork": "soft-skills", "self-learning": "soft-skills",
        "project-mgmt": "product",
    }
    for k, v in extras.items():
        mapping.setdefault(k, v)
    return mapping

_DOMAIN_MAP = _load_domain_map()

_DOMAIN_LABELS = {
    "programming": "Programación",
    "data": "Datos & ML",
    "devops": "DevOps & Cloud",
    "soft-skills": "Soft Skills",
    "product": "Producto & UX",
}

# #region agent log
_DBG_LOG = "/Users/barbara/Desktop/gemelo_digital/GemeloDigital/.cursor/debug-9b2746.log"
def _dbg(loc, msg, data=None):
    try:
        import json, time
        entry = {"sessionId":"9b2746","location":loc,"message":msg,"data":data or {},"timestamp":int(time.time()*1000),"hypothesisId":"H1H2"}
        with open(_DBG_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except: pass
# #endregion

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



# ──────────────────────────────────────────────
# OBTENER PERFIL UNIFICADO (Paso 2)
# ──────────────────────────────────────────────

def get_profile(user_id: str) -> dict | None:
    """
    Retrieves the full unified state (Profile + Roadmap + Avatar).
    """
    print(f"[Service] Searching for full state in DB for user: {user_id}")
    
    db = SessionLocal()
    try:
        # 1. Fetch User
        user = db.query(User).filter(User.id == user_id).first()
        
        # 2. Fetch Latest Profile
        db_profile = db.query(Profile).filter(Profile.user_id == user_id).order_by(Profile.created_at.desc()).first()
        if not db_profile:
            return None
            
        # 3. Fetch Latest Roadmap
        db_roadmap = db.query(Roadmap).filter(Roadmap.user_id == user_id).order_by(Roadmap.created_at.desc()).first()

        # Map competencies
        profile_data = db_profile.competency_profile or {}
        competencies = []
        for c in profile_data.get("competencies", []):
            score_val = c.get("score", 0.5)
            curr_level = int(score_val * 3) + 1
            cid = c.get("competency_id", "")
            raw_domain = _DOMAIN_MAP.get(cid, "general")
            domain_label = _DOMAIN_LABELS.get(raw_domain, raw_domain.replace("-", " ").title())
            competencies.append({
                "id": cid,
                "label": c.get("name"),
                "domain": domain_label,
                "current_level": curr_level,
                "target_level": 4,
                "gap": max(0, 4 - curr_level),
                "score": score_val
            })

        raw = db_profile.raw_answers or {}
        
        # Roadmap Formatting
        roadmap_data = None
        if db_roadmap:
            enriched_phases = []
            for phase in db_roadmap.phases:
                blocks = []
                for b in phase.get("blocks", []):
                    blocks.append({
                        "block_id": b.get("block_id"),
                        "course_id": b.get("content_id") or b.get("course_id", ""),
                        "content_id": b.get("content_id"),
                        "title": b.get("title"),
                        "order": b.get("order", 1),
                        "completed": b.get("completed", False),
                        "priority": b.get("priority", "required"),
                        "duration": b.get("duration", "10h"),
                        "level": b.get("level", "intermediate"),
                        "why": b.get("why", "Recommended based on your gaps."),
                        "competencies_addressed": b.get("competencies_addressed", [])
                    })
                enriched_phases.append({
                    "phase_order": phase.get("phase_order", 1),
                    "name": phase.get("name", "Fase"),
                    "blocks": blocks
                })
            
            trajectory_val = db_roadmap.trajectory or "GENERALISTA"
            if trajectory_val == "A":
                trajectory_val = "GENERALISTA"
            elif trajectory_val == "B":
                trajectory_val = "ESPECIALISTA"

            roadmap_data = {
                "roadmap_id": str(db_roadmap.id),
                "user_id": str(db_roadmap.user_id),
                "trajectory": trajectory_val,
                "phases": enriched_phases,
                "explanation": db_roadmap.ml_prediction.get("explanation", "") if db_roadmap.ml_prediction else ""
            }
            # #region agent log
            _dbg("profile_service.py:roadmap_data", "roadmap_data built", {"trajectory": trajectory_val, "num_phases": len(enriched_phases), "first_block_keys": list(enriched_phases[0]["blocks"][0].keys()) if enriched_phases and enriched_phases[0].get("blocks") else []})
            # #endregion

        return {
            "user_id": str(user_id),
            "full_name": user.name if user else "Usuario",
            "current_role": raw.get("currentRole", "Developer"),
            "target_role": raw.get("targetRole", "Senior"),
            "experience_years": raw.get("experience", 0),
            "avatar": {
                "url": db_profile.avatar_url,
                "personality": db_profile.avatar_personality,
                "color": db_profile.avatar_color
            },
            "competencies": competencies,
            "competency_profile": {
                "user_id": str(user_id),
                "profile_id": str(db_profile.id),
                "current_role": raw.get("currentRole", "Developer"),
                "target_role": raw.get("targetRole", "Senior"),
                "experience_years": raw.get("experience", 0),
                "competencies": competencies,
                "recommended_approach": profile_data.get("recommended_approach", "GENERALISTA"),
                "summary": profile_data.get("summary", "")
            },
            "roadmap": roadmap_data
        }
    finally:
        db.close()

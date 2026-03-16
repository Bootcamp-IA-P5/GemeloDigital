"""
Roadmap Service — Lógica de negocio del roadmap
================================================
Funciones para generar, consultar y actualizar roadmaps.
Orquesta la pipeline completa: Profiling → RAG → Planning → ML → Explanatory.
"""

import uuid
import json
from app.database import SessionLocal
from app.models import Profile, Roadmap, Progress
from agents.graph import app as agent_graph

def to_dict(rm: Roadmap) -> dict:
    """Helper to convert Roadmap ORM to dict matching RoadmapResponse schema."""
    enriched_phases = []
    for phase in rm.phases:
        blocks = []
        for b in phase.get("blocks", []):
            # Normalizamos el ID del curso para el frontend
            blocks.append({
                "course_id": b.get("content_id") or b.get("course_id") or b.get("id"),
                "title": b.get("title"),
                "priority": b.get("priority", "required"),
                "duration": b.get("duration", "10h"),
                "level": b.get("level", "intermediate"),
                "completed": b.get("completed", False),
                "why": b.get("why", "Recomendado basado en tu perfil."),
                "competencies_addressed": b.get("competencies_addressed", [])
            })
        enriched_phases.append({
            "phase_order": phase.get("phase_order", 1),
            "name": phase.get("name", "Fase"),
            "blocks": blocks
        })

    return {
        "roadmap_id": str(rm.id),
        "user_id": str(rm.user_id),
        "trajectory": "GENERALISTA" if rm.trajectory == "A" else "ESPECIALISTA",
        "phases": enriched_phases
    }

# ──────────────────────────────────────────────
# GENERAR ROADMAP
# ──────────────────────────────────────────────

def generate_roadmap(user_id: str, approach: str) -> dict:
    """
    Generates a personalized roadmap by orchestrating the agent pipeline.
    """
    print(f"[Service] Starting roadmap generation for user: {user_id} (approach: {approach})")
    
    db = SessionLocal()
    try:
        # 1. Fetch existing profile
        profile = db.query(Profile).filter(Profile.user_id == user_id).order_by(Profile.created_at.desc()).first()
        if not profile:
            raise ValueError(f"No cognitive profile found for user {user_id}. Please complete the questionnaire first.")

        # 2. Prepare initial state for LangGraph
        initial_input = {
            "user_id": str(user_id),
            "raw_answers": json.dumps(profile.raw_answers) if profile.raw_answers else "{}",
            "competency_profile": profile.competency_profile,
            "approach": approach 
        }

        # 3. Invoke the Full Pipeline (Graph)
        print("[Service] Invoking Agent Graph...")
        result = agent_graph.invoke(initial_input)

        if result.get("errors"):
            raise Exception(f"Agent Pipeline Error: {result['errors'][0]}")

        # 4. Extract generated data
        generated_roadmap = result.get("roadmap", {})
        ml_prediction_val = result.get("ml_prediction", "A")
        
        # 5. Persist the Roadmap in DB
        trajectory_code = "A" if approach.upper() == "GENERALISTA" else "B"
        
        db_roadmap = Roadmap(
            user_id=user_id,
            profile_id=profile.id,
            trajectory=trajectory_code,
            ml_prediction={
                "trajectory": ml_prediction_val,
                "approach": approach,
                "explanation": generated_roadmap.get("explanation", result.get("explanation", ""))
            },
            phases=generated_roadmap.get("phases", [])
        )
        db.add(db_roadmap)
        db.commit()
        db.refresh(db_roadmap)

        return to_dict(db_roadmap)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


# ──────────────────────────────────────────────
# OBTENER ROADMAP ACTUAL
# ──────────────────────────────────────────────

def get_current_roadmap(user_id: str) -> dict | None:
    """
    Obtiene el roadmap más reciente de un usuario.
    """
    db = SessionLocal()
    try:
        roadmap = db.query(Roadmap).filter(Roadmap.user_id == user_id).order_by(Roadmap.created_at.desc()).first()
        if not roadmap:
            return None
        return to_dict(roadmap)
    finally:
        db.close()


# ──────────────────────────────────────────────
# OBTENER ALTERNATIVAS (Trayectoria A y B)
# ──────────────────────────────────────────────

def get_alternatives(roadmap_id: str) -> dict | None:
    """
    Retrieves both trajectories for comparisons.
    """
    db = SessionLocal()
    try:
        current_roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
        if not current_roadmap:
            return None

        # Look for other roadmaps for the same profile
        others = db.query(Roadmap).filter(
            Roadmap.profile_id == current_roadmap.profile_id,
            Roadmap.id != current_roadmap.id
        ).all()

        res = {
            "roadmap_id": str(current_roadmap.id),
            "generalista": None,
            "especialista": None
        }

        if current_roadmap.trajectory == "A":
            res["generalista"] = to_dict(current_roadmap)
        else:
            res["especialista"] = to_dict(current_roadmap)

        for other in others:
            if other.trajectory == "A":
                res["generalista"] = to_dict(other)
            else:
                res["especialista"] = to_dict(other)

        return res
    finally:
        db.close()


# ──────────────────────────────────────────────
# ACTUALIZAR PROGRESO DE BLOQUE
# ──────────────────────────────────────────────

def update_block_progress(roadmap_id: str, block_id: str, completed: bool) -> bool:
    """
    Marks a block as completed or pending in the database.
    """
    db = SessionLocal()
    try:
        roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
        if not roadmap:
            return False

        if completed:
            existing = db.query(Progress).filter(
                Progress.roadmap_id == roadmap_id,
                Progress.block_id == block_id
            ).first()
            if not existing:
                new_progress = Progress(
                    user_id=roadmap.user_id,
                    roadmap_id=roadmap.id,
                    block_id=block_id
                )
                db.add(new_progress)
        else:
            db.query(Progress).filter(
                Progress.roadmap_id == roadmap_id,
                Progress.block_id == block_id
            ).delete()

        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

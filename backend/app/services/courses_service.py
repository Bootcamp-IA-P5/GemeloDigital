"""
Courses Service — Catálogo público de cursos
============================================

Lee el catálogo de cursos desde `data/seed/courses.json` (el mismo
archivo que usa el indexador RAG) y expone funciones de consulta
para los endpoints públicos.
"""

from __future__ import annotations

import json
import os
from typing import List, Dict, Any, Optional


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COURSES_FILE = os.path.join(BASE_DIR, "data", "seed", "courses.json")


# Mapa de categorías temáticas → conjunto de competencias asociadas.
# Esto permite filtrar por "programming", "data", "soft-skills", etc.
CATEGORY_COMPETENCIES_MAP: Dict[str, set[str]] = {
    "programming": {
        "python",
        "programming-fundamentals",
    },
    "data": {
        "sql",
        "data-analysis",
        "machine-learning",
        "data-engineering",
        "gen-ai",
        "data-governance",
    },
    "soft-skills": {
        "communication",
        "leadership",
        "critical-thinking",
    },
    "devops": {
        "cloud",
        "devops",
    },
    "product": {
        "digital-marketing",
        "hr-ai",
        "ai-strategy",
    },
}


def _load_all_courses() -> List[Dict[str, Any]]:
    """Carga todos los cursos desde el JSON de seed."""
    if not os.path.exists(COURSES_FILE):
        return []
    try:
        with open(COURSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data or []
    except Exception:
        # En caso de error de lectura, devolvemos lista vacía para no romper el endpoint.
        return []


def list_courses(
    category: Optional[str] = None,
    level: Optional[str] = None,
    affinity: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Lista cursos del catálogo con filtros opcionales.

    Args:
        category: categoría temática (programming/data/soft-skills/devops/product)
        level: nivel del curso (beginner/intermediate/advanced)
        affinity: afinidad de trayectoria (generalist/specialist/both)
    """
    raw_courses = _load_all_courses()

    results: List[Dict[str, Any]] = []
    for c in raw_courses:
        competencies = c.get("competencies", []) or []
        traj_affinity = c.get("trajectory_affinity", "")
        lvl = c.get("level", "")

        # Filtros opcionales
        if level and lvl != level:
            continue
        if affinity and traj_affinity != affinity:
            continue

        if category:
            comp_set = CATEGORY_COMPETENCIES_MAP.get(category)
            if comp_set:
                if not any(comp in comp_set for comp in competencies):
                    continue

        # Adaptamos la estructura al esquema CourseResponse
        results.append(
            {
                "id": c.get("id"),
                "title": c.get("title"),
                "description": c.get("description"),
                "level": lvl,
                "affinity": traj_affinity,
                "competencies": competencies,
                "duration_hours": c.get("duration_hours", 0),
                "url": c.get("url"),
            }
        )

    return results


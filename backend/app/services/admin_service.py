"""
Admin Service — Lógica de negocio para el panel de administración.
=================================================================
Capa de servicio que encapsula las operaciones de admin: CRUD de cursos,
gestión de usuarios, visualización/edición de roadmaps y métricas.

NOTA: Las funciones usan una dependencia `db` (Session de SQLAlchemy)
que será inyectada cuando el compañero de backend configure la BD.
Mientras tanto, las funciones de catálogo (cursos/competencias) operan
directamente sobre los ficheros JSON de /data/seed/.
"""

import json
from pathlib import Path
from typing import Optional
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # GemeloDigital/
COURSES_PATH = BASE_DIR / "data" / "seed" / "courses.json"
COMPETENCIES_PATH = BASE_DIR / "data" / "seed" / "competencies.json"


# ──────────────────────────────────────────────
# Helpers JSON (funciona sin BD)
# ──────────────────────────────────────────────

def _load_json(path: Path) -> list[dict]:
    """Carga un fichero JSON y devuelve la lista."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: list[dict]):
    """Guarda una lista como JSON con indentación."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ──────────────────────────────────────────────
# CURSOS — CRUD completo sobre courses.json
# ──────────────────────────────────────────────

def list_courses(
    level: Optional[str] = None,
    affinity: Optional[str] = None,
) -> list[dict]:
    """Lista todos los cursos, con filtros opcionales por nivel y afinidad."""
    courses = _load_json(COURSES_PATH)
    if level:
        courses = [c for c in courses if c.get("level") == level]
    if affinity:
        courses = [c for c in courses if c.get("trajectory_affinity") == affinity]
    return courses


def get_course(course_id: str) -> Optional[dict]:
    """Obtiene un curso por ID."""
    courses = _load_json(COURSES_PATH)
    for c in courses:
        if c["id"] == course_id:
            return c
    return None


def create_course(course_data: dict) -> dict:
    """Crea un nuevo curso y lo añade al catálogo."""
    courses = _load_json(COURSES_PATH)

    # Generar ID autoincremental
    existing_ids = [c["id"] for c in courses]
    max_num = 0
    for cid in existing_ids:
        if cid.startswith("DQ-"):
            try:
                max_num = max(max_num, int(cid.split("-")[1]))
            except ValueError:
                pass
    new_id = f"DQ-{max_num + 1:03d}"
    course_data["id"] = new_id

    courses.append(course_data)
    _save_json(COURSES_PATH, courses)
    return course_data


def update_course(course_id: str, updates: dict) -> Optional[dict]:
    """Actualiza campos de un curso existente."""
    courses = _load_json(COURSES_PATH)
    for i, c in enumerate(courses):
        if c["id"] == course_id:
            # Solo actualizar campos no-None
            for key, value in updates.items():
                if value is not None:
                    courses[i][key] = value
            _save_json(COURSES_PATH, courses)
            return courses[i]
    return None


def delete_course(course_id: str) -> bool:
    """Elimina un curso del catálogo."""
    courses = _load_json(COURSES_PATH)
    original_len = len(courses)
    courses = [c for c in courses if c["id"] != course_id]
    if len(courses) < original_len:
        _save_json(COURSES_PATH, courses)
        return True
    return False


# ──────────────────────────────────────────────
# COMPETENCIAS — Lectura de la taxonomía
# ──────────────────────────────────────────────

def list_competencies() -> list[dict]:
    """Lista todas las competencias de la taxonomía."""
    return _load_json(COMPETENCIES_PATH)


def get_competency(comp_id: str) -> Optional[dict]:
    """Obtiene una competencia por ID."""
    for c in _load_json(COMPETENCIES_PATH):
        if c["id"] == comp_id:
            return c
    return None


# ──────────────────────────────────────────────
# USUARIOS — Stubs para cuando exista la BD
# ──────────────────────────────────────────────
# Estas funciones recibirán `db: Session` como parámetro
# cuando el compañero de backend configure SQLAlchemy.

def list_users(db=None, page: int = 1, page_size: int = 20) -> dict:
    """Lista usuarios con paginación. Stub hasta que exista la BD."""
    # TODO: Reemplazar con query real a User model
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


def get_user(user_id: str, db=None) -> Optional[dict]:
    """Obtiene detalle de un usuario. Stub."""
    # TODO: query a User + sus competencias y roadmaps
    return None


def toggle_user_status(user_id: str, is_active: bool, db=None) -> Optional[dict]:
    """Activa/desactiva un usuario. Stub."""
    # TODO: UPDATE user SET is_active = ... WHERE id = ...
    return None


# ──────────────────────────────────────────────
# ROADMAPS — Stubs para cuando exista la BD
# ──────────────────────────────────────────────

def list_roadmaps(
    db=None,
    enfoque: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Lista roadmaps con filtros. Stub."""
    # TODO: query a Roadmap con joins a User y fases
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


def get_roadmap(roadmap_id: str, db=None) -> Optional[dict]:
    """Obtiene un roadmap completo con fases y bloques. Stub."""
    # TODO: query con eager loading de fases y bloques
    return None


def add_block_to_roadmap(
    roadmap_id: str, fase_orden: int, contenido_id: str,
    posicion: Optional[int] = None, db=None,
) -> Optional[dict]:
    """Añade un bloque (curso) a una fase del roadmap. Stub."""
    # TODO: insertar BloqueAprendizaje en la fase indicada
    return None


def remove_block_from_roadmap(
    roadmap_id: str, fase_orden: int, contenido_id: str, db=None,
) -> bool:
    """Elimina un bloque de una fase del roadmap. Stub."""
    # TODO: DELETE BloqueAprendizaje WHERE ...
    return False


# ──────────────────────────────────────────────
# MÉTRICAS — Parcialmente funcional
# ──────────────────────────────────────────────

def get_admin_metrics(db=None) -> dict:
    """
    Calcula métricas del panel de admin.
    Las métricas de cursos funcionan ya (leen del JSON).
    Las métricas de usuarios/roadmaps son stubs hasta que exista la BD.
    """
    courses = _load_json(COURSES_PATH)

    # Métricas que ya funcionan
    total_cursos = len(courses)

    # Métricas que requieren BD (stubs con ceros)
    # TODO: reemplazar con queries reales
    total_usuarios = 0
    total_usuarios_activos = 0
    total_roadmaps = 0
    total_roadmaps_activos = 0
    distribucion_trayectoria = {"A": 0, "B": 0}
    top_cursos = []

    return {
        "total_usuarios": total_usuarios,
        "total_usuarios_activos": total_usuarios_activos,
        "total_roadmaps": total_roadmaps,
        "total_roadmaps_activos": total_roadmaps_activos,
        "total_cursos": total_cursos,
        "distribucion_trayectoria": distribucion_trayectoria,
        "top_cursos_en_roadmaps": top_cursos,
    }

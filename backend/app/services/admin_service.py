"""
Admin Service — Lógica de negocio del panel de administración
=============================================================
Funciones para gestión de cursos, competencias, usuarios,
roadmaps y métricas del panel admin.
Actualmente usa datos stub en memoria; en producción se conectará
a PostgreSQL.

Para uso del compañero de backend:
  - Reemplazar los diccionarios *_DB por queries a las tablas correspondientes
  - Integrar con el indexer RAG para re-indexación de cursos
"""

import uuid

# ──────────────────────────────────────────────
# BASES DE DATOS STUB (en memoria)
# ──────────────────────────────────────────────
COURSES_DB: dict[str, dict] = {
    "curso-python-101": {
        "id": "curso-python-101",
        "titulo": "Python para Principiantes",
        "descripcion": "Curso introductorio de Python para ciencia de datos",
        "nivel": "beginner",
        "afinidad": "both",
        "competencias": ["comp-python"],
        "duracion_horas": 40,
        "url": "https://example.com/python-101",
    },
    "curso-ml-201": {
        "id": "curso-ml-201",
        "titulo": "Introducción a Machine Learning",
        "descripcion": "Fundamentos de ML con scikit-learn",
        "nivel": "intermediate",
        "afinidad": "specialist",
        "competencias": ["comp-ml", "comp-python"],
        "duracion_horas": 60,
        "url": "https://example.com/ml-201",
    },
}

COMPETENCIES_DB: dict[str, dict] = {
    "comp-python": {
        "id": "comp-python",
        "nombre": "Programación en Python",
        "descripcion": "Dominio del lenguaje Python y su ecosistema",
    },
    "comp-ml": {
        "id": "comp-ml",
        "nombre": "Machine Learning",
        "descripcion": "Fundamentos y aplicación de algoritmos de ML",
    },
    "comp-data": {
        "id": "comp-data",
        "nombre": "Análisis de Datos",
        "descripcion": "Capacidad de explorar, limpiar y analizar conjuntos de datos",
    },
}

USERS_DB: dict[str, dict] = {}
ROADMAPS_DB: dict[str, dict] = {}


# ──────────────────────────────────────────────
# CURSOS — CRUD
# ──────────────────────────────────────────────

def list_courses(level: str | None = None, affinity: str | None = None) -> list[dict]:
    """Lista cursos con filtros opcionales por nivel y afinidad."""
    courses = list(COURSES_DB.values())
    if level:
        courses = [c for c in courses if c["nivel"] == level]
    if affinity:
        courses = [c for c in courses if c["afinidad"] == affinity]
    return courses


def get_course(course_id: str) -> dict | None:
    """Obtiene un curso por su ID."""
    return COURSES_DB.get(course_id)


def create_course(data: dict) -> dict:
    """Crea un nuevo curso."""
    course_id = f"curso-{uuid.uuid4().hex[:8]}"
    course = {"id": course_id, **data}
    COURSES_DB[course_id] = course
    return course


def update_course(course_id: str, updates: dict) -> dict | None:
    """Actualiza campos de un curso existente."""
    course = COURSES_DB.get(course_id)
    if not course:
        return None
    course.update(updates)
    return course


def delete_course(course_id: str) -> bool:
    """Elimina un curso. Devuelve True si existía."""
    return COURSES_DB.pop(course_id, None) is not None


# ──────────────────────────────────────────────
# COMPETENCIAS — Solo lectura
# ──────────────────────────────────────────────

def list_competencies() -> list[dict]:
    """Lista todas las competencias de la taxonomía."""
    return list(COMPETENCIES_DB.values())


def get_competency(comp_id: str) -> dict | None:
    """Obtiene una competencia por su ID."""
    return COMPETENCIES_DB.get(comp_id)


# ──────────────────────────────────────────────
# USUARIOS — Stubs
# ──────────────────────────────────────────────

def list_users(page: int = 1, page_size: int = 20) -> dict:
    """Lista usuarios con paginación."""
    users = list(USERS_DB.values())
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": users[start:end],
        "total": len(users),
        "page": page,
        "page_size": page_size,
    }


def get_user(user_id: str) -> dict | None:
    """Obtiene un usuario por su ID."""
    return USERS_DB.get(user_id)


def toggle_user_status(user_id: str, is_active: bool) -> bool:
    """Activa o desactiva un usuario."""
    user = USERS_DB.get(user_id)
    if not user:
        return False
    user["is_active"] = is_active
    return True


# ──────────────────────────────────────────────
# ROADMAPS — Stubs
# ──────────────────────────────────────────────

def list_roadmaps(
    enfoque: str | None = None,
    fecha_desde: str | None = None,
    fecha_hasta: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Lista roadmaps con filtros."""
    roadmaps = list(ROADMAPS_DB.values())
    if enfoque:
        roadmaps = [r for r in roadmaps if r.get("enfoque") == enfoque]
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": roadmaps[start:end],
        "total": len(roadmaps),
        "page": page,
        "page_size": page_size,
    }


def get_roadmap(roadmap_id: str) -> dict | None:
    """Obtiene un roadmap por su ID."""
    return ROADMAPS_DB.get(roadmap_id)


def add_block_to_roadmap(
    roadmap_id: str, fase_orden: int, contenido_id: str, posicion: int | None = None
) -> bool:
    """Añade un bloque a una fase de un roadmap."""
    roadmap = ROADMAPS_DB.get(roadmap_id)
    if not roadmap:
        return False
    for fase in roadmap.get("fases", []):
        if fase["fase_orden"] == fase_orden:
            block = {
                "block_id": f"blk-{uuid.uuid4().hex[:8]}",
                "contenido_id": contenido_id,
                "titulo": f"Curso {contenido_id}",
                "orden": posicion or len(fase["bloques"]) + 1,
                "completado": False,
            }
            fase["bloques"].append(block)
            return True
    return False


def remove_block_from_roadmap(roadmap_id: str, fase_orden: int, contenido_id: str) -> bool:
    """Elimina un bloque de una fase de un roadmap."""
    roadmap = ROADMAPS_DB.get(roadmap_id)
    if not roadmap:
        return False
    for fase in roadmap.get("fases", []):
        if fase["fase_orden"] == fase_orden:
            original_len = len(fase["bloques"])
            fase["bloques"] = [
                b for b in fase["bloques"] if b["contenido_id"] != contenido_id
            ]
            return len(fase["bloques"]) < original_len
    return False


# ──────────────────────────────────────────────
# MÉTRICAS
# ──────────────────────────────────────────────

def get_admin_metrics() -> dict:
    """Devuelve métricas agregadas del panel admin."""
    total_users = len(USERS_DB)
    active_users = sum(1 for u in USERS_DB.values() if u.get("is_active", True))
    total_roadmaps = len(ROADMAPS_DB)

    return {
        "total_usuarios": total_users,
        "usuarios_activos": active_users,
        "total_roadmaps": total_roadmaps,
        "total_cursos": len(COURSES_DB),
        "distribucion_trayectoria": {"generalista": 0, "especialista": 0},
        "top_cursos": [],
    }

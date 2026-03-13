"""
Roadmap Service — Lógica de negocio del roadmap
================================================
Funciones para generar, consultar y actualizar roadmaps.
Actualmente usa datos stub en memoria; en producción orquestará
la pipeline completa: Profiling → RAG → Planning → ML → Explanatory.

Para uso del compañero de backend:
  - Reemplazar ROADMAPS_DB por queries a las tablas `roadmaps` y `progress`
  - Integrar la llamada al orchestrator para la pipeline completa
  - Conectar con el modelo ML para clasificación de trayectorias
"""

import uuid

# ──────────────────────────────────────────────
# BASE DE DATOS STUB (en memoria)
# ──────────────────────────────────────────────
ROADMAPS_DB: dict[str, dict] = {}


# ──────────────────────────────────────────────
# GENERAR ROADMAP
# ──────────────────────────────────────────────

def generate_roadmap(user_id: str, enfoque: str) -> dict:
    """
    Genera un roadmap personalizado para el usuario.

    Pipeline en producción:
      1. Profiling Agent → obtener competency_profile
      2. RAG (ChromaDB) → buscar cursos relevantes
      3. Planning Agent → estructurar fases y bloques
      4. ML Predict → clasificar trayectoria A/B
      5. Explanatory Agent → generar explicación

    Actualmente devuelve un roadmap stub con fases de ejemplo.
    """
    roadmap_id = str(uuid.uuid4())

    roadmap = {
        "roadmap_id": roadmap_id,
        "user_id": user_id,
        "enfoque": enfoque,
        "fases": [
            {
                "fase_orden": 1,
                "nombre": "Fundamentos",
                "bloques": [
                    {
                        "block_id": f"blk-{uuid.uuid4().hex[:8]}",
                        "contenido_id": "curso-python-101",
                        "titulo": "Python para Principiantes",
                        "orden": 1,
                        "completado": False,
                    },
                    {
                        "block_id": f"blk-{uuid.uuid4().hex[:8]}",
                        "contenido_id": "curso-stats-101",
                        "titulo": "Estadística Básica",
                        "orden": 2,
                        "completado": False,
                    },
                ],
            },
            {
                "fase_orden": 2,
                "nombre": "Intermedio",
                "bloques": [
                    {
                        "block_id": f"blk-{uuid.uuid4().hex[:8]}",
                        "contenido_id": "curso-ml-201",
                        "titulo": "Introducción a Machine Learning",
                        "orden": 1,
                        "completado": False,
                    },
                ],
            },
            {
                "fase_orden": 3,
                "nombre": "Avanzado",
                "bloques": [
                    {
                        "block_id": f"blk-{uuid.uuid4().hex[:8]}",
                        "contenido_id": "curso-dl-301",
                        "titulo": "Deep Learning Aplicado",
                        "orden": 1,
                        "completado": False,
                    },
                ],
            },
        ],
        "explicacion": (
            f"Se ha generado un roadmap con enfoque {enfoque} basado en tu perfil "
            "cognitivo. Las fases avanzan progresivamente desde fundamentos "
            "hasta temas avanzados, adaptadas a tus fortalezas y áreas de mejora."
        ),
    }

    ROADMAPS_DB[roadmap_id] = roadmap
    return roadmap


# ──────────────────────────────────────────────
# OBTENER ALTERNATIVAS (Trayectoria A y B)
# ──────────────────────────────────────────────

def get_alternatives(roadmap_id: str) -> dict | None:
    """
    Devuelve ambas trayectorias (generalista y especialista) para un roadmap.

    TODO:
      - Consultar BD para obtener ambas versiones del roadmap
      - Si solo existe una, generar la alternativa con el Planning Agent
    """
    roadmap = ROADMAPS_DB.get(roadmap_id)
    if not roadmap:
        return None

    # Stub: construir alternativa invertida
    enfoque_alt = "ESPECIALISTA" if roadmap["enfoque"] == "GENERALISTA" else "GENERALISTA"

    return {
        "roadmap_id": roadmap_id,
        "generalista": roadmap if roadmap["enfoque"] == "GENERALISTA" else {
            **roadmap,
            "enfoque": "GENERALISTA",
            "explicacion": "Trayectoria generalista alternativa (stub).",
        },
        "especialista": roadmap if roadmap["enfoque"] == "ESPECIALISTA" else {
            **roadmap,
            "enfoque": "ESPECIALISTA",
            "explicacion": "Trayectoria especialista alternativa (stub).",
        },
    }


# ──────────────────────────────────────────────
# ACTUALIZAR PROGRESO DE BLOQUE
# ──────────────────────────────────────────────

def update_block_progress(roadmap_id: str, block_id: str, completado: bool) -> bool:
    """
    Marca un bloque como completado o pendiente.
    Devuelve True si se encontró y actualizó, False en caso contrario.

    TODO: Actualizar tabla `progress` en PostgreSQL.
    """
    roadmap = ROADMAPS_DB.get(roadmap_id)
    if not roadmap:
        return False

    for fase in roadmap["fases"]:
        for bloque in fase["bloques"]:
            if bloque["block_id"] == block_id:
                bloque["completado"] = completado
                return True

    return False

"""
Reindex Service — Puente Backend ↔ RAG Indexer
================================================
Módulo que expone funciones de re-indexación de cursos
para ser llamadas desde el backend (admin_service o routes).

Abstrae la dependencia directa de ChromaDB/SentenceTransformers
para que el backend solo necesite importar este módulo.

Uso desde el backend:
    from ml.reindex_service import reindex_single_course, delete_course_index

    result = reindex_single_course(course_dict)
    # {"status": "ok", "course_id": "crs-py-101"}

    result = delete_course_index("crs-py-101")
    # {"status": "ok", "course_id": "crs-py-101"}
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz esté en el path para importar agents
ROOT_DIR = Path(__file__).resolve().parent.parent  # GemeloDigital/
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def reindex_single_course(course: dict) -> dict:
    """
    Re-indexa un solo curso en ChromaDB.

    Args:
        course: dict del curso con campos id, title, description,
                competencies, level, url, etc.

    Returns:
        dict con status ("ok" o "error") y detalle.
    """
    try:
        from agents.rag.indexer import reindex_course
        return reindex_course(course)
    except ImportError as e:
        return {
            "status": "error",
            "detail": f"No se pudo importar el indexer de agents: {e}"
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": f"Error inesperado al re-indexar: {e}"
        }


def delete_course_index(course_id: str) -> dict:
    """
    Elimina el embedding de un curso de ChromaDB.

    Args:
        course_id: ID del curso a eliminar.

    Returns:
        dict con status ("ok" o "error") y detalle.
    """
    try:
        from agents.rag.indexer import delete_course_embedding
        return delete_course_embedding(course_id)
    except ImportError as e:
        return {
            "status": "error",
            "detail": f"No se pudo importar el indexer de agents: {e}"
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": f"Error inesperado al eliminar embedding: {e}"
        }


def reindex_all_courses() -> dict:
    """
    Re-indexa todos los cursos del catálogo en ChromaDB.
    Útil para reconstruir la BD vectorial completa.

    Returns:
        dict con status ("ok" o "error").
    """
    try:
        from agents.rag.indexer import index_courses
        index_courses()
        return {"status": "ok", "detail": "Todos los cursos re-indexados."}
    except ImportError as e:
        return {
            "status": "error",
            "detail": f"No se pudo importar el indexer de agents: {e}"
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": f"Error inesperado al re-indexar: {e}"
        }

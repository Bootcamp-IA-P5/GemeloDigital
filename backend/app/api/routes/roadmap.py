from fastapi import APIRouter

router = APIRouter()


@router.post("/", summary="Generar roadmap personalizado")
async def create_roadmap():
    """
    Orquesta la pipeline completa:
    Profiling Agent → RAG → Planning Agent → ML Predict → Explanatory Agent.
    """
    # TODO: Llamar al orchestrator con user_id + trajectory preference
    return {"message": "Generar roadmap — pendiente de implementación"}


@router.get("/{roadmap_id}/alternatives", summary="Obtener trayectorias A y B")
async def get_alternatives(roadmap_id: str):
    """Devuelve ambas trayectorias (generalista y especialista) para un roadmap."""
    # TODO: Consultar BD para obtener ambas trayectorias
    return {"message": "Alternativas — pendiente de implementación"}


@router.patch("/{roadmap_id}/block/{block_id}", summary="Marcar bloque completado")
async def update_block_progress(roadmap_id: str, block_id: str):
    """Marca un bloque del roadmap como completado por el usuario."""
    # TODO: Actualizar tabla progress en BD
    return {"message": "Progreso actualizado — pendiente de implementación"}

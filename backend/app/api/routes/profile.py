from fastapi import APIRouter

router = APIRouter()


@router.post("/", summary="Crear perfil cognitivo")
async def create_profile():
    """
    Recibe las respuestas del cuestionario del frontend
    y orquesta el Profiling Agent para generar el competency_profile.
    """
    # TODO: Recibir raw_answers, llamar al orchestrator → Profiling Agent
    return {"message": "Crear perfil — pendiente de implementación"}

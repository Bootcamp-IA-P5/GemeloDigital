import os
from datetime import timedelta

from livekit import api
from livekit.protocol.agent_dispatch import RoomAgentDispatch
from livekit.protocol.room import RoomConfiguration

# Must match WorkerOptions(agent_name=...) in backend/voice_agent/livekit_agent.py
_DATUM_VOICE_AGENT_NAME = os.getenv("LIVEKIT_VOICE_AGENT_NAME", "datum-voice")


def generate_livekit_token(room: str, identity: str, name: str) -> str:
    """
    Genera un token de acceso para LiveKit de forma segura.
    Sustituye la lógica del servidor Node.js original.
    """
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError("LIVEKIT_API_KEY o LIVEKIT_API_SECRET no están configurados en el .env")

    # Crear el token con permisos
    token = api.AccessToken(api_key, api_secret)
    
    # Configurar la identidad y metadatos
    token.with_identity(identity)
    token.with_name(name)
    
    # Otorgar permisos para unirse a la sala, publicar y suscribirse
    # El frontend espera que el agente de voz esté en la sala para interactuar
    grant = api.VideoGrants(
        room_join=True,
        room=room,
        can_publish=True,
        can_subscribe=True
    )
    token.with_grants(grant)

    # Despacho explícito del agente de voz al conectar el participante.
    # Sin esto, algunos proyectos LiveKit Cloud no asignan worker y el cliente
    # se queda solo en la sala (sin avatar / sin voz del agente).
    token.with_room_config(
        RoomConfiguration(
            agents=[
                RoomAgentDispatch(
                    agent_name=_DATUM_VOICE_AGENT_NAME,
                    metadata="{}",
                )
            ]
        )
    )
    
    # El token expira en 1 hora por defecto (igual que el server original)
    token.with_ttl(timedelta(hours=1))

    return token.to_jwt()

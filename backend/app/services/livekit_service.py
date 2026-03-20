import os
from livekit import api
from datetime import timedelta

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
    
    # El token expira en 1 hora por defecto (igual que el server original)
    token.with_ttl(timedelta(hours=1))

    return token.to_jwt()

"""
Auth API Routes — Autenticación
================================
Endpoints FastAPI para registro e inicio de sesión de usuarios.
Genera JWT stubs en memoria; en producción usará bcrypt + python-jose.

Para uso del compañero de backend:
  - Importar este router en main.py:
    from app.api.routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/auth")
  - Configurar dependencias de BD y seguridad (JWT, bcrypt)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from ..schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    MessageResponse,
)
from ...services import auth_service, livekit_service

router = APIRouter(tags=["Autenticación"])


# ──────────────────────────────────────────────
# REGISTRO — Crear nuevo usuario
# ──────────────────────────────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Registrar nuevo usuario",
)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registra un usuario nuevo y devuelve un JWT de acceso.
    """
    return auth_service.register_user(
        db=db,
        email=body.email,
        password=body.password,
        nombre=body.nombre,
    )


# ──────────────────────────────────────────────
# LOGIN — Iniciar sesión
# ──────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica al usuario con email y contraseña y devuelve un JWT.
    """
    return auth_service.login_user(
        db=db,
        email=body.email,
        password=body.password,
    )


# ──────────────────────────────────────────────
# LIVEKIT — Generar token para video/voz
# ──────────────────────────────────────────────

@router.get(
    "/livekit-token",
    summary="Generar token para LiveKit",
)
def get_livekit_token(room: str = "datum-digitaltwin", identity: str = None, name: str = "Usuario"):
    """
    Genera un token de acceso para unirse a una sala de LiveKit.
    
    Parámetros:
      - room: Nombre de la sala (default: datum-digitaltwin)
      - identity: ID único del usuario (si es None, se genera uno)
      - name: Nombre a mostrar
    """
    import uuid
    if not identity:
        identity = f"user-{str(uuid.uuid4())[:8]}"
        
    try:
        token = livekit_service.generate_livekit_token(
            room=room,
            identity=identity,
            name=name
        )
        return {"token": token}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el token: {str(e)}"
        )

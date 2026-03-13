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

from fastapi import APIRouter, HTTPException

from ..schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    MessageResponse,
)
from ...services import auth_service

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
def register(body: RegisterRequest):
    """
    Registra un usuario nuevo y devuelve un JWT de acceso.

    Flujo:
      1. Valida que el email no esté registrado
      2. Hashea la contraseña (TODO: bcrypt)
      3. Persiste en tabla `users` (TODO: PostgreSQL)
      4. Genera un JWT de acceso (TODO: python-jose)

    Respuestas:
      - 201: Usuario creado → TokenResponse
      - 409: Email ya registrado
    """
    result = auth_service.register_user(
        email=body.email,
        password=body.password,
        nombre=body.nombre,
    )
    if result is None:
        raise HTTPException(
            status_code=409,
            detail=f"El email '{body.email}' ya está registrado",
        )
    return result


# ──────────────────────────────────────────────
# LOGIN — Iniciar sesión
# ──────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
)
def login(body: LoginRequest):
    """
    Autentica al usuario con email y contraseña y devuelve un JWT.

    Flujo:
      1. Busca al usuario por email
      2. Verifica la contraseña (TODO: bcrypt.checkpw)
      3. Genera un JWT de acceso (TODO: python-jose)

    Respuestas:
      - 200: Login exitoso → TokenResponse
      - 401: Credenciales inválidas
    """
    result = auth_service.login_user(
        email=body.email,
        password=body.password,
    )
    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas",
        )
    return result

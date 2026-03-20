"""
Auth Service — Lógica de negocio de autenticación
==================================================
Funciones para registro y login de usuarios.
Actualmente usa datos stub en memoria; en producción se conectará
a PostgreSQL y generará JWT reales con python-jose.

Para uso del compañero de backend:
  - Reemplazar el diccionario USERS_DB por queries a la tabla `users`
  - Integrar bcrypt para hash de contraseñas
  - Integrar python-jose para generar JWT reales
"""

import uuid
from datetime import datetime

# ──────────────────────────────────────────────
# BASE DE DATOS STUB (en memoria)
# ──────────────────────────────────────────────
USERS_DB: dict[str, dict] = {}


# ──────────────────────────────────────────────
# REGISTRO
# ──────────────────────────────────────────────

def register_user(email: str, password: str, nombre: str) -> dict:
    """
    Registra un nuevo usuario.
    Devuelve un dict con access_token, token_type, user_id y nombre.

    TODO:
      - Hashear contraseña con bcrypt
      - Persistir en tabla `users`
      - Generar JWT real con python-jose
    """
    # Verificar si el email ya está registrado
    for user in USERS_DB.values():
        if user["email"] == email:
            return None  # Email duplicado

    user_id = str(uuid.uuid4())
    USERS_DB[user_id] = {
        "user_id": user_id,
        "email": email,
        "password": password,  # TODO: hash con bcrypt
        "nombre": nombre,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
    }

    return {
        "access_token": f"stub-jwt-token-{user_id}",
        "token_type": "bearer",
        "user_id": user_id,
        "nombre": nombre,
    }


# ──────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────

def login_user(email: str, password: str) -> dict | None:
    """
    Autentica un usuario por email y contraseña.
    Devuelve un dict con access_token o None si las credenciales son inválidas.

    TODO:
      - Verificar hash con bcrypt.checkpw
      - Generar JWT real con python-jose
    """
    for user in USERS_DB.values():
        if user["email"] == email and user["password"] == password:
            if not user.get("is_active", True):
                return None  # Usuario desactivado
            return {
                "access_token": f"stub-jwt-token-{user['user_id']}",
                "token_type": "bearer",
                "user_id": user["user_id"],
                "nombre": user["nombre"],
            }
    return None

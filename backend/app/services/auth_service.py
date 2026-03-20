"""
Auth Service — Lógica de negocio de autenticación
==================================================
Funciones para registro y login de usuarios con base de datos real.
Utiliza bcrypt para las contraseñas y JWT para las sesiones.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.errors import AppError

# ──────────────────────────────────────────────
# REGISTRO
# ──────────────────────────────────────────────

def register_user(db: Session, email: str, password: str, nombre: str) -> Dict[str, Any]:
    """
    Registra un usuario nuevo en PostgreSQL y devuelve un JWT.
    """
    # Verificar si el email ya existe
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise AppError(status_code=409, detail=f"El email '{email}' ya está registrado")

    # Hashear contraseña y crear usuario
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        password_hash=hashed_password,
        name=nombre,
        role="user",
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generar token real
    user_id_str = str(new_user.id)
    token = create_access_token(data={"user_id": user_id_str})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id_str,
        "name": new_user.name or "Usuario",
    }


# ──────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────

def login_user(db: Session, email: str, password: str) -> Dict[str, Any]:
    """
    Autentica un usuario verificando contra la base de datos y devuelve un JWT.
    """
    user = db.query(User).filter(User.email == email).first()
    
    # Prevenimos enumeración de usuarios usando el mismo mensaje
    if not user or not verify_password(password, user.password_hash):
        raise AppError(status_code=401, detail="Credenciales inválidas")
        
    if not user.is_active:
        raise AppError(status_code=403, detail="Cuenta desactivada")

    user_id_str = str(user.id)
    token = create_access_token(data={"user_id": user_id_str})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id_str,
        "name": user.name or "Usuario",
    }

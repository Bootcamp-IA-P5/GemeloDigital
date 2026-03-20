from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.core.security import decode_access_token
from app.core.errors import AppError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependencia de FastAPI para obtener el usuario autenticado a partir del JWT.
    Extrae el token del header Authorization: Bearer <token>.
    """
    payload = decode_access_token(token)
    if not payload:
        raise AppError(status_code=401, detail="Token inválido o expirado")
    
    user_id: str = payload.get("user_id")
    if not user_id:
        raise AppError(status_code=401, detail="Token no contiene user_id")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppError(status_code=404, detail="Usuario no encontrado")
        
    if not user.is_active:
        raise AppError(status_code=403, detail="Usuario inactivo")
        
    return user

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Valida que el usuario actual tenga rol de administrador."""
    if current_user.role != "admin":
        raise AppError(status_code=403, detail="Privilegios de administrador requeridos")
    return current_user

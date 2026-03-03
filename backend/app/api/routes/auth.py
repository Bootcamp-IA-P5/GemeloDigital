from fastapi import APIRouter

router = APIRouter()


@router.post("/register", summary="Registrar nuevo usuario")
async def register():
    """Registra un usuario y devuelve un JWT."""
    # TODO: Implementar registro con hash de contraseña + JWT
    return {"message": "Registro — pendiente de implementación"}


@router.post("/login", summary="Iniciar sesión")
async def login():
    """Autentica al usuario y devuelve un JWT."""
    # TODO: Implementar login con verificación de credenciales + JWT
    return {"message": "Login — pendiente de implementación"}

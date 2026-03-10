"""
Security — Password Hashing con bcrypt
========================================
Funciones para hashear y verificar contraseñas.
Nunca se almacenan contraseñas en texto plano.

Uso:
    from backend.app.security import hash_password, verify_password

    hashed = hash_password("mi_contraseña_segura")
    # → "$2b$12$..."

    ok = verify_password("mi_contraseña_segura", hashed)
    # → True
"""

import bcrypt


def hash_password(plain_password: str) -> str:
    """
    Genera un hash bcrypt de la contraseña en texto plano.

    bcrypt incluye salt automáticamente en cada hash,
    por lo que dos llamadas con la misma contraseña
    producen hashes diferentes (es lo esperado).

    Args:
        plain_password: Contraseña en texto plano.

    Returns:
        String con el hash bcrypt (incluye salt + cost factor).
    """
    salt = bcrypt.gensalt(rounds=12)  # Cost factor 12 (estándar seguro)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica que una contraseña en texto plano coincide con su hash.

    Args:
        plain_password: Contraseña introducida por el usuario.
        hashed_password: Hash almacenado en la BD.

    Returns:
        True si coinciden, False si no.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

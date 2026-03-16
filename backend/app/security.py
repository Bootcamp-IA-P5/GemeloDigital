"""
Security — Password Hashing (bcrypt) + Cifrado de datos (AES)
===============================================================
Dos capas de seguridad independientes:

  1. HASHING (bcrypt) — para contraseñas
     → Función de un solo sentido: NO se puede recuperar el original.
     → Se usa para almacenar contraseñas de forma segura.

  2. CIFRADO (AES via Fernet) — para datos sensibles
     → Función reversible: se puede cifrar Y descifrar con la clave.
     → Se usa para proteger datos que necesitas leer después
       (emails, datos de perfil, notas privadas, etc.).

Uso:
    from backend.app.security import (
        hash_password, verify_password,
        encrypt_data, decrypt_data,
    )

    # ── Hashing (contraseñas) ──
    hashed = hash_password("mi_contraseña")
    ok = verify_password("mi_contraseña", hashed)  # → True

    # ── Cifrado AES (datos sensibles) ──
    token = encrypt_data("dato secreto")
    # → "gAAAAABl..."  (texto cifrado en base64)
    original = decrypt_data(token)
    # → "dato secreto"
"""

import os
import bcrypt
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


# ──────────────────────────────────────────────
# Configuración AES (Fernet = AES-128-CBC + HMAC-SHA256)
# ──────────────────────────────────────────────

# La clave se lee del .env; si no existe, se genera una temporal
# (en producción SIEMPRE debe estar definida en .env)
AES_SECRET_KEY = os.getenv("AES_SECRET_KEY")

if not AES_SECRET_KEY:
    # ⚠️ Clave temporal — los datos cifrados se pierden al reiniciar
    AES_SECRET_KEY = Fernet.generate_key().decode("utf-8")
    print("⚠️  AES_SECRET_KEY no encontrada en .env — usando clave temporal.")
    print("    Genera una permanente con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")

# Instancia de Fernet (el motor de cifrado/descifrado)
_fernet = Fernet(AES_SECRET_KEY.encode("utf-8") if isinstance(AES_SECRET_KEY, str) else AES_SECRET_KEY)


# ══════════════════════════════════════════════
# 1. HASHING — Contraseñas (bcrypt)
# ══════════════════════════════════════════════

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


# ══════════════════════════════════════════════
# 2. CIFRADO — Datos sensibles (AES via Fernet)
# ══════════════════════════════════════════════

def encrypt_data(plain_text: str) -> str:
    """
    Cifra un texto con AES usando la clave secreta (AES_SECRET_KEY).

    Internamente Fernet usa:
      - AES-128 en modo CBC para el cifrado
      - HMAC-SHA256 para verificar integridad
      - IV (vector de inicialización) aleatorio por cada cifrado
      - Timestamp incluido en el token

    Args:
        plain_text: Texto en claro que quieres proteger.

    Returns:
        Token cifrado en base64 (string seguro para guardar en BD).
    """
    token = _fernet.encrypt(plain_text.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_data(encrypted_token: str) -> str:
    """
    Descifra un token previamente cifrado con encrypt_data().

    Args:
        encrypted_token: Token cifrado (base64 string).

    Returns:
        Texto original en claro.

    Raises:
        cryptography.fernet.InvalidToken: Si la clave es incorrecta
            o el token fue manipulado.
    """
    plain = _fernet.decrypt(encrypted_token.encode("utf-8"))
    return plain.decode("utf-8")

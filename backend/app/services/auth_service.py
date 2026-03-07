"""
Auth Service — Authentication Business Logic
==============================================
Functions for user registration and login.
Currently uses stub data in memory; will connect to PostgreSQL
and generate real JWTs with python-jose in production.

TODO:
  - Replace USERS_DB dict with queries to the `users` table
  - Integrate bcrypt for password hashing
  - Integrate python-jose for real JWT generation
"""

import uuid
from datetime import datetime

# ──────────────────────────────────────────────
# STUB DATABASE (in-memory)
# ──────────────────────────────────────────────
USERS_DB: dict[str, dict] = {}


# ──────────────────────────────────────────────
# REGISTER
# ──────────────────────────────────────────────


def register_user(email: str, password: str, name: str) -> dict | None:
    """
    Register a new user.
    Returns a dict with access_token, token_type, user_id and name.
    Returns None if email is already registered.

    TODO:
      - Hash password with bcrypt
      - Persist in `users` table
      - Generate real JWT with python-jose
    """
    # Check if email is already registered
    for user in USERS_DB.values():
        if user["email"] == email:
            return None  # Duplicate email

    user_id = str(uuid.uuid4())
    USERS_DB[user_id] = {
        "user_id": user_id,
        "email": email,
        "password": password,  # TODO: hash with bcrypt
        "name": name,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
    }

    return {
        "access_token": f"stub-jwt-token-{user_id}",
        "token_type": "bearer",
        "user_id": user_id,
        "name": name,
    }


# ──────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────


def login_user(email: str, password: str) -> dict | None:
    """
    Authenticate a user by email and password.
    Returns a dict with access_token or None if credentials are invalid.

    TODO:
      - Verify hash with bcrypt.checkpw
      - Generate real JWT with python-jose
    """
    for user in USERS_DB.values():
        if user["email"] == email and user["password"] == password:
            if not user.get("is_active", True):
                return None  # User deactivated
            return {
                "access_token": f"stub-jwt-token-{user['user_id']}",
                "token_type": "bearer",
                "user_id": user["user_id"],
                "name": user["name"],
            }
    return None

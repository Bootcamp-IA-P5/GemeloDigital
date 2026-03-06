"""
Schemas Pydantic — Modelos de validación de datos
==================================================
Define los modelos de entrada/salida para los endpoints de la API.
Cada grupo corresponde a un dominio: Auth, Profile, Roadmap, Admin.

Convención:
  - *Request  → datos que envía el cliente
  - *Response → datos que devuelve la API
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ──────────────────────────────────────────────
# COMÚN — Reutilizable en varios dominios
# ──────────────────────────────────────────────

class MessageResponse(BaseModel):
    """Respuesta genérica con un mensaje de texto."""
    message: str


# ──────────────────────────────────────────────
# AUTH — Registro e inicio de sesión
# ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Datos requeridos para registrar un nuevo usuario."""
    email: str = Field(..., description="Correo electrónico del usuario")
    password: str = Field(..., min_length=8, description="Contraseña (mín. 8 caracteres)")
    nombre: str = Field(..., description="Nombre completo del usuario")


class LoginRequest(BaseModel):
    """Credenciales para iniciar sesión."""
    email: str = Field(..., description="Correo electrónico registrado")
    password: str = Field(..., description="Contraseña del usuario")


class TokenResponse(BaseModel):
    """Respuesta con token JWT tras autenticación exitosa."""
    access_token: str = Field(..., description="JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    user_id: str = Field(..., description="ID del usuario autenticado")
    nombre: str = Field(..., description="Nombre del usuario")


# ──────────────────────────────────────────────
# PROFILE — Perfil cognitivo del usuario
# ──────────────────────────────────────────────

class QuestionnaireAnswers(BaseModel):
    """Respuestas del cuestionario enviadas desde el frontend."""
    user_id: str = Field(..., description="ID del usuario")
    respuestas: Dict[str, Any] = Field(
        ...,
        description=(
            "Diccionario con las respuestas del cuestionario. "
            "Clave = ID de la pregunta, Valor = respuesta del usuario"
        ),
    )


class CompetencyScore(BaseModel):
    """Puntuación de una competencia individual."""
    competencia_id: str
    nombre: str
    nivel: str = Field(..., description="Nivel detectado: bajo/medio/alto")
    puntuacion: float = Field(..., ge=0, le=1, description="Score normalizado 0-1")


class CompetencyProfile(BaseModel):
    """Perfil cognitivo generado por el Profiling Agent."""
    user_id: str
    perfil_id: str
    competencias: List[CompetencyScore] = Field(
        default_factory=list,
        description="Lista de competencias evaluadas con su puntuación",
    )
    enfoque_recomendado: str = Field(
        ...,
        description="Trayectoria recomendada: GENERALISTA o ESPECIALISTA",
    )
    resumen: str = Field(..., description="Resumen textual del perfil generado por el agente")


# ──────────────────────────────────────────────
# ROADMAP — Generación y gestión de roadmaps
# ──────────────────────────────────────────────

class RoadmapGenerateRequest(BaseModel):
    """Datos para solicitar la generación de un roadmap personalizado."""
    user_id: str = Field(..., description="ID del usuario")
    enfoque: str = Field(
        ...,
        description="Trayectoria preferida: GENERALISTA o ESPECIALISTA",
    )


class RoadmapBlock(BaseModel):
    """Un bloque (curso) dentro de una fase del roadmap."""
    block_id: str
    contenido_id: str = Field(..., description="ID del curso en el catálogo")
    titulo: str
    orden: int
    completado: bool = False


class RoadmapPhase(BaseModel):
    """Una fase del roadmap con sus bloques."""
    fase_orden: int
    nombre: str
    bloques: List[RoadmapBlock] = Field(default_factory=list)


class RoadmapResponse(BaseModel):
    """Roadmap completo generado para un usuario."""
    roadmap_id: str
    user_id: str
    enfoque: str
    fases: List[RoadmapPhase] = Field(default_factory=list)
    explicacion: str = Field(
        ...,
        description="Explicación del Explanatory Agent sobre por qué se recomienda este roadmap",
    )


class AlternativesResponse(BaseModel):
    """Ambas trayectorias (generalista y especialista) para un roadmap."""
    roadmap_id: str
    generalista: Optional[RoadmapResponse] = None
    especialista: Optional[RoadmapResponse] = None


class BlockProgressUpdate(BaseModel):
    """Datos para marcar un bloque como completado."""
    completado: bool = Field(True, description="Marcar como completado (True) o pendiente (False)")


# ──────────────────────────────────────────────
# ADMIN — Gestión del panel de administración
# ──────────────────────────────────────────────
# (Usados ya por admin.py)

class CourseCreate(BaseModel):
    """Datos para crear un nuevo curso."""
    titulo: str
    descripcion: str
    nivel: str = Field(..., description="beginner/intermediate/advanced")
    afinidad: str = Field(..., description="generalist/specialist/both")
    competencias: List[str] = Field(default_factory=list)
    duracion_horas: int = Field(0, ge=0)
    url: Optional[str] = None


class CourseUpdate(BaseModel):
    """Campos opcionales para actualizar un curso."""
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    nivel: Optional[str] = None
    afinidad: Optional[str] = None
    competencias: Optional[List[str]] = None
    duracion_horas: Optional[int] = None
    url: Optional[str] = None


class CourseResponse(BaseModel):
    """Respuesta con los datos de un curso."""
    id: str
    titulo: str
    descripcion: str
    nivel: str
    afinidad: str
    competencias: List[str] = Field(default_factory=list)
    duracion_horas: int = 0
    url: Optional[str] = None


class UserStatusUpdate(BaseModel):
    """Datos para activar/desactivar un usuario."""
    is_active: bool


class RoadmapBlockAdd(BaseModel):
    """Datos para añadir un bloque a un roadmap."""
    fase_orden: int
    contenido_id: str
    posicion: Optional[int] = None


class RoadmapBlockRemove(BaseModel):
    """Datos para eliminar un bloque de un roadmap."""
    fase_orden: int
    contenido_id: str

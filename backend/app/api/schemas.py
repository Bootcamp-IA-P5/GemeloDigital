"""
Schemas Pydantic para el Panel de Administración.
Define los modelos de request/response para las rutas de admin.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Cursos
# ──────────────────────────────────────────────

class CourseBase(BaseModel):
    title: str
    description: str
    competencies: list[str]
    level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    duration_hours: float = Field(..., gt=0)
    url: str
    trajectory_affinity: str = Field(..., pattern="^(generalist|specialist|both)$")


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    competencies: Optional[list[str]] = None
    level: Optional[str] = None
    duration_hours: Optional[float] = None
    url: Optional[str] = None
    trajectory_affinity: Optional[str] = None


class CourseResponse(CourseBase):
    id: str

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# Usuarios
# ──────────────────────────────────────────────

class UserSummary(BaseModel):
    id: str
    nombre: str
    email: str
    rol_profesional_actual: Optional[str] = None
    nivel_experiencia: Optional[str] = None
    objetivo_profesional: Optional[str] = None
    is_active: bool = True
    fecha_registro: Optional[datetime] = None


class UserStatusUpdate(BaseModel):
    is_active: bool


# ──────────────────────────────────────────────
# Roadmaps
# ──────────────────────────────────────────────

class RoadmapBlock(BaseModel):
    contenido_id: str
    titulo_curso: str
    orden: int
    justificacion_pedagogica: Optional[str] = None


class RoadmapPhase(BaseModel):
    orden: int
    titulo: str
    objetivo_fase: str
    bloques: list[RoadmapBlock] = []


class RoadmapSummary(BaseModel):
    id: str
    usuario_id: str
    usuario_nombre: Optional[str] = None
    fecha_generacion: Optional[datetime] = None
    estado: str  # ACTIVO | HISTORICO
    enfoque: str  # GENERALISTA | ESPECIALISTA
    n_fases: int = 0
    n_bloques: int = 0


class RoadmapDetail(RoadmapSummary):
    fases: list[RoadmapPhase] = []


class RoadmapBlockAdd(BaseModel):
    fase_orden: int
    contenido_id: str
    posicion: Optional[int] = None  # None = al final


class RoadmapBlockRemove(BaseModel):
    fase_orden: int
    contenido_id: str


# ──────────────────────────────────────────────
# Métricas
# ──────────────────────────────────────────────

class CourseUsageStat(BaseModel):
    curso_id: str
    titulo: str
    veces_usado: int


class AdminMetrics(BaseModel):
    total_usuarios: int
    total_usuarios_activos: int
    total_roadmaps: int
    total_roadmaps_activos: int
    total_cursos: int
    distribucion_trayectoria: dict[str, int]  # {"A": N, "B": M}
    top_cursos_en_roadmaps: list[CourseUsageStat]


# ──────────────────────────────────────────────
# Respuestas genéricas
# ──────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int

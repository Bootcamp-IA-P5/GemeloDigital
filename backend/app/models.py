"""
ORM Models — Modelos de Base de Datos (SQLAlchemy)
===================================================
Define las 5 tablas del sistema Gemelo Cognitivo:

    users       → Usuarios registrados (con password_hash bcrypt)
    profiles    → Perfiles cognitivos generados por el Profiling Agent
    courses     → Catálogo formativo (con embedding_id para ChromaDB)
    roadmaps    → Hojas de ruta personalizadas
    progress    → Progreso del usuario en bloques del roadmap

Relaciones:
    users  1──N  profiles
    users  1──N  roadmaps
    users  1──N  progress
    profiles  1──N  roadmaps
    roadmaps  1──N  progress

Uso:
    from backend.app.models import User, Profile, Course, Roadmap, Progress
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from backend.app.database import Base


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────

def _utcnow():
    """Devuelve la hora actual en UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


# ══════════════════════════════════════════════
# USERS — Usuarios registrados
# ══════════════════════════════════════════════

class User(Base):
    """
    Tabla de usuarios del sistema.
    - password_hash: hash bcrypt generado con security.hash_password()
    - role: 'user' (alumno) o 'admin' (administrador del catálogo)
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    name = Column(String(255), nullable=True)
    role = Column(
        String(10),
        nullable=False,
        default="user",  # "user" | "admin"
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # ── Relaciones ──
    profiles = relationship("Profile", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("Progress", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


# ══════════════════════════════════════════════
# PROFILES — Perfiles cognitivos
# ══════════════════════════════════════════════

class Profile(Base):
    """
    Perfil cognitivo generado por el Profiling Agent (LLM).
    - raw_answers: respuestas crudas del cuestionario (JSON)
    - competency_profile: perfil estructurado con puntuaciones (JSON)
    """
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # JSON con las respuestas originales del cuestionario
    raw_answers = Column(JSON, nullable=True)

    # JSON con el perfil de competencias generado por el agente
    # Estructura esperada: { competencies: [...], recommended_approach: "...", summary: "..." }
    competency_profile = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # ── Relaciones ──
    user = relationship("User", back_populates="profiles")
    roadmaps = relationship("Roadmap", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Profile {self.id} for user {self.user_id}>"


# ══════════════════════════════════════════════
# COURSES — Catálogo formativo
# ══════════════════════════════════════════════

class Course(Base):
    """
    Curso del catálogo formativo.
    - competencies: JSON array con IDs de competencias
    - embedding_id: referencia al vector en ChromaDB
      Cuando el admin edita un curso, se lanza el re-embedding
      automáticamente para mantener PostgreSQL ↔ ChromaDB sincronizados.
    """
    __tablename__ = "courses"

    id = Column(String(50), primary_key=True)  # e.g. "crs-py-101"
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    url = Column(String(1000), nullable=True)

    # JSON array con IDs de competencias: ["python", "machine-learning"]
    competencies = Column(JSON, nullable=False, default=list)

    level = Column(
        String(20),
        nullable=False,
        default="beginner",  # "beginner" | "intermediate" | "advanced"
    )

    duration_hours = Column(Float, nullable=False, default=0)

    trajectory_affinity = Column(
        String(20),
        nullable=False,
        default="both",  # "generalist" | "specialist" | "both"
    )

    # 🧠 Referencia al vector embedding en ChromaDB
    # Se usa para sincronizar la BD relacional con la BD vectorial.
    # Valor = ID del documento en la colección ChromaDB (normalmente = course.id)
    embedding_id = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    def __repr__(self):
        return f"<Course {self.id}: {self.title}>"


# ══════════════════════════════════════════════
# ROADMAPS — Hojas de ruta personalizadas
# ══════════════════════════════════════════════

class Roadmap(Base):
    """
    Hoja de ruta generada por el pipeline de agentes.
    - trajectory: "A" (Generalista) o "B" (Especialista)
    - ml_prediction: JSON con la salida completa del modelo ML
    - phases: JSON con la estructura de fases y bloques
    """
    __tablename__ = "roadmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Trayectoria clasificada: "A" (Generalista) o "B" (Especialista)
    trajectory = Column(String(1), nullable=False)  # "A" | "B"

    # JSON con la predicción completa del modelo ML
    # Estructura: { trajectory: "GENERALIST", confidence: 0.78, raw_label: "A" }
    ml_prediction = Column(JSON, nullable=True)

    # JSON con las fases y bloques del roadmap
    # Estructura: [ { phase_order: 1, name: "...", blocks: [...] }, ... ]
    phases = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # ── Relaciones ──
    user = relationship("User", back_populates="roadmaps")
    profile = relationship("Profile", back_populates="roadmaps")
    progress = relationship("Progress", back_populates="roadmap", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Roadmap {self.id} trajectory={self.trajectory}>"


# ══════════════════════════════════════════════
# PROGRESS — Progreso en bloques del roadmap
# ══════════════════════════════════════════════

class Progress(Base):
    """
    Registro de progreso: un usuario completa un bloque de un roadmap.
    Cada fila = un bloque marcado como completado.
    """
    __tablename__ = "progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    roadmap_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ID del bloque específico dentro del roadmap (referencia al JSON de phases)
    block_id = Column(String(100), nullable=False)

    completed_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # ── Constraints ──
    __table_args__ = (
        # Un usuario solo puede completar un bloque una vez por roadmap
        UniqueConstraint("user_id", "roadmap_id", "block_id", name="uq_user_roadmap_block"),
    )

    # ── Relaciones ──
    user = relationship("User", back_populates="progress")
    roadmap = relationship("Roadmap", back_populates="progress")

    def __repr__(self):
        return f"<Progress user={self.user_id} block={self.block_id}>"

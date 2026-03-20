"""
Database Configuration — SQLAlchemy Engine & Session
=====================================================
Configura la conexión a PostgreSQL usando SQLAlchemy.
Lee DATABASE_URL desde el archivo .env.

Uso:
    from app.database import SessionLocal, engine, Base, get_db

    # En FastAPI con Depends:
    @app.get("/example")
    def example(db: Session = Depends(get_db)):
        ...
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar variables de entorno
load_dotenv()

# ──────────────────────────────────────────────
# Configuración
# ──────────────────────────────────────────────

# URL de conexión a PostgreSQL
# Formato: postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:root@localhost:5432/gemelo_cognitivo"
)

# Crear el engine de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=False,  # True para ver las queries SQL en consola (debug)
    pool_pre_ping=True,  # Verifica que la conexión siga viva
)

# Fábrica de sesiones (una sesión por request HTTP)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base declarativa para los modelos ORM
Base = declarative_base()


# ──────────────────────────────────────────────
# Dependency Injection para FastAPI
# ──────────────────────────────────────────────

def get_db():
    """
    Generador que inyecta una sesión de BD en cada request.
    Se usa con FastAPI Depends():

        @app.get("/users")
        def list_users(db: Session = Depends(get_db)):
            ...

    La sesión se cierra automáticamente al terminar el request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Crea todas las tablas en la BD.
    Ejecutar una vez al inicio o como migration inicial.

        from app.database import init_db
        init_db()
    """
    import app.models  # noqa: F401 — registra los modelos con Base
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas en la base de datos.")

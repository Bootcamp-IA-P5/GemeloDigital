# ──────────────────────────────────────────────────────────────
# 📌 IMPORTS
# ──────────────────────────────────────────────────────────────
from contextlib import asynccontextmanager          # Para gestionar el ciclo de vida de la app (startup/shutdown)

from fastapi import FastAPI, Request, status        # Framework web + objeto Request + códigos HTTP
from fastapi.middleware.cors import CORSMiddleware   # Middleware para permitir peticiones cross-origin (frontend)
from fastapi.responses import JSONResponse           # Para construir respuestas JSON personalizadas

# ──────────────────────────────────────────────────────────────
# 📌 IMPORTS DE ROUTERS (endpoints organizados por dominio)
# ──────────────────────────────────────────────────────────────
from app.api.routes import auth, profile, roadmap, admin

# ──────────────────────────────────────────────────────────────
# 📌 LIFESPAN — Ciclo de vida de la aplicación
# ──────────────────────────────────────────────────────────────
# FastAPI usa "lifespan" para ejecutar código al arrancar y al
# apagar el servidor. Aquí es donde conectarás la base de datos,
# cargarás el modelo ML, o inicializarás ChromaDB en el futuro.
# ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP: se ejecuta UNA VEZ al arrancar el servidor ──
    print("🚀 Servidor arrancando...")
    # TODO: Conectar a PostgreSQL
    # TODO: Cargar modelo ML (joblib.load)
    # TODO: Inicializar cliente de ChromaDB

    yield  # ← La app se ejecuta entre el startup y el shutdown

    # ── SHUTDOWN: se ejecuta al apagar el servidor ──
    print("🛑 Servidor apagándose...")
    # TODO: Cerrar conexiones de BD
    # TODO: Liberar recursos


# ──────────────────────────────────────────────────────────────
# 📌 INSTANCIA DE FASTAPI
# ──────────────────────────────────────────────────────────────
# Aquí se crea la aplicación. Los parámetros definen los
# metadatos que aparecen en la documentación automática
# de Swagger (accesible en /docs cuando el servidor corre).
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Gemelo Cognitivo API",                              # Nombre que aparece en Swagger UI
    description=(
        "API REST para el sistema de Gemelo Cognitivo de Aprendizaje. "
        "Orquesta tres agentes LLM (Profiling, Planning, Explanatory), "
        "una pipeline RAG con ChromaDB, y un modelo ML de clasificación "
        "de trayectorias formativas."
    ),
    version="0.1.0",                                           # Versión del MVP
    lifespan=lifespan,                                         # Registra los eventos de startup/shutdown
)


# ──────────────────────────────────────────────────────────────
# 📌 MIDDLEWARE — CORS (Cross-Origin Resource Sharing)
# ──────────────────────────────────────────────────────────────
# El frontend (React en otro puerto/dominio) necesita permiso
# para hacer peticiones HTTP a esta API. Sin CORS, el navegador
# bloquea las peticiones por seguridad.
#
# ⚠️  En producción, reemplaza allow_origins=["*"] por la URL
#     real del frontend (ej: ["https://mi-app.vercel.app"]).
# ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Orígenes permitidos ("*" = todos, solo para desarrollo)
    allow_credentials=True,         # Permitir envío de cookies/tokens en las peticiones
    allow_methods=["*"],            # Métodos HTTP permitidos (GET, POST, PATCH, DELETE, etc.)
    allow_headers=["*"],            # Headers permitidos (Authorization, Content-Type, etc.)
)


# ──────────────────────────────────────────────────────────────
# 📌 HANDLER GLOBAL DE EXCEPCIONES
# ──────────────────────────────────────────────────────────────
# Captura CUALQUIER excepción no manejada en la app y devuelve
# un JSON limpio en vez de un error 500 genérico del servidor.
# Esto es clave para que el frontend siempre reciba respuestas
# parseables, incluso cuando algo falla inesperadamente.
# ──────────────────────────────────────────────────────────────
@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ──────────────────────────────────────────────────────────────
# 📌 REGISTRO DE ROUTERS
# ──────────────────────────────────────────────────────────────
# Cada router agrupa los endpoints de un dominio. FastAPI los
# monta bajo un prefijo de URL y les asigna un tag para que
# aparezcan organizados en la documentación Swagger.
# ──────────────────────────────────────────────────────────────
app.include_router(
    auth.router,
    prefix="/auth",                # Todas las rutas de auth.py empezarán con /auth/...
    tags=["Autenticación"],        # Grupo en Swagger UI
)

app.include_router(
    profile.router,
    prefix="/api/profile",         # Rutas de perfil bajo /api/profile/...
    tags=["Perfil"],
)

app.include_router(
    roadmap.router,
    prefix="/api/roadmap",         # Rutas de roadmap bajo /api/roadmap/...
    tags=["Roadmap"],
)

app.include_router(
    admin.router,
    prefix="/api/admin",           # Rutas de admin bajo /api/admin/...
    tags=["Administración"],
)


# ──────────────────────────────────────────────────────────────
# 📌 HEALTH CHECK — Ruta raíz
# ──────────────────────────────────────────────────────────────
# Endpoint mínimo para verificar que la API está viva.
# Útil para:
#   - Monitoreo de health en Railway/Render
#   - Verificación rápida durante desarrollo
#   - Load balancers que comprueban si el servicio responde
# ──────────────────────────────────────────────────────────────
@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    response_model=dict,
)
async def health_check():
    """Devuelve el estado de la API."""
    return {
        "status": "ok",
        "app": "Gemelo Cognitivo API",
        "version": "0.1.0",
    }

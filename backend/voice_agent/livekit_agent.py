"""
Datum Voice Agent — Entrevistador Cognitivo con Avatar
======================================================
Usa LiveKit Agents 1.x con @function_tool para extraer
el perfil profesional del usuario mediante conversación
y guardarlo automáticamente en PostgreSQL.
"""

import os
import json
import uuid
import logging
import traceback
import httpx
from dotenv import load_dotenv

# ── DB imports (funciona tanto en Docker como en local) ──
try:
    from backend.app.database import SessionLocal
    from backend.app.models import User, Profile, Roadmap
    DB_AVAILABLE = True
except ImportError:
    try:
        from app.database import SessionLocal
        from app.models import User, Profile, Roadmap
        DB_AVAILABLE = True
    except ImportError:
        DB_AVAILABLE = False
        print("⚠️ BD no disponible. El perfil no se guardará.")

from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.bey import AvatarSession

logger = logging.getLogger("datum-voice-agent")

# Cargar variables de entorno
load_dotenv(os.path.join(os.getcwd(), "../../.env"))
load_dotenv(".env")


# ══════════════════════════════════════════════
# AGENTE PRINCIPAL — Datum
# ══════════════════════════════════════════════

class DigitalTwin(Agent):
    def __init__(self) -> None:
        instructions = (
            "Eres Datum, el Asistente de IA de la plataforma Datum.\n\n"
            "TU MISIÓN: Entrevistar al usuario para conocer su perfil profesional. "
            "Debes averiguar estos 3 datos:\n"
            "1. Su rol actual o profesión (ej: desarrollador, diseñador, estudiante).\n"
            "2. Su objetivo profesional — qué quiere ser o aprender.\n"
            "3. Su nivel de experiencia (años, junior/senior, etc.).\n\n"
            "GUARDARRAÍLES:\n"
            "- NUNCA menciones 'DataQuantum'. Solo conoces 'Datum'.\n"
            "- NUNCA recomiendes cursos de otras plataformas ni hables de contenido externo.\n"
            "- Si te preguntan algo fuera de tu misión (política, deportes, etc.), "
            "redirige educadamente: 'Eso no es lo mío, pero cuéntame más de tu carrera.'\n"
            "- Habla SIEMPRE en español. NUNCA en inglés.\n\n"
            "CUANDO TENGAS LOS 3 DATOS: llama a la función 'finish_onboarding' "
            "pasándole el rol actual, el objetivo y los años de experiencia.\n\n"
            "ESTILO:\n"
            "- Sé conciso, cálido y motivador.\n"
            "- No hagas las 3 preguntas a la vez; haz una entrevista fluida natural.\n"
            "- Respuestas de 1-3 frases."
        )
        super().__init__(instructions=instructions)

    @function_tool()
    async def finish_onboarding(
        self,
        context: RunContext,
        current_role: str,
        target_role: str,
        experience_years: int,
    ):
        """Finaliza la entrevista cognitiva y guarda el perfil del usuario.

        Args:
            current_role: El rol o profesión actual del usuario.
            target_role: El objetivo profesional o lo que quiere aprender.
            experience_years: Años de experiencia profesional del usuario.
        """
        logger.info("═══════════════════════════════════════════")
        logger.info("🎯 FINISH ONBOARDING — Extrayendo perfil...")
        logger.info(f"   Rol actual: {current_role}")
        logger.info(f"   Objetivo:   {target_role}")
        logger.info(f"   Experiencia: {experience_years} años")
        logger.info("═══════════════════════════════════════════")

        if not DB_AVAILABLE:
            logger.warning("BD no disponible. No se guardará el perfil.")
            return "He recogido tus datos pero no puedo guardarlos ahora. Inténtalo más tarde."

        db = SessionLocal()
        try:
            # Buscar o crear usuario de demo
            user = db.query(User).filter(User.id == "user-123").first()
            if not user:
                user = User(
                    id="user-123",
                    email="demo@datum.ai",
                    password_hash="not-a-real-hash",
                    name="Usuario Demo",
                    role="user",
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info("✅ Usuario demo creado: user-123")

            # Construir el perfil de competencias
            # Generamos competencias básicas según el target_role
            competencies = _generate_basic_competencies(target_role)

            raw_answers = {
                "user_id": "user-123",
                "currentRole": current_role,
                "targetRole": target_role,
                "experience": experience_years,
                "source": "voice_interview",
            }

            competency_profile = {
                "competencies": competencies,
                "recommended_approach": "GENERALISTA" if experience_years < 3 else "ESPECIALISTA",
                "summary": (
                    f"Profesional con {experience_years} años de experiencia como {current_role}. "
                    f"Busca transición hacia {target_role}."
                ),
            }

            # Guardar en BD (solo perfil; el roadmap lo generará el pipeline de agentes en el backend)
            profile = Profile(
                id=str(uuid.uuid4()),
                user_id="user-123",
                raw_answers=raw_answers,
                competency_profile=competency_profile,
            )
            db.add(profile)
            db.commit()
            logger.info(f"✅ Perfil guardado en BD: {profile.id}")

            return (
                f"¡Perfecto! Ya he guardado tu perfil. "
                f"Eres {current_role} y quieres orientarte hacia {target_role}. "
                f"Entra al Dashboard para generar y ver tu Roadmap personalizado. ¡Mucho ánimo!"
            )

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error guardando perfil: {e}")
            logger.exception("Traceback completo (para diagnosticar BD, tablas o constraints):")
            return "Ha habido un problema guardando tus datos. Inténtalo de nuevo."
        finally:
            db.close()


def _generate_basic_competencies(target_role: str) -> list:
    """
    Genera competencias básicas según el objetivo del usuario.
    En producción esto lo haría el Profiling Agent con un LLM.
    """
    role_lower = target_role.lower()

    # Competencias base según área
    if any(k in role_lower for k in ["data", "dato", "machine learning", "ml", "ia", "inteligencia"]):
        return [
            {"competency_id": "python", "name": "Python", "score": 0.5},
            {"competency_id": "ml-fundamentals", "name": "ML Fundamentals", "score": 0.3},
            {"competency_id": "statistics", "name": "Estadística", "score": 0.4},
            {"competency_id": "deep-learning", "name": "Deep Learning", "score": 0.2},
            {"competency_id": "sql", "name": "SQL & Bases de Datos", "score": 0.5},
            {"competency_id": "data-viz", "name": "Visualización de Datos", "score": 0.4},
        ]
    elif any(k in role_lower for k in ["front", "web", "react", "diseño", "ux", "ui"]):
        return [
            {"competency_id": "html-css", "name": "HTML & CSS", "score": 0.6},
            {"competency_id": "javascript", "name": "JavaScript", "score": 0.5},
            {"competency_id": "react", "name": "React", "score": 0.3},
            {"competency_id": "ux-design", "name": "Diseño UX/UI", "score": 0.4},
            {"competency_id": "responsive", "name": "Responsive Design", "score": 0.5},
            {"competency_id": "testing-fe", "name": "Testing Frontend", "score": 0.2},
        ]
    elif any(k in role_lower for k in ["back", "server", "api", "devops", "cloud"]):
        return [
            {"competency_id": "python", "name": "Python", "score": 0.5},
            {"competency_id": "rest-api", "name": "REST APIs", "score": 0.4},
            {"competency_id": "docker", "name": "Docker & Containers", "score": 0.3},
            {"competency_id": "databases", "name": "Bases de Datos", "score": 0.5},
            {"competency_id": "ci-cd", "name": "CI/CD", "score": 0.2},
            {"competency_id": "security", "name": "Seguridad Web", "score": 0.3},
        ]
    else:
        # Competencias genéricas
        return [
            {"competency_id": "problem-solving", "name": "Resolución de Problemas", "score": 0.5},
            {"competency_id": "communication", "name": "Comunicación", "score": 0.5},
            {"competency_id": "digital-literacy", "name": "Competencia Digital", "score": 0.4},
            {"competency_id": "teamwork", "name": "Trabajo en Equipo", "score": 0.5},
            {"competency_id": "self-learning", "name": "Autoaprendizaje", "score": 0.4},
            {"competency_id": "project-mgmt", "name": "Gestión de Proyectos", "score": 0.3},
        ]


def _generate_roadmap_phases(competencies: list, target_role: str) -> list:
    """
    Genera un roadmap de 3 fases basado en las competencias del usuario.
    Las competencias con score más bajo van primero (mayor gap).
    """
    # Ordenar por score (menor primero = mayor gap)
    sorted_comps = sorted(competencies, key=lambda c: c.get("score", 0.5))

    # Dividir en 3 fases
    phase_1_comps = sorted_comps[:2]  # Las 2 más débiles → Fundamentos
    phase_2_comps = sorted_comps[2:4]  # Las 2 intermedias → Profundización
    phase_3_comps = sorted_comps[4:]   # Las restantes → Especialización

    def _make_blocks(comps, phase_num):
        blocks = []
        for i, c in enumerate(comps):
            cid = c.get("competency_id", f"comp-{i}")
            name = c.get("name", "Curso")
            blocks.append({
                "content_id": f"course-{cid}",
                "course_id": f"course-{cid}",
                "title": f"Curso de {name} para {target_role}",
                "priority": "required" if phase_num == 1 else "recommended",
                "duration": "10h" if phase_num <= 2 else "15h",
                "level": ["beginner", "intermediate", "advanced"][phase_num - 1],
                "completed": False,
                "why": f"Tu nivel actual en {name} necesita refuerzo para alcanzar tu objetivo.",
                "competencies_addressed": [cid],
            })
        return blocks

    phases = [
        {
            "phase_order": 1,
            "name": "Fase 1: Fundamentos",
            "blocks": _make_blocks(phase_1_comps, 1),
        },
        {
            "phase_order": 2,
            "name": "Fase 2: Profundización",
            "blocks": _make_blocks(phase_2_comps, 2),
        },
    ]

    if phase_3_comps:
        phases.append({
            "phase_order": 3,
            "name": "Fase 3: Especialización",
            "blocks": _make_blocks(phase_3_comps, 3),
        })

    return phases


# ══════════════════════════════════════════════
# ENTRYPOINT — Punto de entrada del agente
# ══════════════════════════════════════════════

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)

    # LLM: Groq con Llama 3.1 (gratis)
    groq_llm = openai.LLM(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ.get("GROQ_API_KEY", ""),
        model="llama-3.1-8b-instant",
    )

    # Avatar Bey (vídeo del gemelo digital)
    avatar = AvatarSession(
        avatar_id=os.environ.get("BEY_AVATAR_ID"),
        api_key=os.environ.get("BEY_API_KEY"),
    )

    # Sesión de voz
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(language="es", model="nova-2"),
        llm=groq_llm,
        tts=cartesia.TTS(
            model="sonic-multilingual",
            language="es",
            voice=os.environ.get("CARTESIA_VOICE_ID", "ccfea4bf-b3f4-421e-87ed-dd05dae01431"),
        ),
    )

    # Iniciar avatar + sesión
    await avatar.start(session, room=ctx.room)

    await session.start(
        room=ctx.room,
        agent=DigitalTwin(),
    )

    # Saludo inicial
    await session.generate_reply(
        instructions=(
            "Saluda al usuario en español de manera cálida y profesional. "
            "Dile que eres Datum y que te gustaría conocerle para crear su ruta de aprendizaje. "
            "Pregúntale a qué se dedica actualmente. "
            "Hazlo en 2 frases máximo. SOLO en español."
        )
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

import os
import sys
from dotenv import load_dotenv

try:
    from backend.app.database import SessionLocal
    from backend.app.models import User, Profile
    DB_ID_AVAILABLE = True
except ImportError:
    try:
        from app.database import SessionLocal
        from app.models import User, Profile
        DB_ID_AVAILABLE = True
    except ImportError:
        DB_ID_AVAILABLE = False
        print("⚠️ No se pudo cargar el backend para consultar la BD. Usando modo genérico.")

from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import cartesia, deepgram, openai, silero, llm
from livekit.plugins.bey import AvatarSession
import logging

logger = logging.getLogger("voice-agent")

# Cargar .env: Intentar en raíz, si no en el directorio actual
load_dotenv(os.path.join(os.getcwd(), "../../.env"))
load_dotenv(".env")


class AssistantFunctions(llm.FunctionContext):
    """Acciones que el agente puede ejecutar durante la charla."""

    @llm.ai_callable(description="Finaliza la entrevista cuando Datum tiene info suficiente y guarda el perfil.")
    async def finish_onboarding(self):
        logger.info("BOTÓN PULSADO: Datum finaliza la entrevista.")
        # Aquí dispararemos la extracción real en el siguiente paso
        return "Perfecto, he guardado tus datos. En unos segundos verás tu Roadmap en el Dashboard."

class DigitalTwin(Agent):
    def __init__(self, user_name: str = "Usuario", user_details: str = "") -> None:
        instructions = (
            f"Eres Datum, el Asistente de IA de la plataforma Datum. Hablas con {user_name}.\n\n"
            "TU MISIÓN: Entrevistar al usuario para conocer su perfil profesional. Debes averiguar:\n"
            "1. Su rol actual o profesión.\n"
            "2. Su objetivo profesional (qué quiere ser).\n"
            "3. Su nivel de experiencia o tiempo disponible.\n\n"
            "GUARDARRAÍLES Y REGLAS ESTRICTAS:\n"
            "- NUNCA menciones a 'DataQuantum'. Si te preguntan, di que solo conoces Datum.\n"
            "- NUNCA recomiendes cursos específicos de otras plataformas ni hables de contenido formativo externo.\n"
            "- Habla SIEMPRE en español. NUNCA en inglés.\n"
            "- Cuando tengas toda la info (los 3 puntos de arriba), usa la función 'finish_onboarding'.\n\n"
            "ESTILO:\n"
            "- Sé conciso, cálido y motivador.\n"
            "- No hagas las 3 preguntas a la vez; haz una entrevista fluida."
        )
        super().__init__(instructions=instructions)


async def entrypoint(ctx: JobContext):
    # Conectar al room — necesitamos audio y vídeo para el avatar
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)

    user_name = "Usuario"
    user_details = "Aún no tenemos datos detallados de tu perfil."

    # Intentar obtener el perfil del último usuario registrado para la demo
    if DB_ID_AVAILABLE:
        db = SessionLocal()
        try:
            # Buscamos el perfil más reciente
            profile = db.query(Profile).order_by(Profile.created_at.desc()).first()
            if profile and profile.user:
                user_name = profile.user.name or "Usuario"
                competencies = profile.competency_profile or {}
                summary = competencies.get("summary", "Sin resumen.")
                user_details = f"El usuario se llama {user_name}. Su resumen de perfil es: {summary}"
        except Exception as e:
            print(f"Error consultando BD: {e}")
        finally:
            db.close()

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

    # Sesión de voz con STT español + LLM + TTS español
    fnc_ctx = AssistantFunctions()
    
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(
            language="es",
            model="nova-2",
        ),
        llm=groq_llm,
        tts=cartesia.TTS(
            model="sonic-multilingual",
            language="es",
            voice="ccfea4bf-b3f4-421e-87ed-dd05dae01431",
        ),
        fnc_ctx=fnc_ctx,
    )

    # Iniciar el avatar + la sesión de voz juntos
    await avatar.start(session, room=ctx.room)

    await session.start(
        room=ctx.room,
        agent=DigitalTwin(user_name=user_name, user_details=user_details),
    )

    # Saludo inicial en español
    await session.generate_reply(
        instructions=(
            f"Saluda a {user_name} en español de España de manera cálida y profesional. "
            "Dile que eres Datum, el asistente de voz de Datum Gemelo IA. "
            "Menciona algo breve sobre que ya conoces su perfil si tienes datos disponibles. "
            "Dile que estás listo para ayudarle con su plan de carrera y competencias. "
            "Hazlo en 2 frases máximo. SOLO en español."
        )
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

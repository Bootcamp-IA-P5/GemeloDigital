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
from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.bey import AvatarSession

# Cargar .env: Intentar en raíz, si no en el directorio actual
load_dotenv(os.path.join(os.getcwd(), "../../.env"))
load_dotenv(".env")


class DigitalTwin(Agent):
    def __init__(self, user_name: str = "Usuario", user_details: str = "") -> None:
        instructions = (
            f"Eres Datum, un asistente de voz de IA para la plataforma Datum Gemelo IA. "
            f"Estás hablando con {user_name}. "
            "Tu rol es ayudar al usuario a entender sus competencias profesionales, "
            "orientarle en su plan de aprendizaje y responder sobre su roadmap de carrera. "
            "\n\n"
            "DETALLES DEL USUARIO:\n"
            f"{user_details}\n\n"
            "REGLAS ESTRICTAS DE IDIOMA:\n"
            "- Habla SIEMPRE en español. NUNCA en inglés, ni una sola palabra.\n"
            "- Si el usuario habla en inglés, respóndele en español de todas formas.\n"
            "- Habla de forma natural, cercana y motivadora.\n"
            "- Sé conciso: respuestas cortas de 1-3 oraciones al inicio.\n"
            "- El usuario te puede interrumpir — para de hablar si lo hace.\n"
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

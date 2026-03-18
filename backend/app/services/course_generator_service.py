"""
Course Generator Service — Extracción de contenido desde URL (Fase 1)
=====================================================================
Fase 1: extrae el texto principal de una URL para usarlo como fuente del curso.
Usa solo biblioteca estándar (sin dependencias nuevas).

Fase 2: generará estructura del curso (diapositivas + guion) usando un LLM.
"""

import re
import urllib.error
import urllib.request
from typing import List, Optional, Tuple

# Límite de caracteres para no cargar páginas enormes en memoria
MAX_CONTENT_CHARS = 150_000
# Timeout de la petición HTTP (segundos)
URL_TIMEOUT = 10


def extract_text_from_url(url: str) -> Tuple[str, str | None]:
    """
    Descarga la URL y extrae texto plano del HTML (quita scripts, estilos y tags).

    Returns:
        (texto_extraido, error). Si error es None, texto_extraido tiene el contenido.
        El texto se trunca a MAX_CONTENT_CHARS.
    """
    if not url or not url.strip().startswith(("http://", "https://")):
        return "", "URL debe ser http o https"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GemeloCourseGenerator/1.0"})
        with urllib.request.urlopen(req, timeout=URL_TIMEOUT) as resp:
            raw = resp.read()
            # Intentar decodificar
            for enc in ("utf-8", "latin-1", "cp1252"):
                try:
                    html = raw.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return "", "No se pudo decodificar el contenido de la página"
    except urllib.error.HTTPError as e:
        return "", f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return "", f"Error de conexión: {e.reason}"
    except TimeoutError:
        return "", "La página tardó demasiado en responder"
    except Exception as e:
        return "", str(e)

    # Quitar scripts y estilos para reducir ruido
    html = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    # Sustituir tags por espacios y decodificar entidades básicas
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"&amp;", "&", text, flags=re.IGNORECASE)
    text = re.sub(r"&lt;", "<", text, flags=re.IGNORECASE)
    text = re.sub(r"&gt;", ">", text, flags=re.IGNORECASE)
    text = re.sub(r"&quot;", '"', text, flags=re.IGNORECASE)
    # Normalizar espacios
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_CONTENT_CHARS:
        text = text[:MAX_CONTENT_CHARS] + " [truncado]"
    return text, None


# ==========================================
# Fase 2: Generación de slides + guion
# ==========================================


# Nota: Definimos los esquemas aquí para mantener el cambio aislado.
try:
    from pydantic import BaseModel, Field

    class _SlideModel(BaseModel):
        # El LLM a veces omite esta propiedad. La hacemos opcional y
        # rellenamos nosotros en post-procesado para evitar fallos de validación.
        slide_number: Optional[int] = Field(default=None, ge=1)
        title: str
        bullets: List[str] = Field(default_factory=list, description="3-5 bullets breves")
        script: str = Field(..., description="Guion narrativo para el slide (2-4 frases)")

    class _CourseGenerationResult(BaseModel):
        course_title: str
        target_audience: str
        learning_objectives: List[str] = Field(default_factory=list, description="5-7 objetivos")
        slides: List[_SlideModel] = Field(default_factory=list, description="8-12 slides")

    class _SlideImagePromptModel(BaseModel):
        # El LLM puede omitir slide_number. Lo dejamos opcional y lo normalizamos luego.
        slide_number: Optional[int] = Field(default=None, ge=1)
        # Prompt pensado para un generador de imágenes (idealmente en inglés) y sin texto embebido.
        image_prompt: str = Field(..., description="Prompt para generar la imagen de la slide (evita texto en la imagen)")
        # Texto alternativo en español (para accesibilidad / frontend).
        alt_text: str = Field(..., description="Descripción alternativa de la imagen (en español)")

    class _ImagePromptsResult(BaseModel):
        image_style: str = Field(..., description="Estilo visual general consistente para todas las slides")
        slides_image_prompts: List[_SlideImagePromptModel] = Field(
            default_factory=list,
            description="Lista de prompts por slide (misma cantidad y orden)",
        )

except Exception:  # pragma: no cover
    # Si por alguna razón falla la importación de pydantic/langchain en runtime,
    # dejaremos la función de generación fallar con un error claro.
    _SlideModel = None
    _CourseGenerationResult = None
    _ImagePromptsResult = None


def generate_course_slides_and_script(
    source_text: str,
    prompt: Optional[str] = None,
    *,
    max_source_chars: int = 30_000,
) -> Tuple[dict, str | None]:
    """
    Genera una estructura de curso (diapositivas + guion) a partir del texto fuente.

    Returns:
        (result_dict, error). Si error es None, result_dict contiene el JSON del curso.
    """
    if not source_text or not source_text.strip():
        return {}, "No hay texto fuente para generar el curso"
    if _CourseGenerationResult is None:
        return {}, "El generador de curso requiere dependencias de LLM que no se pudieron cargar"

    try:
        from dotenv import load_dotenv
        from langchain_groq import ChatGroq
        from langchain_core.prompts import ChatPromptTemplate

        from agents.utils.guardrails import handle_llm_output_error, validate_and_format_response

        load_dotenv()

        source_text_limited = source_text[:max_source_chars]
        user_prompt = prompt.strip() if prompt else ""

        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.2,
            max_retries=2,
        )

        structured_llm = llm.with_structured_output(_CourseGenerationResult)

        system_instructions = (
            "Eres un diseñador instruccional y guionista pedagógico. "
            "Genera un curso coherente en ESPAÑOL usando únicamente el texto fuente proporcionado. "
            "Devuelve una respuesta que cumpla estrictamente el esquema JSON solicitado."
        )

        human_instructions = (
            "PROMPT DEL USUARIO (opcional, sigue sus instrucciones si no contradicen el texto):\n"
            "{user_prompt}\n\n"
            "TEXTO FUENTE (puede estar ruidoso y truncado):\n"
            "{source_text}\n\n"
            "Genera:\n"
            "- Un `course_title` claro.\n"
            "- `target_audience` en 1 frase.\n"
            "- `learning_objectives` con 5-7 objetivos accionables.\n"
            "- `slides` con 8-12 slides.\n"
            "- En cada slide incluye `slide_number` (empieza en 1 y sigue en orden).\n"
            "  - Cada slide debe tener 3-5 `bullets` breves.\n"
            "  - Cada slide debe incluir un `script` de 2-4 frases para narración.\n"
            "Reglas:\n"
            "- No inventes datos específicos no presentes en el texto.\n"
            "- Mantén coherencia conceptual entre slides.\n"
        )

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_instructions),
                ("human", human_instructions),
            ]
        )

        chain = prompt_template | structured_llm
        response_model = chain.invoke(
            {
                "user_prompt": user_prompt if user_prompt else "(sin prompt adicional)",
                "source_text": source_text_limited,
            }
        )

        course_dict = validate_and_format_response(response_model)
        # Normaliza slide_number en caso de que el LLM lo haya omitido.
        slides = course_dict.get("slides") or []
        for idx, s in enumerate(slides):
            if isinstance(s, dict) and not s.get("slide_number"):
                s["slide_number"] = idx + 1
        course_dict["slides"] = slides
        return course_dict, None
    except Exception as error:
        # Reutilizamos guardrails para mantener formato consistente.
        try:
            from agents.utils.guardrails import handle_llm_output_error

            return handle_llm_output_error(error), str(error)
        except Exception:
            return {}, str(error)


def generate_course_image_prompts(
    slides: List[dict],
    prompt: Optional[str] = None,
    *,
    max_slides: int = 12,
) -> Tuple[dict, str | None]:
    """
    Fase 2-2: genera prompts de imagen (uno por slide) a partir de `slides`.

    Nota: en este MVP todavía no generamos bitmaps; devolvemos prompts listos
    para que el frontend/servicio de imágenes los renderice más adelante.
    """
    if not slides:
        return {}, "No hay slides para generar image_prompts"
    if _ImagePromptsResult is None:
        return {}, "El generador de prompts de imagen requiere dependencias de LLM que no se pudieron cargar"

    try:
        from dotenv import load_dotenv
        from langchain_groq import ChatGroq
        from langchain_core.prompts import ChatPromptTemplate

        from agents.utils.guardrails import handle_llm_output_error, validate_and_format_response

        load_dotenv()

        limited_slides = slides[:max_slides]

        # Compactamos el contexto: suficiente para que el LLM proponga composición + estilo,
        # pero evitando meter guiones completos.
        slides_context = [
            {
                "slide_number": s.get("slide_number"),
                "title": s.get("title"),
                "bullets": s.get("bullets", [])[:5],
                "script_snippet": (s.get("script") or "")[:180],
            }
            for s in limited_slides
        ]

        user_prompt = prompt.strip() if prompt else ""

        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_retries=2,
        )
        structured_llm = llm.with_structured_output(_ImagePromptsResult)

        system_instructions = (
            "Eres un director de arte para educación digital. "
            "Debes proponer prompts consistentes para un generador de imágenes. "
            "Reglas: NO incluyas texto dentro de la imagen (sin letras, sin frases, sin títulos). "
            "Mantén coherencia de estilo entre todas las slides."
        )

        human_instructions = (
            "PROMPT DEL USUARIO (opcional):\n"
            "{user_prompt}\n\n"
            "OBJETIVO: generar prompts de imagen para CADA slide.\n\n"
            "SLIDES (entrada):\n"
            "{slides_json}\n\n"
            "Salida requerida (JSON estructurado):\n"
            "- `image_style`: describe el estilo consistente (ej: flat vector, isométrico, etc.)\n"
            "- `slides_image_prompts`: lista con 1 elemento por slide, en el mismo orden.\n"
            "  - Cada elemento con `slide_number` (si es posible), `image_prompt` (en inglés, sin texto) y `alt_text` (en español).\n"
        )

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_instructions),
                ("human", human_instructions),
            ]
        )

        chain = prompt_template | structured_llm
        response_model = chain.invoke(
            {
                "user_prompt": user_prompt if user_prompt else "(sin prompt adicional)",
                "slides_json": slides_context,
            }
        )

        image_dict = validate_and_format_response(response_model)
        # Normaliza slide_number si el LLM no lo devolvió.
        ip = image_dict.get("slides_image_prompts") or []
        for idx, s in enumerate(ip):
            if isinstance(s, dict) and not s.get("slide_number"):
                s["slide_number"] = idx + 1
        image_dict["slides_image_prompts"] = ip
        return image_dict, None

    except Exception as error:
        try:
            from agents.utils.guardrails import handle_llm_output_error

            return handle_llm_output_error(error), str(error)
        except Exception:
            return {}, str(error)

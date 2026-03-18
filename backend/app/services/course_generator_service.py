"""
Course Generator Service — Extracción de contenido desde URL (Fase 1)
=====================================================================
Extrae el texto principal de una URL para usarlo como fuente del curso.
Usa solo biblioteca estándar (sin dependencias nuevas).
"""

import re
import urllib.error
import urllib.request
from typing import Tuple

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

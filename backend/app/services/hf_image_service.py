"""
HF Image Service — Generación de imágenes desde prompts
==========================================================
Transforma `image_prompts` (generados por el LLM) en imágenes reales usando
Hugging Face Inference API.

MVP:
 - Genera 1 imagen PNG por slide.
 - Guarda las imágenes en disco dentro de `backend/app/static/generated-courses/<course_id>/`.
 - Devuelve URLs relativas para servirlas desde FastAPI (StaticFiles).
"""

from __future__ import annotations

import json
import os
import uuid
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv


DEFAULT_HF_MODEL = os.getenv("HF_IMAGE_MODEL", "stabilityai/stable-diffusion-2")
HF_ENDPOINT = f"https://api-inference.huggingface.co/models/{DEFAULT_HF_MODEL}"


def _try_load_dotenv_from_filesystem() -> None:
    """
    En Docker, el `.env` puede no estar en el CWD.
    Buscamos el archivo cerca del path del código (subiendo directorios).
    """
    start_dir = os.path.dirname(os.path.abspath(__file__))
    cur = start_dir
    for _ in range(8):
        candidate = os.path.join(cur, ".env")
        if os.path.exists(candidate):
            load_dotenv(dotenv_path=candidate, override=False)
            return
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent


def _static_generated_root() -> str:
    # backend/app/services/* -> backend/app
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_dir = os.path.join(app_dir, "static", "generated-courses")
    os.makedirs(static_dir, exist_ok=True)
    return static_dir


def generate_images_from_prompts(
    image_prompts: List[Dict[str, Any]],
    image_style: str,
    *,
    course_id: Optional[str] = None,
    max_images: int = 12,
    timeout_s: int = 120,
) -> Tuple[List[Dict[str, Any]], str | None]:
    """
    Args:
        image_prompts: lista con elementos como:
          { "slide_number": 1, "image_prompt": "...", "alt_text": "..." }
        image_style: estilo global (flat vector, etc.)
        course_id: carpeta destino. Si no existe, se genera un UUID.
        max_images: límite para no disparar costes ilimitados.
    Returns:
        (items, err). items incluye {slide_number, image_url, image_path, alt_text}
    """
    _try_load_dotenv_from_filesystem()

    # Obtenemos el token en runtime (evita problemas si el módulo se importó antes
    # de que el contenedor inyectara variables de entorno).
    hf_api_key = os.getenv("HF_API_KEY") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not hf_api_key or hf_api_key == "your_hf_token_here":
        return [], (
            "Falta HF API token (HF_API_KEY o HUGGINGFACEHUB_API_TOKEN) en el entorno. "
            "En Docker normalmente hay que asegurar que el contenedor recibe la `.env` correcta "
            "y reiniciar/rebuild el backend."
        )
    if not image_prompts:
        return [], "No hay image_prompts para generar"

    generation_id = course_id or f"gen-{uuid.uuid4().hex[:10]}"
    out_root = os.path.join(_static_generated_root(), generation_id)
    os.makedirs(out_root, exist_ok=True)

    limited = image_prompts[:max_images]
    results: List[Dict[str, Any]] = []

    for idx, p in enumerate(limited):
        slide_number = p.get("slide_number") or (idx + 1)
        image_prompt = p.get("image_prompt") or ""
        alt_text = p.get("alt_text") or ""

        full_prompt = image_prompt
        if image_style:
            full_prompt = f"{image_style}. {image_prompt}"

        payload = {
            "inputs": full_prompt,
            "options": {
                # Evita que el modelo “se duerma” demasiado y espera el resultado.
                # Si no es soportado por el modelo, se ignora.
                "wait_for_model": True,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            HF_ENDPOINT,
            data=data,
            headers={
                "Authorization": f"Bearer {hf_api_key}",
                "Content-Type": "application/json",
                # Intentamos forzar respuesta binaria de imagen
                "Accept": "image/png",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            # A veces el cuerpo es JSON con mensaje de error
            try:
                body = e.read().decode("utf-8", errors="ignore")
                return [], f"HF HTTPError {e.code}: {body}"
            except Exception:
                return [], f"HF HTTPError {e.code}: {e.reason}"
        except Exception as e:
            return [], f"HF request failed: {str(e)}"

        # Si el modelo devuelve JSON en vez de bytes PNG
        if raw.strip().startswith(b"{") or raw.strip().startswith(b"["):
            try:
                parsed = json.loads(raw.decode("utf-8", errors="ignore"))
                return [], f"HF returned JSON instead of image: {parsed}"
            except Exception:
                return [], "HF returned unexpected JSON payload"

        file_name = f"slide_{int(slide_number)}.png"
        file_path = os.path.join(out_root, file_name)
        with open(file_path, "wb") as f:
            f.write(raw)

        # URL relativa servida por StaticFiles
        image_url = f"/static/generated-courses/{generation_id}/{file_name}"

        results.append(
            {
                "slide_number": slide_number,
                "image_url": image_url,
                "image_path": file_path,
                "alt_text": alt_text,
            }
        )

    return results, None


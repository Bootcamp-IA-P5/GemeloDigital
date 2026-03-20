"""
Unsplash Image Service — Descarga de imágenes desde Unsplash
===============================================================
Convierte `image_prompts` (generados por el LLM) en imágenes reales
descargando fotos desde Unsplash.

MVP:
 - 1 imagen por slide (máximo `max_images`)
 - Guarda las imágenes en disco dentro de
   `backend/app/static/generated-courses/<course_id>/`
 - Devuelve URLs relativas para que `pptx_deck_service` use `image_path`
"""

from __future__ import annotations

import json
import os
import re
import uuid
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv


SEARCH_ENDPOINT = "https://api.unsplash.com/search/photos"


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


def _fetch_json(url: str, *, headers: Dict[str, str], timeout_s: int) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read()
    decoded = raw.decode("utf-8", errors="ignore")
    return json.loads(decoded)


def _download_bytes(url: str, *, timeout_s: int) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "GemeloUnsplashImageService/1.0",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read()


def _normalize_query(s: str) -> str:
    s = (s or "").strip()
    s = s.replace("\n", " ")
    s = " ".join(s.split())
    return s[:140]


def _candidate_queries(image_style: str, image_prompt: str) -> List[str]:
    prompt = _normalize_query(image_prompt)
    style = _normalize_query(image_style)

    banned = [
        "flat vector",
        "vector",
        "illustration",
        "isometric",
        "3d",
        "infographic",
        "icon",
        "logo",
        "cartoon",
        "drawing",
        "anime",
        "watercolor",
        "poster",
    ]

    cleaned = prompt
    for b in banned:
        cleaned = re.sub(re.escape(b), "", cleaned, flags=re.IGNORECASE)
    cleaned = _normalize_query(cleaned)

    shortened = " ".join(cleaned.split()[:7]).strip() if cleaned else ""

    base = shortened or cleaned or prompt or "education technology"
    fallback = _normalize_query(f"education technology {base}")

    candidates = [
        _normalize_query(f"{style} {prompt}".strip()),
        prompt,
        shortened,
        fallback,
    ]

    seen = set()
    out: List[str] = []
    for c in candidates:
        c = _normalize_query(c)
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def generate_images_from_prompts(
    image_prompts: List[Dict[str, Any]],
    image_style: str,
    *,
    course_id: Optional[str] = None,
    max_images: int = 12,
    timeout_s: int = 30,
) -> Tuple[List[Dict[str, Any]], str | None]:
    """
    Args:
        image_prompts: lista con elementos como:
          { "slide_number": 1, "image_prompt": "...", "alt_text": "..." }
        image_style: estilo global (flat vector, etc.) que usamos como keyword
        course_id: carpeta destino. Si no existe, se genera un UUID.
        max_images: límite para no disparar llamadas ilimitadas.
        timeout_s: timeout por llamada HTTP.

    Returns:
        (items, err). items incluye {slide_number, image_url, image_path, alt_text}
    """
    _try_load_dotenv_from_filesystem()

    unsplash_api_key = os.getenv("UNPLASH_API_KEY")
    if not unsplash_api_key:
        return [], "Falta UNPLASH_API_KEY en el entorno."

    if not image_prompts:
        return [], "No hay image_prompts para generar"

    generation_id = course_id or f"gen-{uuid.uuid4().hex[:10]}"
    out_root = os.path.join(_static_generated_root(), generation_id)
    os.makedirs(out_root, exist_ok=True)

    headers = {
        # Unsplash soporta Authorization: Client-ID <key>
        "Authorization": f"Client-ID {unsplash_api_key}",
        "Accept-Version": "v1",
    }

    limited = image_prompts[:max_images]
    results: List[Dict[str, Any]] = []

    for idx, p in enumerate(limited):
        slide_number = p.get("slide_number") or (idx + 1)
        image_prompt = (p.get("image_prompt") or "").strip()
        alt_text = p.get("alt_text") or ""

        if not image_prompt:
            image_prompt = "education"

        # Unsplash busca fotos; los prompts del LLM suelen incluir estilos gráficos ("flat vector", etc.),
        # que a veces hacen que no haya resultados. Probamos varias queries con fallback.
        candidate_queries = _candidate_queries(image_style, image_prompt)

        photo: Optional[Dict[str, Any]] = None
        last_query: Optional[str] = None
        last_unsplash_err: Optional[str] = None

        for query in candidate_queries:
            last_query = query
            url = f"{SEARCH_ENDPOINT}?{urllib.parse.urlencode({'query': query, 'per_page': 5})}"
            try:
                data = _fetch_json(url, headers=headers, timeout_s=timeout_s)
            except urllib.error.HTTPError as e:
                try:
                    body = e.read().decode("utf-8", errors="ignore")
                except Exception:
                    body = ""
                last_unsplash_err = f"HTTPError {e.code}: {body[:200]}"
                continue
            except Exception as e:
                last_unsplash_err = f"request failed: {str(e)[:200]}"
                continue

            results_list = data.get("results") or []
            if not results_list:
                continue

            first = results_list[0] or {}
            if isinstance(first, dict) and first:
                photo = first
                break

        if not photo:
            details = f" query_last={last_query!r}" if last_query else ""
            details2 = f" last_err={last_unsplash_err}" if last_unsplash_err else ""
            return [], f"Unsplash no devolvió resultados para ninguna query.{details}{details2}"
        photo_urls = photo.get("urls") or {}
        # regular suele ser suficientemente grande para PPTX
        image_source_url = photo_urls.get("regular") or photo_urls.get("small") or photo_urls.get("raw")
        if not image_source_url:
            return [], "Unsplash result no tenía `urls` descargables"

        try:
            raw = _download_bytes(image_source_url, timeout_s=timeout_s)
        except urllib.error.HTTPError as e:
            return [], f"Unsplash download HTTPError {e.code}: {e.reason}"
        except Exception as e:
            return [], f"Unsplash download failed: {str(e)}"

        file_name = f"slide_{int(slide_number)}.jpg"
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


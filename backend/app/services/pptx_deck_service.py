"""
PPTX Deck Service — Construir un deck con imágenes + contenido
===============================================================
Genera un `.pptx` colocando:
 - Imagen por slide (generada con HF)
 - Título
 - Bullets (3-5)
 - Script (opcional como texto pequeño)

Salida:
 - Guarda el archivo en `backend/app/static/generated-courses/<course_id>/deck.pptx`
 - Devuelve `deck_file_url` (URL relativa servida por StaticFiles)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple


def _static_generated_root() -> str:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/app
    static_dir = os.path.join(app_dir, "static", "generated-courses")
    os.makedirs(static_dir, exist_ok=True)
    return static_dir


def build_pptx_deck(
    *,
    course_id: str,
    slides: List[Dict[str, Any]],
    images_by_slide_number: List[Dict[str, Any]],
    deck_title: Optional[str] = None,
) -> Tuple[str, str | None]:
    """
    Args:
        slides: lista de slides con {slide_number,title,bullets,script}
        images_by_slide_number: lista con {slide_number,image_path} (o image_url)
    Returns:
        (deck_file_url, err)
    """
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
    except Exception as e:
        return "", f"Falta python-pptx/Pillow en runtime: {str(e)}"

    generation_dir = os.path.join(_static_generated_root(), course_id)
    os.makedirs(generation_dir, exist_ok=True)

    # Mapa rápido slide_number -> image_path
    img_map: Dict[int, str] = {}
    for item in images_by_slide_number:
        try:
            sn = int(item.get("slide_number"))
        except Exception:
            continue
        img_path = item.get("image_path")
        if img_path and os.path.exists(img_path):
            img_map[sn] = img_path

    prs = Presentation()

    # Respaldo: layout en blanco suele ser el índice 6
    BLANK_LAYOUT_IDX = 6

    for slide in slides:
        sn = slide.get("slide_number")
        try:
            sn_int = int(sn)
        except Exception:
            sn_int = None

        title = slide.get("title", "")
        bullets = slide.get("bullets", []) or []
        script = slide.get("script", "")

        layout = prs.slide_layouts[BLANK_LAYOUT_IDX] if len(prs.slide_layouts) > BLANK_LAYOUT_IDX else prs.slide_layouts[0]
        slide_obj = prs.slides.add_slide(layout)

        # Imagen (centrada a la izquierda)
        img_path = img_map.get(sn_int) if sn_int is not None else None
        if img_path:
            # Tamaño aproximado y márgenes conservadores
            pic_left = Inches(0.6)
            pic_top = Inches(1.4)
            pic_width = Inches(5.0)
            try:
                slide_obj.shapes.add_picture(img_path, pic_left, pic_top, width=pic_width)
            except Exception:
                # Si la imagen falla, seguimos con el texto.
                pass

        # Título arriba
        title_box = slide_obj.shapes.add_textbox(Inches(0.6), Inches(0.3), Inches(6.9), Inches(0.8))
        title_tf = title_box.text_frame
        title_tf.clear()
        p = title_tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(24)

        # Bullets en columna derecha
        text_box = slide_obj.shapes.add_textbox(Inches(6.0), Inches(1.4), Inches(2.8), Inches(3.8))
        tf = text_box.text_frame
        tf.clear()

        # Agregamos bullets como lista
        for i, b in enumerate(bullets[:6]):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.text = str(b)
            para.level = 0
            para.font.size = Pt(16)

        # Script como "nota" (texto pequeño al final del texto)
        if script:
            para = tf.add_paragraph()
            para.text = f"Guion: {script}"
            para.font.size = Pt(10)

    deck_file_name = "deck.pptx"
    deck_file_path = os.path.join(generation_dir, deck_file_name)
    prs.save(deck_file_path)

    deck_file_url = f"/static/generated-courses/{course_id}/{deck_file_name}"
    return deck_file_url, None


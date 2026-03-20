# Data Quantum PPTX Theme Notes

El preset visual del deck se configura en:

- `backend/app/services/pptx_theme_data_quantum.json`

## Que puedes ajustar sin tocar logica

- **Paleta**: `palette`
  - `navy`, `green`, `orange`, `light_bg`, `text_primary`, `text_secondary`
- **Tipografia**: `typography`
  - `font_family`, tamanos (`cover_title_pt`, `slide_title_pt`, `subtitle_pt`, `body_pt`, `footer_pt`)
- **Espaciado**: `spacing`
  - margenes y alturas base
- **Reglas de densidad**: `limits`
  - `max_bullets_per_slide`
  - `max_chars_per_bullet`

## Motor de render

- Archivo: `backend/app/services/pptx_deck_service.py`
- Layouts fijos:
  - `cover`
  - `agenda`
  - `section-divider`
  - `content-bullets`
  - `content-two-columns`
  - `closing`

El LLM solo aporta el contenido; el diseno siempre lo impone este engine.

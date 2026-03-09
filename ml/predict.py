"""
Path Predictor — Módulo de predicción para integración con el backend
=====================================================================
Carga el modelo entrenado (path_predictor.pkl) y expone funciones
de predicción compatibles con los schemas del backend.

Mapping de etiquetas ML ↔ Backend API:
    A  →  GENERALIST   (trayectoria generalista)
    B  →  SPECIALIST   (trayectoria especialista)

El campo `dominant_domain` corresponde al campo `domain`
de la taxonomía en data/seed/competencies.json:
    - "Datos e IA"
    - "Programación y Desarrollo"
    - "Cloud e Infraestructura"
    - "Gestión y Producto"
    - "Habilidades Transversales"

Uso desde el backend / orquestador:
    from ml.predict import predict_trajectory

    result = predict_trajectory(
        experience_years=3,
        avg_current_level=2.5,
        avg_gap=2.0,
        n_competencies=5,
        dominant_domain="Datos e IA",
        objetivo_profesional="Data Scientist",
    )
    # result = {"trajectory": "GENERALIST", "confidence": 0.78, "raw_label": "A"}
"""

from pathlib import Path
from typing import Optional

import numpy as np
import joblib

# ──────────────────────────────────────────────
# Rutas y constantes
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent  # ml/
MODEL_PATH = BASE_DIR / "models" / "path_predictor.pkl"

# Mapping ML labels → Backend API labels
LABEL_MAP = {
    "A": "GENERALIST",
    "B": "SPECIALIST",
}

# Reverse mapping para uso interno
LABEL_MAP_REVERSE = {v: k for k, v in LABEL_MAP.items()}


def _load_model():
    """Carga el artefacto del modelo entrenado."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modelo no encontrado en {MODEL_PATH}. "
            "Ejecuta 'python ml/train.py' primero."
        )
    return joblib.load(MODEL_PATH)


def predict_trajectory(
    experience_years: float,
    avg_current_level: float,
    avg_gap: float,
    n_competencies: int,
    dominant_domain: str,
    objetivo_profesional: str,
) -> dict:
    """
    Predice la trayectoria formativa de un usuario.

    Args:
        experience_years: Años de experiencia profesional.
        avg_current_level: Nivel medio actual en competencias (0-5).
        avg_gap: Gap medio respecto al nivel objetivo.
        n_competencies: Número de competencias evaluadas.
        dominant_domain: Dominio principal del perfil del usuario.
        objetivo_profesional: Objetivo profesional declarado.

    Returns:
        dict con:
            - trajectory: "GENERALIST" o "SPECIALIST" (compatible con schemas del backend)
            - confidence: float 0-1

    Raises:
        FileNotFoundError: Si el modelo no ha sido entrenado.
    """
    artifact = _load_model()
    model = artifact["model"]
    encoder = artifact["encoder"]
    numeric_features = artifact["numeric_features"]
    categorical_features = artifact["categorical_features"]

    # Preparar features
    num_vals = np.array([[experience_years, avg_current_level, avg_gap, n_competencies]])
    cat_vals = encoder.transform([[dominant_domain, objetivo_profesional]])
    X = np.hstack([num_vals, cat_vals])

    # Predicción
    raw_label = model.predict(X)[0]  # "A" o "B"
    probas = model.predict_proba(X)[0]

    # Índice de la clase predicha para obtener confianza
    class_idx = list(model.classes_).index(raw_label)
    confidence = float(probas[class_idx])

    return {
        "trajectory": LABEL_MAP[raw_label],
        "confidence": round(confidence, 4),
        "raw_label": raw_label,
    }


def predict_batch(profiles: list[dict]) -> list[dict]:
    """
    Predicción en batch para múltiples perfiles.

    Args:
        profiles: Lista de dicts, cada uno con las mismas keys
                  que los args de predict_trajectory.

    Returns:
        Lista de resultados de predicción.
    """
    return [predict_trajectory(**p) for p in profiles]

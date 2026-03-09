"""
Path Predictor — Clasificador de trayectoria formativa (Generalista vs Especialista)
====================================================================================
Carga el dataset sintético, entrena Logistic Regression y Random Forest,
compara métricas y exporta el mejor modelo como path_predictor.pkl.

Uso:
    python ml/train.py
"""

import os
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)
import joblib

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────
# Rutas
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent            # ml/
DATA_PATH = BASE_DIR / "data" / "path_labels.csv"
MODELS_DIR = BASE_DIR / "models"
MODEL_OUTPUT = MODELS_DIR / "path_predictor.pkl"
REPORT_OUTPUT = MODELS_DIR / "training_report.json"

RANDOM_STATE = 42
TEST_SIZE = 0.20

NUMERIC_FEATURES = [
    "experience_years",
    "avg_current_level",
    "avg_gap",
    "n_competencies",
]
CATEGORICAL_FEATURES = ["dominant_domain", "objetivo_profesional"]
TARGET = "chosen_trajectory"


def load_data(path: Path) -> pd.DataFrame:
    """Carga el CSV y valida que tiene las columnas esperadas."""
    print(f"📂 Cargando datos de {path}")
    df = pd.read_csv(path)
    expected = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"Columnas faltantes en CSV: {missing}")
    print(f"   ➜ {len(df)} filas, {len(df.columns)} columnas")
    print(f"   ➜ Distribución de target:\n{df[TARGET].value_counts().to_string()}\n")
    return df


def preprocess(df: pd.DataFrame):
    """One-hot encoding de dominant_domain y split train/test."""
    # One-hot encoding
    encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    cat_encoded = encoder.fit_transform(df[CATEGORICAL_FEATURES])
    cat_columns = encoder.get_feature_names_out(CATEGORICAL_FEATURES)

    # Combinar features numéricas + categóricas
    X_numeric = df[NUMERIC_FEATURES].values
    X = np.hstack([X_numeric, cat_encoded])
    feature_names = NUMERIC_FEATURES + list(cat_columns)

    y = df[TARGET].values

    # Split 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    print(f"✂️  Split: {len(X_train)} train / {len(X_test)} test")
    print(f"   ➜ Features: {feature_names}\n")

    return X_train, X_test, y_train, y_test, feature_names, encoder


def evaluate(model, name: str, X_test, y_test) -> dict:
    """Evalúa un modelo y devuelve dict con métricas."""
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, pos_label="B", zero_division=0)
    rec = recall_score(y_test, y_pred, pos_label="B", zero_division=0)
    f1 = f1_score(y_test, y_pred, pos_label="B", zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=["A", "B"])

    print(f"{'='*50}")
    print(f"📊 {name}")
    print(f"{'='*50}")
    print(f"   Accuracy:  {acc:.4f}")
    print(f"   Precision: {prec:.4f}")
    print(f"   Recall:    {rec:.4f}")
    print(f"   F1-Score:  {f1:.4f}")
    print(f"\n   Confusion Matrix (rows=true, cols=pred):")
    print(f"              Pred A   Pred B")
    print(f"   True A   {cm[0][0]:>6}   {cm[0][1]:>6}")
    print(f"   True B   {cm[1][0]:>6}   {cm[1][1]:>6}")
    print()
    print(classification_report(y_test, y_pred, labels=["A", "B"], zero_division=0))

    return {
        "model_name": name,
        "accuracy": round(acc, 4),
        "precision_B": round(prec, 4),
        "recall_B": round(rec, 4),
        "f1_B": round(f1, 4),
        "confusion_matrix": cm.tolist(),
    }


def get_feature_importances(model, name: str, feature_names: list):
    """Muestra la importancia de las features si el modelo lo soporta."""
    if hasattr(model, "coef_"):
        importances = np.abs(model.coef_[0])
    elif hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    else:
        return

    pairs = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    print(f"🔍 Feature importances ({name}):")
    for feat, imp in pairs:
        bar = "█" * int(imp / max(importances) * 20)
        print(f"   {feat:<45} {imp:.4f}  {bar}")
    print()


def main():
    print("=" * 60)
    print("🧠 PATH PREDICTOR — Entrenamiento del clasificador")
    print("   Generalista (A) vs Especialista (B)")
    print("=" * 60, "\n")

    # 1. Carga
    df = load_data(DATA_PATH)

    # 2. Preprocesado
    X_train, X_test, y_train, y_test, feature_names, encoder = preprocess(df)

    # 3. Entrenamiento — Logistic Regression
    print("🔧 Entrenando Logistic Regression...")
    lr = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    lr.fit(X_train, y_train)
    lr_metrics = evaluate(lr, "Logistic Regression", X_test, y_test)
    get_feature_importances(lr, "Logistic Regression", feature_names)

    # 4. Entrenamiento — Random Forest
    print("🔧 Entrenando Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=100, max_depth=5, random_state=RANDOM_STATE
    )
    rf.fit(X_train, y_train)
    rf_metrics = evaluate(rf, "Random Forest", X_test, y_test)
    get_feature_importances(rf, "Random Forest", feature_names)

    # 5. Selección del mejor modelo
    models = {
        "Logistic Regression": (lr, lr_metrics),
        "Random Forest": (rf, rf_metrics),
    }
    best_name = max(models, key=lambda k: models[k][1]["f1_B"])
    best_model, best_metrics = models[best_name]

    print("=" * 60)
    print(f"🏆 MEJOR MODELO: {best_name}")
    print(f"   F1-Score: {best_metrics['f1_B']:.4f}")
    print(f"   Accuracy: {best_metrics['accuracy']:.4f}")
    print("=" * 60, "\n")

    # 6. Exportar
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    model_artifact = {
        "model": best_model,
        "encoder": encoder,
        "feature_names": feature_names,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "target": TARGET,
        "classes": ["A", "B"],
    }
    joblib.dump(model_artifact, MODEL_OUTPUT)
    print(f"💾 Modelo exportado: {MODEL_OUTPUT}")
    print(f"   Tamaño: {MODEL_OUTPUT.stat().st_size / 1024:.1f} KB\n")

    # 7. Reporte JSON
    report = {
        "best_model": best_name,
        "test_size": TEST_SIZE,
        "n_samples_train": len(X_train),
        "n_samples_test": len(X_test),
        "metrics": {
            "logistic_regression": lr_metrics,
            "random_forest": rf_metrics,
        },
        "features": feature_names,
    }
    with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"📋 Reporte exportado: {REPORT_OUTPUT}\n")

    # 8. Quick demo
    print("=" * 60)
    print("🎯 DEMO — Predicción de ejemplo")
    print("=" * 60)
    demo_profiles = [
        {"experience_years": 1, "avg_current_level": 1.2, "avg_gap": 3.5,
         "n_competencies": 3, "dominant_domain": "Datos e IA",
         "objetivo_profesional": "Data Analyst"},
        {"experience_years": 10, "avg_current_level": 4.0, "avg_gap": 0.8,
         "n_competencies": 3, "dominant_domain": "Programación y Desarrollo",
         "objetivo_profesional": "ML Engineer"},
    ]
    for profile in demo_profiles:
        cat_vals = encoder.transform([[profile[c] for c in CATEGORICAL_FEATURES]])
        num_vals = np.array([[profile[c] for c in NUMERIC_FEATURES]])
        X_demo = np.hstack([num_vals, cat_vals])
        pred = best_model.predict(X_demo)[0]
        proba = best_model.predict_proba(X_demo)[0]
        label = "Generalista" if pred == "A" else "Especialista"
        print(f"   Perfil: {profile}")
        print(f"   ➜ Predicción: {pred} ({label}) — P(A)={proba[0]:.2f}, P(B)={proba[1]:.2f}\n")

    print("✅ Entrenamiento completado con éxito.")


if __name__ == "__main__":
    main()

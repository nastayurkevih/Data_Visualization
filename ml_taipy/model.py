"""Model loading, inference, and SHAP helpers for the Taipy prototype."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(__file__).resolve().parent / "models" / "incident_classifier.joblib"
FEATURE_COLUMNS = [
    "incident_type",
    "severity",
    "source_severity",
    "source_product",
    "resolution_team",
    "detection_name",
    "incident_count",
]


def load_model(model_path: Path = MODEL_PATH) -> Any:
    """Load a fitted sklearn-compatible estimator or pipeline."""
    if not model_path.is_file():
        raise FileNotFoundError(
            f"Model artifact not found: {model_path}. "
            "Train/export a compatible model to this path first."
        )

    model = joblib.load(model_path)
    if not callable(getattr(model, "predict", None)):
        raise TypeError(f"Loaded object at {model_path} has no predict() method.")
    return model


def inference_payload(model: Any, incidents: pd.DataFrame) -> pd.DataFrame:
    """Run prediction on the explicit feature contract used by this prototype."""
    missing = [column for column in FEATURE_COLUMNS if column not in incidents.columns]
    if missing:
        raise ValueError(f"Prepared data is missing model features: {missing}")

    features = incidents[FEATURE_COLUMNS].copy()
    predictions = model.predict(features)
    result = incidents[["incident_id", "verdict"]].copy()
    result["predicted_is_false_positive"] = predictions

    if callable(getattr(model, "predict_proba", None)):
        probabilities = model.predict_proba(features)
        classes = list(getattr(model, "classes_", []))
        if 1 in classes:
            result["probability_false_positive"] = probabilities[:, classes.index(1)]

    return result


def shap_importance(model: Any, incidents: pd.DataFrame) -> pd.DataFrame:
    """Return mean absolute SHAP importance for a bounded sample."""
    import shap

    missing = [column for column in FEATURE_COLUMNS if column not in incidents.columns]
    if missing:
        raise ValueError(f"Prepared data is missing model features: {missing}")

    features = incidents[FEATURE_COLUMNS].head(200).copy()
    if features.empty:
        raise ValueError("There are no rows available for SHAP analysis.")

    explanation = shap.Explainer(model, features)(features)
    values = explanation.values
    if values.ndim == 3:
        classes = list(getattr(model, "classes_", []))
        positive_index = classes.index(1) if 1 in classes else values.shape[2] - 1
        values = values[:, :, positive_index]
    if values.ndim != 2 or values.shape[1] != len(FEATURE_COLUMNS):
        raise ValueError(f"Unexpected SHAP output shape: {values.shape}")

    importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "mean_absolute_shap": abs(values).mean(axis=0),
        }
    )
    return importance.sort_values("mean_absolute_shap", ascending=False).head(12)

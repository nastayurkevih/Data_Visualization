"""Taipy asynchronous callbacks for model inference and SHAP analysis."""

from __future__ import annotations

from typing import Any

import pandas as pd
from taipy.gui import State, invoke_long_callback, notify

from model import inference_payload, load_model, shap_importance


def _predict(model_path: str, incidents: pd.DataFrame) -> pd.DataFrame:
    return inference_payload(load_model(model_path), incidents)


def _calculate_shap(model_path: str, incidents: pd.DataFrame) -> pd.DataFrame:
    return shap_importance(load_model(model_path), incidents)


def _on_async_result(
    state: State, success: bool, target: str, result: Any = None
) -> None:
    if not success:
        state.status = f"Операция {target} завершилась ошибкой; проверьте лог приложения."
        notify(state, "error", state.status)
        return

    setattr(state, target, result)
    state.status = "Операция завершена."
    notify(state, "success", state.status)


def run_inference(state: State) -> None:
    state.status = "Модель выполняет инференс..."
    notify(state, "info", state.status)
    invoke_long_callback(
        state,
        _predict,
        user_function_args=[state.model_path, state.incident_table],
        user_status_function=_on_async_result,
        user_status_function_args=["predictions"],
    )


def run_shap(state: State) -> None:
    state.status = "Вычисляются SHAP-значения (не более 200 строк)..."
    notify(state, "info", state.status)
    invoke_long_callback(
        state,
        _calculate_shap,
        user_function_args=[state.model_path, state.incident_table],
        user_status_function=_on_async_result,
        user_status_function_args=["shap_table"],
    )

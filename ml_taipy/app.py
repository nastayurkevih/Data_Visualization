"""Minimal Taipy GUI for SOC alert triage model prototyping."""

from pathlib import Path

import pandas as pd
import plotly.express as px
from taipy.gui import Gui

from callbacks import run_inference, run_shap
from model import MODEL_PATH, ROOT

DATA_PATH = ROOT / "data" / "processed" / "tableau_incidents.csv"

if not DATA_PATH.is_file():
    raise FileNotFoundError(
        f"Prepared data not found: {DATA_PATH}. Run `python data/prepare_data.py` first."
    )

incident_table = pd.read_csv(DATA_PATH, sep=";", encoding="utf-8-sig")
required_columns = {"incident_id", "verdict"}
missing_columns = required_columns.difference(incident_table.columns)
if missing_columns:
    raise ValueError(f"Prepared CSV is missing columns: {sorted(missing_columns)}")

verdict_counts = (
    incident_table["verdict"]
    .fillna("Не указан")
    .value_counts()
    .rename_axis("Вердикт")
    .reset_index(name="Количество")
)
verdict_figure = px.bar(
    verdict_counts,
    x="Вердикт",
    y="Количество",
    title="Карточки по вердиктам",
    labels={"Вердикт": "Итоговый вердикт", "Количество": "Число карточек"},
)

model_path = str(MODEL_PATH)
status = (
    "Данные загружены. Для инференса положите совместимую модель "
    "в ml_taipy/models/incident_classifier.joblib."
)
predictions = pd.DataFrame()
shap_table = pd.DataFrame(columns=["feature", "mean_absolute_shap"])

page = """
# SOC alert triage — ML prototype

Используется плоский подготовленный набор. «Не указан» — это неизвестная
разметка, а не подтвержденная безопасная активность.

<|{status}|text|>

## Карточки инцидентов
<|{incident_table}|table|page_size=10|>

## Распределение вердиктов
<|{verdict_figure}|chart|>

## ML-инференс
<|Запустить инференс|button|on_action=run_inference|>
<|{predictions}|table|page_size=10|>

## Интерпретация SHAP
<|Рассчитать SHAP|button|on_action=run_shap|>
<|{shap_table}|chart|type=bar|x=feature|y=mean_absolute_shap|title=Средний модуль SHAP-вклада|>
<|{shap_table}|table|page_size=12|>
"""

if __name__ == "__main__":
    Gui(page).run(title="SOC Alert Triage", port=5000)

"""Create a Tableau dashboard mockup and field-placement guide from the BI CSV."""

from __future__ import annotations

import csv
import html
import math
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "processed" / "tableau_incidents.csv"
OUTPUT_FILE = Path(__file__).resolve().parent / "tableau_dashboard_guide.svg"

COLORS = [
    "#2F6B8A",
    "#D97941",
    "#4C956C",
    "#8A6FB0",
    "#C64D5B",
    "#8B8D54",
    "#4C9A9A",
    "#C69C35",
]
BACKGROUND = "#F2F5F8"
INK = "#1D2A35"
MUTED = "#5B6B78"
WHITE = "#FFFFFF"
GRID = "#E1E7EC"


def clean(value: str | None, fallback: str = "Не указано") -> str:
    value = (value or "").strip()
    return value if value else fallback


def fmt(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def text(x: float, y: float, value: str, size: int = 14, color: str = INK, weight: int = 400, anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{esc(value)}</text>'
    )


def rect(x: float, y: float, width: float, height: float, fill: str, radius: int = 0, stroke: str = "none") -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
        f'rx="{radius}" fill="{fill}" stroke="{stroke}"/>'
    )


def donut_slice(cx: float, cy: float, outer: float, inner: float, start: float, end: float, fill: str) -> str:
    large = 1 if end - start > math.pi else 0
    x1, y1 = cx + outer * math.cos(start), cy + outer * math.sin(start)
    x2, y2 = cx + outer * math.cos(end), cy + outer * math.sin(end)
    ix2, iy2 = cx + inner * math.cos(end), cy + inner * math.sin(end)
    ix1, iy1 = cx + inner * math.cos(start), cy + inner * math.sin(start)
    return (
        f'<path d="M {x1:.2f} {y1:.2f} A {outer} {outer} 0 {large} 1 {x2:.2f} {y2:.2f} '
        f'L {ix2:.2f} {iy2:.2f} A {inner} {inner} 0 {large} 0 {ix1:.2f} {iy1:.2f} Z" '
        f'fill="{fill}" stroke="{WHITE}" stroke-width="2"/>'
    )


def load_data() -> tuple[int, dict[str, int], dict[str, dict[str, int]], dict[str, dict[str, int]], dict[str, dict[str, int]]]:
    if not DATA_FILE.is_file():
        raise FileNotFoundError(
            f"Data file not found: {DATA_FILE}. Run `python data/prepare_data.py --full` first."
        )

    all_ids: set[str] = set()
    verdict_ids: dict[str, set[str]] = defaultdict(set)
    monthly_ids: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    source_ids: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    severity_ids: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        required = {"incident_id", "incident_date", "verdict", "source_product", "severity"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

        for row in reader:
            incident_id = (row.get("incident_id") or "").strip()
            if not incident_id:
                continue
            verdict = clean(row.get("verdict"))
            source = clean(row.get("source_product"))
            severity = clean(row.get("severity"))
            try:
                incident_month = date.fromisoformat(row["incident_date"][:10]).strftime("%Y-%m")
            except (ValueError, TypeError):
                incident_month = "Дата не указана"

            all_ids.add(incident_id)
            verdict_ids[verdict].add(incident_id)
            monthly_ids[incident_month][verdict].add(incident_id)
            source_ids[source][verdict].add(incident_id)
            severity_ids[severity][verdict].add(incident_id)

    to_counts = lambda values: {key: {v: len(ids) for v, ids in nested.items()} for key, nested in values.items()}
    return (
        len(all_ids),
        {verdict: len(ids) for verdict, ids in verdict_ids.items()},
        to_counts(monthly_ids),
        to_counts(source_ids),
        to_counts(severity_ids),
    )


def draw_legend(items: list[tuple[str, int]], x: float, y: float, max_width: float, color_map: dict[str, str]) -> str:
    parts = []
    columns = min(2, len(items))
    rows_per_column = math.ceil(len(items) / max(1, columns))
    col_width = max_width / max(1, columns)
    for index, (label, value) in enumerate(items):
        column = index // rows_per_column
        row = index % rows_per_column
        px = x + column * col_width
        py = y + row * 26
        parts.append(rect(px, py - 11, 12, 12, color_map[label], 3))
        parts.append(text(px + 20, py, f"{label}: {fmt(value)}", 12, MUTED))
    return "".join(parts)


def panel_shell(x: float, y: float, title: str, subtitle: str, number: str) -> str:
    return (
        rect(x, y, 670, 490, WHITE, 18, GRID)
        + text(x + 24, y + 39, f"{number}  {title}", 21, INK, 700)
        + text(x + 24, y + 66, subtitle, 12, MUTED)
        + f'<line x1="{x+24}" y1="{y+82}" x2="{x+646}" y2="{y+82}" stroke="{GRID}"/>'
    )


def build_svg(total, verdicts, monthly, sources, severities) -> str:
    verdict_order = sorted(verdicts, key=lambda key: (-verdicts[key], key.casefold()))
    color_map = {label: COLORS[i % len(COLORS)] for i, label in enumerate(verdict_order)}
    width, height = 1420, 1220
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{BACKGROUND}"/>',
        '<style>text{font-family:Arial,"DejaVu Sans",sans-serif} .mono{font-family:Consolas,monospace}</style>',
        text(40, 46, "SOC | Макет первого Tableau-дашборда", 28, INK, 700),
        text(40, 75, f"Карточек в данных: {fmt(total)}  •  Все визуализации используют COUNTD(incident_id)", 14, MUTED),
        text(1380, 47, "BI • описываем данные, не предсказываем класс", 12, MUTED, 400, "end"),
    ]

    # 1. Verdict distribution donut.
    x, y = 40, 105
    out.append(panel_shell(x, y, "Карточки по вердиктам", "Кольцевая диаграмма • сравнение долей итоговых решений", "1"))
    cx, cy, outer, inner = x + 220, y + 262, 142, 78
    start = -math.pi / 2
    for verdict in verdict_order:
        end = start + (verdicts[verdict] / max(1, total)) * (2 * math.pi)
        out.append(donut_slice(cx, cy, outer, inner, start, end, color_map[verdict]))
        start = end
    out.append(text(cx, cy - 7, fmt(total), 24, INK, 700, "middle"))
    out.append(text(cx, cy + 17, "карточек", 12, MUTED, 400, "middle"))
    out.append(draw_legend([(v, verdicts[v]) for v in verdict_order], x + 405, y + 150, 220, color_map))
    out.append(text(x + 24, y + 430, "ПОЛЯ И ПОЛОЖЕНИЕ В TABLEAU", 10, MUTED, 700))
    out.append(text(x + 24, y + 453, "verdict → Цвет; incident_id → Угол (COUNTD) и Метка (COUNTD)", 12, INK))
    out.append(text(x + 24, y + 475, "«Не указан» — неизвестный исход, не угроза и не безопасная карточка.", 11, MUTED))

    # 2. Monthly trend by verdict.
    x, y = 710, 105
    out.append(panel_shell(x, y, "Динамика по месяцам", "Линейный график • число карточек по дате и вердикту", "2"))
    chart_x, chart_y, chart_w, chart_h = x + 62, y + 110, 565, 175
    month_keys = sorted((k for k in monthly if k != "Дата не указана"))
    series_max = max((monthly[m].get(v, 0) for m in month_keys for v in verdict_order), default=1)
    for tick in range(5):
        val = series_max * tick / 4
        py = chart_y + chart_h - chart_h * tick / 4
        out.append(f'<line x1="{chart_x}" y1="{py}" x2="{chart_x+chart_w}" y2="{py}" stroke="{GRID}"/>')
        out.append(text(chart_x - 10, py + 4, fmt(round(val)), 10, MUTED, 400, "end"))
    for idx, month in enumerate(month_keys):
        if len(month_keys) > 1:
            px = chart_x + chart_w * idx / (len(month_keys) - 1)
        else:
            px = chart_x + chart_w / 2
        if len(month_keys) <= 14 or idx % max(1, len(month_keys) // 10) == 0:
            out.append(text(px, chart_y + chart_h + 20, month, 10, MUTED, 400, "middle"))
    for verdict in verdict_order:
        points = []
        for idx, month in enumerate(month_keys):
            px = chart_x + chart_w * idx / max(1, len(month_keys) - 1)
            py = chart_y + chart_h - chart_h * monthly[month].get(verdict, 0) / max(1, series_max)
            points.append((px, py))
        if points:
            path = " ".join(("M" if i == 0 else "L") + f" {px:.1f} {py:.1f}" for i, (px, py) in enumerate(points))
            out.append(f'<path d="{path}" fill="none" stroke="{color_map[verdict]}" stroke-width="2.4"/>')
    out.append(draw_legend([(v, verdicts[v]) for v in verdict_order], chart_x, y + 320, 560, color_map))
    out.append(text(x + 24, y + 430, "ПОЛЯ И ПОЛОЖЕНИЕ В TABLEAU", 10, MUTED, 700))
    out.append(text(x + 24, y + 453, "incident_date → Столбцы (Месяц); incident_id → Строки (COUNTD)", 12, INK))
    out.append(text(x + 24, y + 475, "verdict → Цвет; тип метки → Линия. Месяц должен быть упорядочен по времени.", 11, MUTED))

    # 3. Stacked horizontal bars by SIEM source.
    x, y = 40, 600
    out.append(panel_shell(x, y, "Карточки по источникам", "Горизонтальные составные столбцы • источники и вердикты", "3"))
    source_order = sorted(sources, key=lambda key: (-sum(sources[key].values()), key.casefold()))
    max_source = max((sum(sources[key].values()) for key in source_order), default=1)
    chart_x, chart_y, chart_w, row_h = x + 175, y + 105, 440, min(31, 220 / max(1, len(source_order)))
    shown_sources = source_order[:7]
    for idx, source in enumerate(shown_sources):
        py = chart_y + idx * row_h
        amount = sum(sources[source].values())
        out.append(text(chart_x - 10, py + 15, source[:22], 11, MUTED, 400, "end"))
        px = chart_x
        for verdict in verdict_order:
            count = sources[source].get(verdict, 0)
            if count:
                bar_w = chart_w * count / max_source
                out.append(rect(px, py, bar_w, 20, color_map[verdict], 3))
                px += bar_w
        out.append(text(min(px + 8, x + 645), py + 15, fmt(amount), 10, MUTED))
    out.append(draw_legend([(v, verdicts[v]) for v in verdict_order], x + 190, y + 320, 430, color_map))
    out.append(text(x + 24, y + 430, "ПОЛЯ И ПОЛОЖЕНИЕ В TABLEAU", 10, MUTED, 700))
    out.append(text(x + 24, y + 453, "source_product → Строки; incident_id → Столбцы (COUNTD)", 12, INK))
    out.append(text(x + 24, y + 475, "verdict → Цвет; сортировка источников по убыванию числа карточек.", 11, MUTED))

    # 4. Stacked bars by severity.
    x, y = 710, 600
    out.append(panel_shell(x, y, "Карточки по критичности", "Столбцы • сравнение критичности с разбивкой по вердиктам", "4"))
    severity_order = sorted(severities, key=lambda key: (-sum(severities[key].values()), key.casefold()))
    max_severity = max((sum(severities[key].values()) for key in severity_order), default=1)
    chart_x, chart_y, chart_w, row_h = x + 160, y + 105, 440, min(31, 220 / max(1, len(severity_order)))
    shown_severity = severity_order[:7]
    for idx, severity in enumerate(shown_severity):
        py = chart_y + idx * row_h
        amount = sum(severities[severity].values())
        out.append(text(chart_x - 10, py + 15, severity[:19], 11, MUTED, 400, "end"))
        px = chart_x
        for verdict in verdict_order:
            count = severities[severity].get(verdict, 0)
            if count:
                bar_w = chart_w * count / max_severity
                out.append(rect(px, py, bar_w, 20, color_map[verdict], 3))
                px += bar_w
        out.append(text(min(px + 8, x + 645), py + 15, fmt(amount), 10, MUTED))
    out.append(draw_legend([(v, verdicts[v]) for v in verdict_order], x + 170, y + 320, 450, color_map))
    out.append(text(x + 24, y + 430, "ПОЛЯ И ПОЛОЖЕНИЕ В TABLEAU", 10, MUTED, 700))
    out.append(text(x + 24, y + 453, "severity → Строки; incident_id → Столбцы (COUNTD)", 12, INK))
    out.append(text(x + 24, y + 475, "verdict → Цвет. Это распределение карточек, не доказательство угрозы.", 11, MUTED))

    out.extend([
        text(40, 1155, "Важно: incident_count — исходные инциденты внутри карточки; для количества карточек используйте только COUNTD(incident_id).", 13, INK, 700),
        text(40, 1182, "ML-поле is_false_positive не используется в этих BI-графиках. «Не указан» показывается как отдельный неизвестный исход.", 12, MUTED),
        "</svg>",
    ])
    return "\n".join(out)


def main() -> None:
    total, verdicts, monthly, sources, severities = load_data()
    svg = build_svg(total, verdicts, monthly, sources, severities)
    OUTPUT_FILE.write_text(svg, encoding="utf-8")
    print(f"Created: {OUTPUT_FILE}")
    print(f"Distinct cards in the guide: {fmt(total)}")
    print(f"Verdicts: {len(verdicts)}; months: {len(monthly)}; sources: {len(sources)}; severities: {len(severities)}")


if __name__ == "__main__":
    main()

"""Prepare incident data for shared EDA, Tableau, and Taipy prototyping."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "Dataset"
OUTPUT_DIR = ROOT / "data" / "processed"
SAMPLE_FILE = "iavd_1000_incidents_raw_target.parquet"
FULL_FILE = "iavd_incidents_raw_target.parquet"
CALENDAR_FILE = "calendar.parquet"
CSV_SEPARATOR = ";"

VERDICT_COLUMN = "Вердикт"
FALSE_POSITIVE_LABEL = "False Positive"
KNOWN_NON_FP_LABELS = {
    "Решён",
    "Дубликат",
    "Закрыт из родительской атаки",
}

MEANINGS = {
    "EntityId": "Уникальный идентификатор карточки инцидента в SOAR.",
    "Создан": "Время создания карточки инцидента.",
    "Дата": "Календарная дата карточки; ключ для справочника календаря.",
    "Вердикт": "Итоговый вердикт аналитика; исходная категориальная цель.",
    "verdict": "Числовой код вердикта; дубликат целевой колонки «Вердикт».",
    "Дата закрытия (факт)": "Фактическое время закрытия карточки.",
    "Дата закрытия": "Плановое или системное время закрытия карточки.",
    "Время первого события": "Время первого события, включенного в инцидент.",
    "Время последнего события": "Время последнего события, включенного в инцидент.",
    "Дата создания в источнике": "Время создания карточки в исходной SIEM.",
    "Дата изменения в источнике": "Время последнего изменения карточки в исходной SIEM.",
    "Дата взятия в работу": "Время, когда аналитик начал обработку.",
    "Время решения": "Числовая величина аномального масштаба; смысл и единицы не подтверждены.",
    "Время Решения": "Поле, сохраненное как дата-время; требует проверки единиц.",
    "Период взятия в работу": "Задержка до начала обработки; единицы требуют сверки.",
    "Количество инцидентов": "Число исходных инцидентов, объединенных в карточку.",
    "Критичность": "Критичность карточки во внутренней системе.",
    "Критичность инцидента в источнике": "Критичность, присвоенная исходной SIEM.",
    "Тип инцидента": "Классификация инцидента во внутреннем справочнике.",
    "Типы угроз": "Типы вредоносных объектов или угроз.",
    "Источник инцидента": "Продукт, создавший карточку (например, SIEM или ручной ввод).",
    "Группа устранения": "Линия или группа поддержки, обрабатывающая инцидент.",
    "Фаза реагирования": "Текущая фаза обработки инцидента.",
    "Пиктограмма IRP": "Категория карточки в IRP.",
    "Наименование": "Название правила или детекции.",
    "Правило корреляции SIEM": "Полное имя правила корреляции в SIEM.",
    "Теги": "Метки обнаружения; значения могут быть объединены разделителем.",
    "Значение Атаки (группировка)": "Агрегированные значения родительской атаки.",
    "Значение Инцидента (группировка)": "Агрегированные объекты/учетные записи; пары могут содержать роль.",
    "Алерт": "Текст одного или нескольких исходных алертов.",
    "Команда": "Одна или несколько команд, связанных с событием.",
    "Описание инцидента": "Текстовое описание карточки.",
    "Решение": "Текст заключения аналитика; может напрямую раскрывать целевой вердикт.",
    "Ответственный": "ФИО аналитика, обрабатывавшего карточку.",
    "Полное имя": "ФИО пользователя, связанного с событием.",
    "suser": "Учетная запись источника события.",
    "duser": "Учетная запись цели события.",
    "Hostname Цели": "Имя целевого хоста.",
    "Hostname атакующего": "Имя хоста-источника или атакующего.",
    "processName": "Имя процесса, связанного с событием.",
    "processParentName": "Имя родительского процесса.",
    "processPath": "Путь исполняемого файла процесса.",
    "processParentPath": "Путь исполняемого файла родительского процесса.",
    "CMDLINE": "Командная строка процесса.",
    "commandName": "Имя утилиты или команды.",
    "filePath": "Путь к файлу, связанному с событием.",
    "Файловый ресурс": "Файл или иной ресурс, связанный с событием.",
    "categoryHigh": "Верхний уровень классификации категории SIEM.",
    "categoryMain": "Основная категория SIEM.",
    "categoryLow": "Нижний уровень классификации категории SIEM.",
    "object": "Тип объекта события (например, процесс или ресурс).",
    "object.name": "Имя объекта события.",
    "objectLinks": "Пары учетная запись/утилита, связанные с объектом.",
    "objectValue": "Пары учетная запись/объект, связанные с событием.",
    "Привилегии аккаунта": "Уровень прав учетной записи, связанной с событием.",
    "Эскалировался на L2?": "Признак эскалации карточки на вторую линию.",
    "SLA по устранению Атаки": "Норматив времени на устранение; единицы не подтверждены.",
    "SLA по взятию в работу Атаки": "Норматив времени до начала обработки; единицы не подтверждены.",
    "Попытка эксплуатации": "Поле о наличии попытки эксплуатации уязвимости.",
    "Список вредоносных команд": "Список команд, помеченных как вредоносные.",
    "Прошлый ответственный": "Предыдущий аналитик, если карточку переназначали.",
    "Рекомендации по плейбуку": "Рекомендации для обработки по плейбуку.",
    "Вендор из сием": "Вендор исходного продукта или источника события.",
    "Организация": "Организация, к которой относится карточка.",
    "Ответсвенный по РП": "Числовой идентификатор ответственного по РП.",
    "Принятые меры": "Текст мер, предпринятых аналитиком.",
    "Статус инцидента из SIEM": "Статус связанной карточки в исходной SIEM.",
    "Значение Инцидента (группировка по типу)": "Группировка значений события по типам объектов.",
    "Имя файла-IRP": "Имя файла, сохраненное в карточке IRP.",
    "Принятые меры из SIEM": "Меры, записанные исходной SIEM.",
    "Конвейер SIEM": "Конвейер/маршрут обработки события в SIEM.",
    "Инцидент в Источнике": "Ссылка или список ссылок на исходные карточки SIEM.",
    "Комментарий": "Заметки аналитика по ходу разбора.",
    "Ошибки": "Технические ошибки, сохраненные в карточке.",
    "Ссылка в NAD (actual)": "Ссылка на объект в PT Network Attack Discovery.",
    "src": "Адрес или объект источника сетевого события.",
    "dst": "Адрес или объект назначения сетевого события.",
    "Начало паузы": "Время начала паузы обработки карточки.",
    "Конец паузы": "Время окончания паузы обработки карточки.",
    "Период взятия в работу": "Расчетная задержка до взятия в работу; единицы не подтверждены.",
    "задержка перед автоназначением": "Числовое время до автоназначения; похоже на timestamp, требует проверки.",
    "binary_target": "Бинарная цель: 1 — явный FP, 0 — явный не-FP, пропуск — неизвестный вердикт.",
    "Год": "Календарный год из справочника дат.",
    "Номер недели": "Номер календарной недели.",
    "Месяц": "Номер календарного месяца.",
    "МесяцГод": "Дата начала календарного месяца.",
    "День": "Номер дня месяца.",
    "ДеньМесяц": "Дата календарного дня.",
    "ДеньМесяц_Недели": "Дата, используемая для календарной группировки по неделям.",
    "Дата_ДеньНедели": "Календарная дата для группировки по дням недели.",
    "Квартал": "Номер календарного квартала.",
    "НеделяГод": "Дата начала недели по календарной системе.",
    "Неделя Год": "Дата начала недели в альтернативном поле календаря.",
    "День недели": "Номер дня недели.",
    "_180 дней": "Флаг попадания даты в 180-дневное окно.",
    "_90 дней": "Флаг попадания даты в 90-дневное окно.",
    "_30 дней": "Флаг попадания даты в 30-дневное окно.",
    "_7 дней": "Флаг попадания даты в 7-дневное окно.",
    "Тип дня": "Код типа календарного дня.",
    "Год ГИС": "Год в календарной системе ГИС.",
    "Номер недели ГИС": "Номер недели в календарной системе ГИС.",
    "НеделяГод ГИС": "Дата начала недели в календарной системе ГИС.",
}

TABLEAU_COLUMNS = {
    "EntityId": "incident_id",
    "Создан": "created_at_utc",
    "Дата": "incident_date",
    "Вердикт": "verdict",
    "binary_target": "is_false_positive",
    "Тип инцидента": "incident_type",
    "Критичность": "severity",
    "Критичность инцидента в источнике": "source_severity",
    "Источник инцидента": "source_product",
    "Группа устранения": "resolution_team",
    "Фаза реагирования": "response_phase",
    "Наименование": "detection_name",
    "Количество инцидентов": "incident_count",
    "Дата закрытия (факт)": "closed_at_utc",
    "SLA по устранению Атаки": "sla_resolution_raw",
    "SLA по взятию в работу Атаки": "sla_acknowledgement_raw",
    "Год": "calendar_year",
    "Месяц": "calendar_month",
    "Квартал": "calendar_quarter",
    "Номер недели": "calendar_week",
    "День недели": "calendar_weekday",
    "Тип дня": "calendar_day_type",
}


def _normalise_values(frame: pd.DataFrame) -> pd.DataFrame:
    """Trim text, retain unknowns as missing, and standardise date columns."""
    frame = frame.copy()

    for column in frame.select_dtypes(include=["object", "string"]).columns:
        values = frame[column].astype("string").str.strip()
        frame[column] = values.mask(values.eq(""))

        present = frame[column].dropna()
        if not present.empty and present.str.casefold().isin({"true", "false"}).all():
            frame[column] = frame[column].str.casefold().map(
                {"true": True, "false": False}
            ).astype("boolean")

    if "Дата" in frame.columns:
        frame["Дата"] = pd.to_datetime(frame["Дата"], errors="coerce", utc=True)

    for column in frame.columns:
        if pd.api.types.is_datetime64_any_dtype(frame[column]):
            frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True)

    return frame


def _add_binary_target(frame: pd.DataFrame) -> pd.DataFrame:
    """Label only explicit decisions; unresolved verdicts remain missing."""
    result = frame.copy()
    verdict = result[VERDICT_COLUMN].astype("string").str.strip()
    binary = pd.Series(pd.NA, index=result.index, dtype="Int8")
    binary.loc[verdict.eq(FALSE_POSITIVE_LABEL)] = 1
    binary.loc[verdict.isin(KNOWN_NON_FP_LABELS)] = 0
    result["binary_target"] = binary
    return result


def _join_calendar(frame: pd.DataFrame, source_path: Path) -> pd.DataFrame:
    """Add calendar attributes through the many-incidents-to-one-date relation."""
    calendar_path = source_path.parent / CALENDAR_FILE
    if not calendar_path.exists() or "Дата" not in frame.columns:
        return frame

    calendar = pd.read_parquet(calendar_path)
    if "Дата" not in calendar.columns:
        raise ValueError(f"{calendar_path} does not contain a 'Дата' join key.")

    frame = frame.copy()
    calendar = calendar.copy()
    frame["_calendar_date"] = pd.to_datetime(frame["Дата"], errors="coerce", utc=True).dt.normalize()
    calendar["_calendar_date"] = pd.to_datetime(
        calendar["Дата"], errors="coerce", utc=True
    ).dt.normalize()

    duplicate_dates = calendar["_calendar_date"].duplicated(keep=False)
    if duplicate_dates.any():
        raise ValueError(
            f"Calendar has {int(duplicate_dates.sum())} rows with duplicate dates; "
            "a many-to-one join would duplicate incidents."
        )

    attributes = [
        column
        for column in calendar.columns
        if column not in {"Дата", "_calendar_date"}
        and column not in frame.columns
    ]
    frame = frame.merge(
        calendar[["_calendar_date", *attributes]],
        on="_calendar_date",
        how="left",
        validate="many_to_one",
    )
    return frame.drop(columns="_calendar_date")


def _profile(frame: pd.DataFrame) -> pd.DataFrame:
    def meaning(column: str) -> str:
        if column in MEANINGS:
            return MEANINGS[column]
        if str(frame[column].dtype) == "boolean":
            return "Булевый флаг workflow; пропуск не означает False."
        return "Поле инцидента; подробная расшифровка — в словаре полей."

    return pd.DataFrame(
        {
            "column": frame.columns,
            "pandas_dtype": [str(frame[column].dtype) for column in frame.columns],
            "missing_count": [int(frame[column].isna().sum()) for column in frame.columns],
            "missing_percent": [
                round(float(frame[column].isna().mean() * 100), 2)
                for column in frame.columns
            ],
            "unique_non_null": [
                int(frame[column].nunique(dropna=True)) for column in frame.columns
            ],
            "meaning": [meaning(column) for column in frame.columns],
        }
    )


def _tableau_export(frame: pd.DataFrame) -> pd.DataFrame:
    available = {
        source: alias
        for source, alias in TABLEAU_COLUMNS.items()
        if source in frame.columns or source == "binary_target"
    }
    export = pd.DataFrame(index=frame.index)
    for source, alias in available.items():
        export[alias] = frame[source]

    if "created_at_utc" in export.columns:
        export["created_date"] = pd.to_datetime(
            export["created_at_utc"], errors="coerce", utc=True
        ).dt.strftime("%Y-%m-%d")
    if "incident_date" in export.columns:
        export["incident_date"] = pd.to_datetime(
            export["incident_date"], errors="coerce", utc=True
        ).dt.strftime("%Y-%m-%d")
    return export


def prepare_data(source_path: Path, output_dir: Path) -> dict[str, Path]:
    """Clean the selected Parquet file and create shared BI/ML-friendly exports."""
    if not source_path.is_file():
        raise FileNotFoundError(f"Input Parquet file not found: {source_path}")

    raw = pd.read_parquet(source_path)
    if VERDICT_COLUMN not in raw.columns:
        raise ValueError(f"Input file does not contain target column {VERDICT_COLUMN!r}.")

    clean = _normalise_values(raw)
    exact_duplicates = int(clean.duplicated().sum())
    if exact_duplicates:
        clean = clean.drop_duplicates().reset_index(drop=True)

    clean = _add_binary_target(clean)
    clean = _join_calendar(clean, source_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "clean": output_dir / "incidents_clean.parquet",
        "clean_csv": output_dir / "incidents_clean.csv",
        "flat": output_dir / "tableau_incidents.csv",
        "daily": output_dir / "tableau_verdict_daily.csv",
        "source": output_dir / "tableau_source_summary.csv",
        "profile": output_dir / "column_profile.csv",
    }

    clean.to_parquet(paths["clean"], index=False)
    # A semicolon delimiter opens as separate columns in common Russian Excel setups.
    clean.to_csv(
        paths["clean_csv"],
        index=False,
        encoding="utf-8-sig",
        sep=CSV_SEPARATOR,
    )
    flat = _tableau_export(clean)
    flat.to_csv(
        paths["flat"],
        index=False,
        encoding="utf-8-sig",
        sep=CSV_SEPARATOR,
    )

    daily = (
        flat.groupby(["incident_date", "verdict"], dropna=False)["incident_id"]
        .nunique()
        .rename("card_count")
        .reset_index()
        .sort_values(["incident_date", "verdict"], na_position="last")
    )
    daily.to_csv(
        paths["daily"],
        index=False,
        encoding="utf-8-sig",
        sep=CSV_SEPARATOR,
    )

    if "source_product" in flat.columns:
        by_source = (
            flat.groupby(["source_product", "verdict"], dropna=False)["incident_id"]
            .nunique()
            .rename("card_count")
            .reset_index()
            .sort_values(["source_product", "verdict"], na_position="last")
        )
    else:
        by_source = pd.DataFrame(columns=["source_product", "verdict", "card_count"])
    by_source.to_csv(
        paths["source"],
        index=False,
        encoding="utf-8-sig",
        sep=CSV_SEPARATOR,
    )

    _profile(clean).to_csv(
        paths["profile"],
        index=False,
        encoding="utf-8-sig",
        sep=CSV_SEPARATOR,
    )

    print(f"Input: {source_path.name} ({len(raw):,} rows, {len(raw.columns)} columns)")
    print(f"Exact duplicate rows removed: {exact_duplicates}")
    print("Verdicts:")
    print(clean[VERDICT_COLUMN].value_counts(dropna=False).to_string())
    print(f"Explicit binary labels: {int(clean['binary_target'].notna().sum()):,}")
    print(f"Rows in clean CSV: {len(clean):,}")
    print(f"Distinct incident cards in flat export: {flat['incident_id'].nunique():,}")
    for name, path in paths.items():
        print(f"{name}: {path}")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Use the full ~174 MB Parquet dataset instead of the 1,000-row sample.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional explicit input Parquet path; overrides --full.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for processed Parquet/CSV files.",
    )
    args = parser.parse_args()

    default_file = FULL_FILE if args.full else SAMPLE_FILE
    source_path = args.input or SOURCE_DIR / default_file
    prepare_data(source_path.resolve(), args.output_dir.resolve())


if __name__ == "__main__":
    main()

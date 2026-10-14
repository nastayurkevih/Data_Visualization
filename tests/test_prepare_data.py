import tempfile
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

from data.prepare_data import (
    CSV_SEPARATOR,
    FALSE_POSITIVE_LABEL,
    KNOWN_NON_FP_LABELS,
    VERDICT_COLUMN,
    _add_binary_target,
    _join_calendar,
    _tableau_export,
    prepare_data,
)


class PrepareDataTests(unittest.TestCase):
    def test_binary_target_keeps_unresolved_verdicts_unknown(self) -> None:
        labels = [FALSE_POSITIVE_LABEL, *KNOWN_NON_FP_LABELS, "Не указан"]
        frame = _add_binary_target(pd.DataFrame({VERDICT_COLUMN: labels}))

        self.assertEqual(frame["binary_target"].iloc[0], 1)
        self.assertEqual(frame["binary_target"].iloc[1:4].tolist(), [0, 0, 0])
        self.assertTrue(pd.isna(frame["binary_target"].iloc[4]))

    def test_tableau_export_is_flat_and_omits_unverified_duration(self) -> None:
        frame = pd.DataFrame(
            {
                "EntityId": [1],
                "Создан": pd.to_datetime(["2025-01-02T03:04:00Z"]),
                "Дата": pd.to_datetime(["2025-01-02T00:00:00Z"]),
                VERDICT_COLUMN: ["Не указан"],
                "binary_target": pd.Series([pd.NA], dtype="Int8"),
                "Время решения": [1.7e12],
            }
        )

        export = _tableau_export(frame)

        self.assertEqual(export.loc[0, "created_date"], "2025-01-02")
        self.assertIn("is_false_positive", export.columns)
        self.assertNotIn("resolution_seconds", export.columns)
        self.assertEqual(len(export), 1)

    def test_calendar_join_preserves_rows_and_adds_date_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "sample.parquet"
            source_path.touch()
            pd.DataFrame(
                {
                    "Дата": [date(2025, 1, 2)],
                    "Год": [2025],
                    "Месяц": [1],
                }
            ).to_parquet(Path(temporary_directory) / "calendar.parquet")
            incidents = pd.DataFrame(
                {
                    "EntityId": [1, 2],
                    "Дата": pd.to_datetime(
                        ["2025-01-02T00:00:00Z", "2025-01-02T00:00:00Z"]
                    ),
                }
            )

            joined = _join_calendar(incidents, source_path)

        self.assertEqual(len(joined), 2)
        self.assertEqual(joined["Год"].tolist(), [2025, 2025])

    def test_prepare_data_writes_semicolon_csvs_with_distinct_card_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            input_path = root / "sample.parquet"
            pd.DataFrame(
                {
                    "EntityId": [10, 11, 12],
                    "Создан": pd.to_datetime(
                        [
                            "2025-01-02T03:04:00Z",
                            "2025-01-02T04:04:00Z",
                            "2025-01-03T04:04:00Z",
                        ]
                    ),
                    "Дата": pd.to_datetime(
                        [
                            "2025-01-02T00:00:00Z",
                            "2025-01-02T00:00:00Z",
                            "2025-01-03T00:00:00Z",
                        ]
                    ),
                    VERDICT_COLUMN: [
                        FALSE_POSITIVE_LABEL,
                        FALSE_POSITIVE_LABEL,
                        "Не указан",
                    ],
                    "Источник инцидента": ["SIEM A", "SIEM A", "SIEM B"],
                    "Описание инцидента": ["Текст 1", "Текст 2", "Текст 3"],
                }
            ).to_parquet(input_path)
            output_dir = root / "processed"

            outputs = prepare_data(input_path, output_dir)

            for key in ["clean_csv", "flat", "daily", "source", "profile"]:
                self.assertTrue(outputs[key].is_file())

            clean_csv = pd.read_csv(
                outputs["clean_csv"], sep=CSV_SEPARATOR, encoding="utf-8-sig"
            )
            flat_csv = pd.read_csv(
                outputs["flat"], sep=CSV_SEPARATOR, encoding="utf-8-sig"
            )
            daily_csv = pd.read_csv(
                outputs["daily"], sep=CSV_SEPARATOR, encoding="utf-8-sig"
            )
            source_csv = pd.read_csv(
                outputs["source"], sep=CSV_SEPARATOR, encoding="utf-8-sig"
            )

        self.assertEqual(len(clean_csv), 3)
        self.assertIn("Описание инцидента", clean_csv.columns)
        self.assertEqual(len(flat_csv), 3)
        self.assertEqual(int(daily_csv.loc[0, "card_count"]), 2)
        self.assertEqual(
            set(source_csv.columns), {"source_product", "verdict", "card_count"}
        )


if __name__ == "__main__":
    unittest.main()

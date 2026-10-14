"""Print a compact EDA summary from the prepared Parquet dataset."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "incidents_clean.parquet"


def main() -> None:
    if not DATA_PATH.is_file():
        raise FileNotFoundError(
            f"{DATA_PATH} is missing. Run `python data/prepare_data.py` first."
        )

    frame = pd.read_parquet(DATA_PATH)
    print(f"Rows: {len(frame):,}; columns: {len(frame.columns)}")
    print("\nTarget:")
    print(frame["Вердикт"].value_counts(dropna=False).to_string())
    print("\nMost-missing fields:")
    missing = frame.isna().mean().mul(100).sort_values(ascending=False)
    print(missing.head(15).round(1).to_string())
    print("\nBinary labels (unknown decisions excluded):")
    print(frame["binary_target"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()

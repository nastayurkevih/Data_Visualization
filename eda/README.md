# Общий EDA

Для быстрой сводки запускайте:

```powershell
python data/prepare_data.py
python eda/quick_eda.py
```

Профиль типов, пропусков и уникальных значений всех полей записывается в
`data/processed/column_profile.csv`. Для чтения полного набора используйте
`python data/prepare_data.py --full`; полный файл не загружается по умолчанию.
В профиле явно сохранен pandas-тип после очистки; календарные признаки
отмечены как добавленные из `calendar.parquet`.

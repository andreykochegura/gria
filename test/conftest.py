import pandas as pd
import pytest


@pytest.fixture
def valid_excel(tmp_path):
    path = tmp_path / "test.xlsx"

    sheets = {
        "Варианты": pd.DataFrame([
            ["SOD2", "rs4880", "6", "A/C"],
            ["GPX1", "rs1050450", "3", "G/T"],
        ], columns=["Ген", "rsID", "Хромосома", "Аллели"]),

        "Признаки": pd.DataFrame([
            ["F001", "Тестовый признак", "rs4880, rs1050450", 2],
        ], columns=["Код признака", "Название", "Варианты", "Минимум входов"]),

        "Вклады": pd.DataFrame([
            ["F001", "SOD2", "rs4880", "A/A", "0.20"],
            ["F001", "GPX1", "rs1050450", "G/G", "0.60"],
        ], columns=["Код признака", "Ген", "rsID", "Генотип", "Вклад"]),

        "Пороги": pd.DataFrame([
            ["F001", "-1", "low", "Низкий уровень"],
            ["F001", "0", "medium", "Средний уровень"],
            ["F001", "0.3", "high", "Высокий уровень"],
        ], columns=["Код признака", "Нижняя граница", "Уровень", "Заключение"]),

        "Образцы": pd.DataFrame([
            ["S01", "male", "A/A", "G/G"],
        ], columns=["Образец", "Пол", "SOD2 rs4880", "GPX1 rs1050450"]),
    }

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)

    return path


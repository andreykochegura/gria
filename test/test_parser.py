import pytest
from gria import parser


def test_parse_valid_excel(valid_excel):
    data = parser.parse(valid_excel)

    assert set(data.keys()) == {
        "variants",
        "features",
        "contributions",
        "thresholds",
        "samples",
    }
    assert len(data["variants"]) == 2
    assert len(data["features"]) == 1
    assert len(data["contributions"]) == 2
    assert len(data["thresholds"]) == 3
    assert len(data["samples"]) == 1


def test_parse_file_not_found(tmp_path):
    path = tmp_path / "missing.xlsx"

    with pytest.raises(FileNotFoundError):
        parser.parse(path)


def test_parse_wrong_extension(tmp_path):
    path = tmp_path / "test.csv"
    path.touch()

    with pytest.raises(parser.ParseError, match="Wrong file extension"):
        parser.parse(path)


def test_parse_missing_sheet(valid_excel, tmp_path):
    import pandas as pd

    path = tmp_path / "invalid.xlsx"

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"Ген": ["SOD2"]}).to_excel(
            writer, sheet_name="Варианты", index=False
        )

    with pytest.raises(parser.ParseError, match="Sheet is missing"):
        parser.parse(path)


def test_parse_missing_column(tmp_path):
    import pandas as pd

    path = tmp_path / "invalid.xlsx"

    sheets = {
        "Варианты": pd.DataFrame(columns=["Ген", "rsID", "Хромосома"]),
        "Признаки": pd.DataFrame(columns=["Код признака", "Название", "Варианты", "Минимум входов"]),
        "Вклады": pd.DataFrame(columns=["Код признака", "Ген", "rsID", "Генотип", "Вклад"]),
        "Пороги": pd.DataFrame(columns=["Код признака", "Нижняя граница", "Уровень", "Заключение"]),
        "Образцы": pd.DataFrame(columns=["Образец", "Пол", "SOD2 rs4880"]),
    }

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)

    with pytest.raises(parser.ParseError, match="Column"):
        parser.parse(path)

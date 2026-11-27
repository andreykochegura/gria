from fractions import Fraction

import pandas as pd
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


def parse_modified(valid_excel, tmp_path, mutate):
    sheets = pd.read_excel(valid_excel, sheet_name=None, dtype=object)
    mutate(sheets)
    path = tmp_path / "modified.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    return parser.parse(path)


def test_parse_rejects_contribution_out_of_range(valid_excel, tmp_path, capsys):
    def mutate(sheets):
        sheets["Вклады"]["Вклад"] = ["5", "0.60"]

    data = parse_modified(valid_excel, tmp_path, mutate)

    assert len(data["contributions"]) == 1
    assert "greater than" in capsys.readouterr().err


def test_parse_rejects_contribution_with_excess_precision(valid_excel, tmp_path, capsys):
    def mutate(sheets):
        sheets["Вклады"]["Вклад"] = ["0.123", "0.60"]

    data = parse_modified(valid_excel, tmp_path, mutate)

    assert len(data["contributions"]) == 1
    assert "decimal places" in capsys.readouterr().err


def test_parse_accepts_float_cells_exactly(valid_excel, tmp_path, capsys):
    def mutate(sheets):
        sheets["Вклады"]["Вклад"] = [0.2, 0.6]

    data = parse_modified(valid_excel, tmp_path, mutate)

    assert list(data["contributions"]["contribution"]) == [Fraction(1, 5), Fraction(3, 5)]
    assert capsys.readouterr().err == ""


def test_parse_normalizes_case_and_allele_order(valid_excel, tmp_path):
    def mutate(sheets):
        sheets["Образцы"]["Пол"] = ["Male"]
        sheets["Вклады"].loc[len(sheets["Вклады"])] = ["F001", "SOD2", "rs4880", "c/a", "0.10"]

    data = parse_modified(valid_excel, tmp_path, mutate)

    assert data["samples"].loc[0, "sex"] == "male"
    assert "A/C" in set(data["contributions"]["genotype"])


def test_parse_drops_sample_with_unknown_sex(valid_excel, tmp_path, capsys):
    def mutate(sheets):
        sheets["Образцы"]["Пол"] = ["other"]

    data = parse_modified(valid_excel, tmp_path, mutate)

    assert len(data["samples"]) == 0
    assert "Failed to validate" in capsys.readouterr().err


def test_parse_drops_row_instead_of_crashing_on_unparsable_number(valid_excel, tmp_path, capsys):
    def mutate(sheets):
        sheets["Вклады"]["Вклад"] = ["abc", "0.60"]
        sheets["Признаки"]["Минимум входов"] = [0]

    data = parse_modified(valid_excel, tmp_path, mutate)

    assert len(data["contributions"]) == 1
    assert len(data["features"]) == 0
    assert "dropped" in capsys.readouterr().err


def test_parse_fails_on_invalid_threshold(valid_excel, tmp_path):
    def mutate(sheets):
        sheets["Пороги"]["Уровень"] = ["low", "medium", "extreme"]

    with pytest.raises(parser.ParseError, match="Пороги"):
        parse_modified(valid_excel, tmp_path, mutate)


def test_parse_rejects_malformed_variant_list(valid_excel, tmp_path):
    def mutate(sheets):
        sheets["Признаки"]["Варианты"] = ["rs4880; rs1050450"]

    data = parse_modified(valid_excel, tmp_path, mutate)

    assert len(data["features"]) == 0


def test_parse_keeps_blank_genotype_as_missing(valid_excel, tmp_path):
    def mutate(sheets):
        sheets["Образцы"] = pd.DataFrame(
            [["S01", "male", "A/A", "G/G"], ["S02", "female", "A/A", None]],
            columns=["Образец", "Пол", "SOD2 rs4880", "GPX1 rs1050450"],
        )

    data = parse_modified(valid_excel, tmp_path, mutate)

    assert pd.isna(data["samples"].loc[1, "GPX1 rs1050450"])


def test_parse_keeps_check_marker_in_genotype(valid_excel, tmp_path, capsys):
    def mutate(sheets):
        sheets["Образцы"]["GPX1 rs1050450"] = ["ПРОВЕРИТЬ"]

    data = parse_modified(valid_excel, tmp_path, mutate)

    assert data["samples"].loc[0, "GPX1 rs1050450"] == "ПРОВЕРИТЬ"
    assert capsys.readouterr().err == ""

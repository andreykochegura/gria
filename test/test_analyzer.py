import pandas as pd
from gria import parser, analyzer


def test_analyze_calculates_score(valid_excel, capsys):
    data = parser.parse(valid_excel)

    analyzer.analyze(data)

    output = capsys.readouterr().out

    assert "S01" in output
    assert "Тестовый признак" in output
    assert "Балл: 0.4" in output
    assert "Уровень: high" in output
    assert "Высокий уровень" in output


def test_analyze_insufficient_data(valid_excel, capsys):
    
    data = parser.parse(valid_excel)
    data["samples"].loc[0, "GPX1 rs1050450"] = pd.NA
    analyzer.analyze(data)
    output = capsys.readouterr().out
    assert analyzer.INSUFFICIENT_DATA in output


def test_analyze_wrong_genotype(valid_excel, capsys):
    data = parser.parse(valid_excel)
    data["samples"].loc[0, "SOD2 rs4880"] = "B/B"
    analyzer.analyze(data)
    output = capsys.readouterr()
    
    assert analyzer.INSUFFICIENT_DATA in output.out
    assert "Wrong genotype" in output.err


def test_analyze_missing_variant(valid_excel, capsys):
    data = parser.parse(valid_excel)
    data["features"].loc[0, "variants"] = "rs4880, rs999999"
    analyzer.analyze(data)
    output = capsys.readouterr()

    assert analyzer.INSUFFICIENT_DATA in output.out
    assert "Variant not found" in output.err


def test_analyze_palindromic_variant(valid_excel, capsys):
    data = parser.parse(valid_excel)

    data["variants"].loc[data["variants"]["rsid"] == "rs4880", "alleles"] = "A/T"
    analyzer.analyze(data)
    output = capsys.readouterr()

    assert analyzer.INSUFFICIENT_DATA in output.out
    assert "Palindromic allele" in output.err

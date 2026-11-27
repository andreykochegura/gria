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
    assert "Variant not found" not in output.err
    assert "Not enough inputs" in output.err


def test_analyze_palindromic_variant_is_skipped_when_enough_inputs(valid_excel, capsys):
    data = parser.parse(valid_excel)

    data["variants"].loc[data["variants"]["rsid"] == "rs4880", "alleles"] = "A/T"
    data["features"].loc[0, "min_inputs"] = 1
    analyzer.analyze(data)
    output = capsys.readouterr()

    assert "Palindromic allele" in output.err
    assert "Variant not found" not in output.err
    assert "Балл: 0.6" in output.out
    assert "Уровень: high" in output.out


def test_analyze_empty_genotype_is_excluded_and_reported(valid_excel, capsys):
    data = parser.parse(valid_excel)
    data["features"].loc[0, "min_inputs"] = 1
    data["samples"].loc[0, "GPX1 rs1050450"] = pd.NA
    analyzer.analyze(data)
    output = capsys.readouterr()

    assert "Empty genotype" in output.err
    assert "Балл: 0.2" in output.out


def test_analyze_missing_genotype_column_is_reported(valid_excel, capsys):
    data = parser.parse(valid_excel)
    data["features"].loc[0, "min_inputs"] = 1
    data["samples"] = data["samples"].drop(columns=["GPX1 rs1050450"])
    analyzer.analyze(data)
    output = capsys.readouterr()

    assert "Empty genotype" in output.err
    assert "Балл: 0.2" in output.out


def test_analyze_wrong_genotypes_are_excluded_not_fatal(valid_excel, capsys):
    for bad in ("B/B", "A/", "A/G/A", "5"):
        data = parser.parse(valid_excel)
        data["features"].loc[0, "min_inputs"] = 1
        data["samples"].loc[0, "SOD2 rs4880"] = bad
        analyzer.analyze(data)
        output = capsys.readouterr()

        assert "Wrong genotype" in output.err, bad
        assert "Балл: 0.6" in output.out, bad


def test_analyze_wrong_ploidy_is_excluded_not_fatal(valid_excel, capsys):
    data = parser.parse(valid_excel)
    data["features"].loc[0, "min_inputs"] = 1
    data["variants"].loc[data["variants"]["rsid"] == "rs4880", "chromosome"] = "X"
    data["samples"].loc[0, "SOD2 rs4880"] = "A/A"
    analyzer.analyze(data)
    output = capsys.readouterr()

    assert "Wrong ploidy" in output.err
    assert "Балл: 0.6" in output.out


def test_analyze_check_marker_makes_feature_insufficient(valid_excel, capsys):
    for marker in ("ПРОВЕРИТЬ", "проверить"):
        data = parser.parse(valid_excel)
        data["features"].loc[0, "min_inputs"] = 1
        data["samples"].loc[0, "GPX1 rs1050450"] = marker
        analyzer.analyze(data)
        output = capsys.readouterr()

        assert analyzer.INSUFFICIENT_DATA in output.out
        assert "Балл" not in output.out
        assert any(line.startswith("WARNING:") and "ПРОВЕРИТЬ" in line for line in output.err.splitlines())
        assert "ERROR" not in output.err

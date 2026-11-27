import sys
from gria import main


def test_main_pipeline(monkeypatch, tmp_path):
    path = tmp_path / "test.xlsx"
    path.touch()
    parsed_data = {"test": "data"}
    calls = {"parse": None, "analyze": None}

    def mock_parse(arg):
        calls["parse"] = arg
        return parsed_data

    def mock_analyze(data):
        calls["analyze"] = data

    monkeypatch.setattr(main.parser, "parse", mock_parse)
    monkeypatch.setattr(main.analyzer, "analyze", mock_analyze)
    monkeypatch.setattr(sys, "argv", ["main.py", str(path)])

    main.main()

    assert calls["parse"] == str(path)
    assert calls["analyze"] is parsed_data

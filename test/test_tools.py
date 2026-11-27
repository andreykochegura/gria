from fractions import Fraction
import pandas as pd
from gria.analyzer import get_threshold
from gria.tools import roundup


def test_roundup_is_exact_and_rounds_away_from_zero():
    assert roundup(Fraction(3, 10)) == Fraction(3, 10)
    assert roundup(Fraction(1, 3)) == Fraction(34, 100)
    assert roundup(Fraction(-1, 3)) == Fraction(-34, 100)
    assert roundup(Fraction(0)) == 0


def test_get_threshold_score_equal_to_lower_bound():
    thresholds = pd.DataFrame({
        "lower_bound": [Fraction(-1), Fraction(0), Fraction(3, 10)],
        "level": ["low", "medium", "high"],
        "conclusion": ["a", "b", "c"],
    })

    assert get_threshold(Fraction(3, 10), thresholds)["level"] == "high"
    assert get_threshold(Fraction(29, 100), thresholds)["level"] == "medium"
    assert get_threshold(Fraction(-1), thresholds)["level"] == "low"
    assert get_threshold(Fraction(-101, 100), thresholds) is None
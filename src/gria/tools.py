import sys
import pandas as pd
from math import ceil
from fractions import Fraction


def roundup(x: Fraction, digits: int = 2) -> float:
    k = 10 ** digits
    r = Fraction(ceil(abs(x) * k), k)
    return float(-r if x < 0 else r)


Dataset = dict[str, pd.DataFrame]


def info(msg: str):
    print(msg, file=sys.stdout)


def warning(msg: str):
    print(f"WARNING: {msg}", file=sys.stderr)


def error(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)

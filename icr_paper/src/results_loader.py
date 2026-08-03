"""Access to the generated analysis results and number formatting helpers.

Every number that appears in the manuscript passes through this module, so
the manuscript builders contain no result literals.
"""

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_JSON = RESULTS_DIR / "results.json"


def load_results() -> dict:
    if not RESULTS_JSON.exists():
        raise SystemExit(
            f"{RESULTS_JSON} not found. Run: python run_analysis.py"
        )
    with open(RESULTS_JSON) as fh:
        return json.load(fh)


def load_table(name: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS_DIR / name)


# ---------------------------------------------------------------- formatting
def num(value, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def pct(value, digits: int = 1) -> str:
    """Format a percentage already expressed on the 0-100 scale."""
    return f"{float(value):.{digits}f}%"


def rate_pct(value, digits: int = 1) -> str:
    """Format a proportion (0-1) as a percentage."""
    return f"{100 * float(value):.{digits}f}%"


def signed(value, digits: int = 3) -> str:
    return f"{float(value):+.{digits}f}"


def ci(lower, upper, digits: int = 3) -> str:
    return f"[{float(lower):.{digits}f}, {float(upper):.{digits}f}]"


def pval(value) -> str:
    v = float(value)
    if v < 0.001:
        return "P < 0.001"
    return f"P = {v:.3f}"


def pval_plain(value) -> str:
    v = float(value)
    return "< 0.001" if v < 0.001 else f"{v:.3f}"


def mean_mcse(stat: dict, digits: int = 3, percent: bool = False) -> str:
    """Format a Monte Carlo summary as ``mean (MCSE)``."""
    if percent:
        return f"{stat['mean']:.{digits}f}% (MCSE {stat['mcse']:.{digits}f})"
    return f"{stat['mean']:.{digits}f} (MCSE {stat['mcse']:.{digits}f})"


def thousands(value) -> str:
    return f"{int(value):,}"

"""Loading of the real-world Table 1 datasets from data/ CSV files.

All numbers used by the analysis and by the manuscript originate here or in
the IST individual patient data downloaded by scripts/download_ist.sh; no
result value is written as a literal in any analysis or manuscript script.
"""

import math
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _optional(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return float(value)


def load_dataset(tag: str) -> dict:
    """Load one real-world dataset (``statin`` or ``glucose_control``).

    Returns a dict in the shape consumed by
    :func:`icr_paper.src.real_world_analysis.analyze_example_dataset`.
    """
    studies = pd.read_csv(DATA_DIR / f"{tag}_studies.csv")
    table1 = pd.read_csv(DATA_DIR / f"{tag}_table1.csv")
    sources = pd.read_csv(DATA_DIR / "study_sources.csv")
    sources = sources[sources["dataset"] == tag]

    out = []
    for _, s in studies.iterrows():
        rows = table1[table1["study"] == s["study"]]
        variables = []
        endpoints = []
        for _, v in rows.iterrows():
            entry = {"variable": v["variable"], "type": v["type"]}
            if v["type"] == "continuous":
                entry.update(
                    mean_I=_optional(v["mean_I"]), std_I=_optional(v["sd_I"]),
                    mean_C=_optional(v["mean_C"]), std_C=_optional(v["sd_C"]),
                )
            else:
                entry.update(
                    prop_I=_optional(v["prop_I"]), prop_C=_optional(v["prop_C"])
                )
            variables.append(entry)
            if int(v["is_endpoint"]) == 1:
                endpoints.append(v["variable"])
        out.append(
            {
                "name": s["study"],
                "n_i": int(s["n_intervention"]),
                "n_c": int(s["n_control"]),
                "table1": variables,
                "endpoints": endpoints,
                "effect_size": float(s["effect_size_logrr"]),
                "effect_var": float(s["effect_var"]),
            }
        )

    return {
        "tag": tag,
        "description": DESCRIPTIONS[tag],
        "studies": out,
        "sources": sources.to_dict(orient="records"),
    }


DESCRIPTIONS = {
    "statin": (
        "Statin therapy for cardiovascular prevention. Landmark RCTs with a "
        "consistent all-cause mortality benefit and similar baseline variable sets."
    ),
    "glucose_control": (
        "Intensive glucose control in type 2 diabetes. Trials whose all-cause "
        "mortality results diverged and whose baseline variable sets differ in size."
    ),
}


def load_all_datasets() -> dict:
    return {tag: load_dataset(tag) for tag in ("statin", "glucose_control")}

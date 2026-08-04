"""
Real-world data analysis for ICR research.

Baseline (Table 1) summary statistics and trial-level effect sizes are read
from ``data/*_table1.csv`` and ``data/*_studies.csv``; their provenance is
recorded in ``data/study_sources.csv``. Nothing is hard-coded here.
"""

import numpy as np
import pandas as pd
from .data_io import load_all_datasets
from .icr_calculator import compute_icr_v
from .meta_analysis import (
    dersimonian_laird_meta,
    sequential_meta_analysis,
)
from scipy import stats


def analyze_example_dataset(dataset: dict) -> dict:
    """Analyze a predefined real-world dataset.

    Parameters
    ----------
    dataset : dict
        A dataset as returned by :func:`icr_paper.src.data_io.load_dataset`.

    Returns
    -------
    dict with ICR values, meta-analysis results, and correlation analysis.
    """
    study_results = []

    for study in dataset["studies"]:
        icr_result = compute_icr_v(
            table1_data=study["table1"],
            endpoints=study["endpoints"],
            n_i=study["n_i"],
            n_c=study["n_c"],
        )

        study_results.append({
            "study": study["name"],
            "n_total": study["n_i"] + study["n_c"],
            "n_variables": icr_result["n_variables_used"],
            "n_endpoints": icr_result["n_endpoint_variables"],
            "icr_std": icr_result["icr_std"],
            "icr_raw": icr_result["icr_raw"],
            "icr_raw_intervention": icr_result["icr_raw_intervention"],
            "icr_raw_control": icr_result["icr_raw_control"],
            "group_icr_difference": icr_result["group_icr_difference"],
            "effect_size": study["effect_size"],
            "effect_var": study["effect_var"],
            "unusable": icr_result["unusable_variables"],
        })

    df_studies = pd.DataFrame(study_results)

    # Meta-analysis
    effects = df_studies["effect_size"].values
    variances = df_studies["effect_var"].values
    icr_values = df_studies["icr_std"].values

    meta = dersimonian_laird_meta(effects, variances)

    # Sequential meta-analysis
    seq = sequential_meta_analysis(effects, variances, icr_values)

    # Correlation: ICR vs effect size
    if len(effects) > 2:
        corr_icr_effect, p_icr_effect = stats.pearsonr(icr_values, effects)
    else:
        corr_icr_effect, p_icr_effect = np.nan, np.nan

    # ICR discrepancy
    icrd = np.max(icr_values) - np.min(icr_values)
    icr_cv = np.std(icr_values, ddof=1) / np.mean(icr_values) if np.mean(icr_values) > 0 else 0

    return {
        "description": dataset["description"],
        "study_results": df_studies,
        "meta_analysis": meta,
        "sequential_meta": seq,
        "icr_statistics": {
            "icr_mean": np.mean(icr_values),
            "icr_sd": np.std(icr_values, ddof=1),
            "icr_cv": icr_cv,
            "icrd": icrd,
            "icr_values": icr_values,
        },
        "correlation": {
            "icr_vs_effect_r": corr_icr_effect,
            "icr_vs_effect_p": p_icr_effect,
        },
    }


def run_real_world_analyses() -> dict:
    """Run all real-world data analyses from the CSV inputs in data/."""
    return {
        tag: analyze_example_dataset(dataset)
        for tag, dataset in load_all_datasets().items()
    }

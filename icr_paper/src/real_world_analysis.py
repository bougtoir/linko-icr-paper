"""
Real-world data analysis for ICR research.

Provides tools to:
1. Extract Table1 data from published RCTs and compute ICR_v
2. Analyze known meta-analyses where heterogeneity changed over time
3. Test association between ICR discrepancy and heterogeneity
"""

import numpy as np
import pandas as pd
from typing import Optional
from .icr_calculator import compute_icr_v
from .meta_analysis import (
    dersimonian_laird_meta,
    sequential_meta_analysis,
    compute_heterogeneity_metrics,
)
from scipy import stats


# ============================================================================
# Example real-world dataset: Statin therapy meta-analyses
# Early RCTs (e.g., 4S, WOSCOPS, CARE, LIPID, AFCAPS) showed consistent
# benefit. Later large meta-analyses including diverse populations showed
# increased heterogeneity in some subgroups.
# ============================================================================

STATIN_EXAMPLE = {
    "description": (
        "Statin therapy for cardiovascular prevention. "
        "Early landmark RCTs showed consistent benefit (low I²). "
        "Subsequent inclusion of diverse populations and endpoints "
        "introduced heterogeneity."
    ),
    "studies": [
        {
            "name": "4S (1994)",
            "n_i": 2221, "n_c": 2223,
            "table1": [
                {"variable": "Age", "type": "continuous",
                 "mean_I": 58.6, "std_I": 7.7, "mean_C": 58.5, "std_C": 7.9},
                {"variable": "Male", "type": "binary",
                 "prop_I": 0.81, "prop_C": 0.82},
                {"variable": "Total_Cholesterol", "type": "continuous",
                 "mean_I": 261.0, "std_I": 30.0, "mean_C": 260.0, "std_C": 30.0},
                {"variable": "LDL_Cholesterol", "type": "continuous",
                 "mean_I": 188.0, "std_I": 26.0, "mean_C": 189.0, "std_C": 26.0},
                {"variable": "HDL_Cholesterol", "type": "continuous",
                 "mean_I": 46.0, "std_I": 12.0, "mean_C": 46.0, "std_C": 12.0},
                {"variable": "Triglycerides", "type": "continuous",
                 "mean_I": 132.0, "std_I": 60.0, "mean_C": 131.0, "std_C": 58.0},
                {"variable": "Smoking", "type": "binary",
                 "prop_I": 0.26, "prop_C": 0.25},
                {"variable": "Hypertension", "type": "binary",
                 "prop_I": 0.26, "prop_C": 0.26},
                {"variable": "Diabetes", "type": "binary",
                 "prop_I": 0.05, "prop_C": 0.04},
                {"variable": "Mortality", "type": "binary",
                 "prop_I": 0.082, "prop_C": 0.119},
            ],
            "endpoints": ["Mortality"],
            "effect_size": -0.37,  # log-RR for all-cause mortality
            "effect_var": 0.012,
        },
        {
            "name": "WOSCOPS (1995)",
            "n_i": 3302, "n_c": 3293,
            "table1": [
                {"variable": "Age", "type": "continuous",
                 "mean_I": 55.3, "std_I": 5.5, "mean_C": 55.1, "std_C": 5.5},
                {"variable": "Male", "type": "binary",
                 "prop_I": 1.0, "prop_C": 1.0},
                {"variable": "Total_Cholesterol", "type": "continuous",
                 "mean_I": 272.0, "std_I": 23.0, "mean_C": 272.0, "std_C": 23.0},
                {"variable": "LDL_Cholesterol", "type": "continuous",
                 "mean_I": 192.0, "std_I": 17.0, "mean_C": 192.0, "std_C": 17.0},
                {"variable": "HDL_Cholesterol", "type": "continuous",
                 "mean_I": 44.0, "std_I": 11.0, "mean_C": 44.0, "std_C": 11.0},
                {"variable": "Triglycerides", "type": "continuous",
                 "mean_I": 164.0, "std_I": 68.0, "mean_C": 162.0, "std_C": 66.0},
                {"variable": "Smoking", "type": "binary",
                 "prop_I": 0.44, "prop_C": 0.44},
                {"variable": "Hypertension", "type": "binary",
                 "prop_I": 0.16, "prop_C": 0.15},
                {"variable": "Diabetes", "type": "binary",
                 "prop_I": 0.01, "prop_C": 0.01},
                {"variable": "Mortality", "type": "binary",
                 "prop_I": 0.032, "prop_C": 0.041},
            ],
            "endpoints": ["Mortality"],
            "effect_size": -0.25,
            "effect_var": 0.035,
        },
        {
            "name": "CARE (1996)",
            "n_i": 2081, "n_c": 2078,
            "table1": [
                {"variable": "Age", "type": "continuous",
                 "mean_I": 59.0, "std_I": 9.0, "mean_C": 59.0, "std_C": 9.0},
                {"variable": "Male", "type": "binary",
                 "prop_I": 0.86, "prop_C": 0.86},
                {"variable": "Total_Cholesterol", "type": "continuous",
                 "mean_I": 209.0, "std_I": 17.0, "mean_C": 209.0, "std_C": 17.0},
                {"variable": "LDL_Cholesterol", "type": "continuous",
                 "mean_I": 139.0, "std_I": 15.0, "mean_C": 139.0, "std_C": 15.0},
                {"variable": "HDL_Cholesterol", "type": "continuous",
                 "mean_I": 39.0, "std_I": 9.0, "mean_C": 39.0, "std_C": 9.0},
                {"variable": "Triglycerides", "type": "continuous",
                 "mean_I": 155.0, "std_I": 55.0, "mean_C": 156.0, "std_C": 57.0},
                {"variable": "Smoking", "type": "binary",
                 "prop_I": 0.21, "prop_C": 0.21},
                {"variable": "Hypertension", "type": "binary",
                 "prop_I": 0.43, "prop_C": 0.42},
                {"variable": "Diabetes", "type": "binary",
                 "prop_I": 0.14, "prop_C": 0.15},
                {"variable": "BMI", "type": "continuous",
                 "mean_I": 28.0, "std_I": 4.3, "mean_C": 28.0, "std_C": 4.2},
                {"variable": "Mortality", "type": "binary",
                 "prop_I": 0.085, "prop_C": 0.094},
            ],
            "endpoints": ["Mortality"],
            "effect_size": -0.10,
            "effect_var": 0.020,
        },
        {
            "name": "LIPID (1998)",
            "n_i": 4512, "n_c": 4502,
            "table1": [
                {"variable": "Age", "type": "continuous",
                 "mean_I": 62.0, "std_I": 8.3, "mean_C": 62.0, "std_C": 8.2},
                {"variable": "Male", "type": "binary",
                 "prop_I": 0.83, "prop_C": 0.83},
                {"variable": "Total_Cholesterol", "type": "continuous",
                 "mean_I": 218.0, "std_I": 20.0, "mean_C": 218.0, "std_C": 20.0},
                {"variable": "LDL_Cholesterol", "type": "continuous",
                 "mean_I": 150.0, "std_I": 16.0, "mean_C": 150.0, "std_C": 16.0},
                {"variable": "HDL_Cholesterol", "type": "continuous",
                 "mean_I": 36.0, "std_I": 9.0, "mean_C": 36.0, "std_C": 9.0},
                {"variable": "Triglycerides", "type": "continuous",
                 "mean_I": 139.0, "std_I": 56.0, "mean_C": 142.0, "std_C": 59.0},
                {"variable": "Smoking", "type": "binary",
                 "prop_I": 0.10, "prop_C": 0.09},
                {"variable": "Hypertension", "type": "binary",
                 "prop_I": 0.42, "prop_C": 0.41},
                {"variable": "Diabetes", "type": "binary",
                 "prop_I": 0.09, "prop_C": 0.09},
                {"variable": "Mortality", "type": "binary",
                 "prop_I": 0.110, "prop_C": 0.142},
            ],
            "endpoints": ["Mortality"],
            "effect_size": -0.25,
            "effect_var": 0.008,
        },
        {
            "name": "AFCAPS/TexCAPS (1998)",
            "n_i": 3304, "n_c": 3301,
            "table1": [
                {"variable": "Age", "type": "continuous",
                 "mean_I": 58.0, "std_I": 7.0, "mean_C": 58.0, "std_C": 7.0},
                {"variable": "Male", "type": "binary",
                 "prop_I": 0.85, "prop_C": 0.85},
                {"variable": "Total_Cholesterol", "type": "continuous",
                 "mean_I": 221.0, "std_I": 21.0, "mean_C": 221.0, "std_C": 21.0},
                {"variable": "LDL_Cholesterol", "type": "continuous",
                 "mean_I": 150.0, "std_I": 17.0, "mean_C": 150.0, "std_C": 17.0},
                {"variable": "HDL_Cholesterol", "type": "continuous",
                 "mean_I": 36.0, "std_I": 6.0, "mean_C": 36.0, "std_C": 5.0},
                {"variable": "Triglycerides", "type": "continuous",
                 "mean_I": 158.0, "std_I": 70.0, "mean_C": 156.0, "std_C": 68.0},
                {"variable": "Smoking", "type": "binary",
                 "prop_I": 0.12, "prop_C": 0.13},
                {"variable": "Hypertension", "type": "binary",
                 "prop_I": 0.22, "prop_C": 0.22},
                {"variable": "Diabetes", "type": "binary",
                 "prop_I": 0.00, "prop_C": 0.00},
                {"variable": "Mortality", "type": "binary",
                 "prop_I": 0.025, "prop_C": 0.028},
            ],
            "endpoints": ["Mortality"],
            "effect_size": -0.11,
            "effect_var": 0.060,
        },
    ],
}


# ============================================================================
# Example: Intensive glucose control meta-analyses
# UKPDS showed benefit; ACCORD, ADVANCE, VADT showed mixed results with
# heterogeneity. Different studies measured different numbers of variables.
# ============================================================================

GLUCOSE_CONTROL_EXAMPLE = {
    "description": (
        "Intensive glucose control in type 2 diabetes. "
        "UKPDS showed mortality benefit, but ACCORD/ADVANCE/VADT "
        "increased heterogeneity with diverse patient populations "
        "and variable definitions."
    ),
    "studies": [
        {
            "name": "UKPDS 33 (1998)",
            "n_i": 2729, "n_c": 1138,
            "table1": [
                {"variable": "Age", "type": "continuous",
                 "mean_I": 53.3, "std_I": 8.6, "mean_C": 53.4, "std_C": 8.7},
                {"variable": "Male", "type": "binary",
                 "prop_I": 0.61, "prop_C": 0.58},
                {"variable": "BMI", "type": "continuous",
                 "mean_I": 27.5, "std_I": 5.1, "mean_C": 27.2, "std_C": 5.0},
                {"variable": "HbA1c", "type": "continuous",
                 "mean_I": 7.0, "std_I": 1.3, "mean_C": 7.0, "std_C": 1.3},
                {"variable": "FPG", "type": "continuous",
                 "mean_I": 8.0, "std_I": 2.6, "mean_C": 8.0, "std_C": 2.5},
                {"variable": "Smoking", "type": "binary",
                 "prop_I": 0.33, "prop_C": 0.30},
                {"variable": "Hypertension", "type": "binary",
                 "prop_I": 0.39, "prop_C": 0.40},
                {"variable": "Mortality", "type": "binary",
                 "prop_I": 0.178, "prop_C": 0.189},
            ],
            "endpoints": ["Mortality"],
            "effect_size": -0.06,
            "effect_var": 0.008,
        },
        {
            "name": "ACCORD (2008)",
            "n_i": 5128, "n_c": 5123,
            "table1": [
                {"variable": "Age", "type": "continuous",
                 "mean_I": 62.2, "std_I": 6.8, "mean_C": 62.2, "std_C": 6.8},
                {"variable": "Male", "type": "binary",
                 "prop_I": 0.61, "prop_C": 0.62},
                {"variable": "BMI", "type": "continuous",
                 "mean_I": 32.2, "std_I": 5.5, "mean_C": 32.2, "std_C": 5.5},
                {"variable": "HbA1c", "type": "continuous",
                 "mean_I": 8.1, "std_I": 1.0, "mean_C": 8.1, "std_C": 1.0},
                {"variable": "Duration_DM", "type": "continuous",
                 "mean_I": 10.0, "std_I": 7.0, "mean_C": 10.0, "std_C": 7.0},
                {"variable": "CVD_history", "type": "binary",
                 "prop_I": 0.35, "prop_C": 0.35},
                {"variable": "Smoking", "type": "binary",
                 "prop_I": 0.14, "prop_C": 0.14},
                {"variable": "Hypertension", "type": "binary",
                 "prop_I": 0.86, "prop_C": 0.86},
                {"variable": "Statin_use", "type": "binary",
                 "prop_I": 0.62, "prop_C": 0.62},
                {"variable": "Aspirin_use", "type": "binary",
                 "prop_I": 0.55, "prop_C": 0.54},
                {"variable": "SBP", "type": "continuous",
                 "mean_I": 136.0, "std_I": 17.0, "mean_C": 136.0, "std_C": 17.0},
                {"variable": "Creatinine", "type": "continuous",
                 "mean_I": 0.9, "std_I": 0.2, "mean_C": 0.9, "std_C": 0.2},
                {"variable": "Mortality", "type": "binary",
                 "prop_I": 0.050, "prop_C": 0.040},
            ],
            "endpoints": ["Mortality"],
            "effect_size": 0.22,  # HARM: increased mortality
            "effect_var": 0.018,
        },
        {
            "name": "ADVANCE (2008)",
            "n_i": 5571, "n_c": 5569,
            "table1": [
                {"variable": "Age", "type": "continuous",
                 "mean_I": 66.0, "std_I": 6.4, "mean_C": 66.0, "std_C": 6.3},
                {"variable": "Male", "type": "binary",
                 "prop_I": 0.57, "prop_C": 0.58},
                {"variable": "BMI", "type": "continuous",
                 "mean_I": 28.3, "std_I": 5.2, "mean_C": 28.3, "std_C": 5.1},
                {"variable": "HbA1c", "type": "continuous",
                 "mean_I": 7.5, "std_I": 1.6, "mean_C": 7.5, "std_C": 1.5},
                {"variable": "Duration_DM", "type": "continuous",
                 "mean_I": 7.9, "std_I": 6.3, "mean_C": 8.0, "std_C": 6.3},
                {"variable": "CVD_history", "type": "binary",
                 "prop_I": 0.32, "prop_C": 0.32},
                {"variable": "Smoking", "type": "binary",
                 "prop_I": 0.13, "prop_C": 0.14},
                {"variable": "Hypertension", "type": "binary",
                 "prop_I": 0.91, "prop_C": 0.91},
                {"variable": "SBP", "type": "continuous",
                 "mean_I": 145.0, "std_I": 21.7, "mean_C": 145.0, "std_C": 21.5},
                {"variable": "DBP", "type": "continuous",
                 "mean_I": 81.0, "std_I": 10.8, "mean_C": 81.0, "std_C": 10.7},
                {"variable": "Creatinine", "type": "continuous",
                 "mean_I": 88.0, "std_I": 22.0, "mean_C": 88.0, "std_C": 22.0},
                {"variable": "Mortality", "type": "binary",
                 "prop_I": 0.088, "prop_C": 0.093},
            ],
            "endpoints": ["Mortality"],
            "effect_size": -0.07,
            "effect_var": 0.010,
        },
        {
            "name": "VADT (2009)",
            "n_i": 892, "n_c": 899,
            "table1": [
                {"variable": "Age", "type": "continuous",
                 "mean_I": 60.4, "std_I": 9.0, "mean_C": 60.4, "std_C": 8.7},
                {"variable": "Male", "type": "binary",
                 "prop_I": 0.97, "prop_C": 0.97},
                {"variable": "BMI", "type": "continuous",
                 "mean_I": 31.3, "std_I": 4.5, "mean_C": 31.2, "std_C": 4.6},
                {"variable": "HbA1c", "type": "continuous",
                 "mean_I": 9.4, "std_I": 1.5, "mean_C": 9.4, "std_C": 1.5},
                {"variable": "Duration_DM", "type": "continuous",
                 "mean_I": 11.5, "std_I": 7.3, "mean_C": 11.5, "std_C": 7.4},
                {"variable": "CVD_history", "type": "binary",
                 "prop_I": 0.40, "prop_C": 0.42},
                {"variable": "Smoking", "type": "binary",
                 "prop_I": 0.17, "prop_C": 0.17},
                {"variable": "Hypertension", "type": "binary",
                 "prop_I": 0.72, "prop_C": 0.72},
                {"variable": "SBP", "type": "continuous",
                 "mean_I": 132.0, "std_I": 16.0, "mean_C": 131.0, "std_C": 17.0},
                {"variable": "LDL_Cholesterol", "type": "continuous",
                 "mean_I": 104.0, "std_I": 32.0, "mean_C": 105.0, "std_C": 32.0},
                {"variable": "Triglycerides", "type": "continuous",
                 "mean_I": 196.0, "std_I": 145.0, "mean_C": 193.0, "std_C": 130.0},
                {"variable": "Mortality", "type": "binary",
                 "prop_I": 0.107, "prop_C": 0.109},
            ],
            "endpoints": ["Mortality"],
            "effect_size": -0.02,
            "effect_var": 0.045,
        },
    ],
}


def analyze_example_dataset(dataset: dict) -> dict:
    """Analyze a predefined real-world dataset.

    Parameters
    ----------
    dataset : dict
        One of the example datasets (e.g., STATIN_EXAMPLE).

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
    """Run all real-world data analyses."""
    return {
        "statin": analyze_example_dataset(STATIN_EXAMPLE),
        "glucose_control": analyze_example_dataset(GLUCOSE_CONTROL_EXAMPLE),
    }

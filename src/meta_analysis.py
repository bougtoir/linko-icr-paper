"""
Meta-analysis utilities for ICR research.

Implements random-effects meta-analysis (DerSimonian-Laird),
heterogeneity statistics (I², τ²), and ICR-weighted meta-analysis.
"""

import numpy as np
import pandas as pd
from typing import Optional
from scipy import stats


def fixed_effect_meta(
    effects: np.ndarray,
    variances: np.ndarray,
) -> dict:
    """Fixed-effect (inverse-variance) meta-analysis.

    Parameters
    ----------
    effects : np.ndarray
        Effect sizes from each study.
    variances : np.ndarray
        Variance of effect size from each study.

    Returns
    -------
    dict with pooled effect, SE, CI, and Q statistic.
    """
    weights = 1.0 / variances
    pooled = np.sum(weights * effects) / np.sum(weights)
    pooled_var = 1.0 / np.sum(weights)
    pooled_se = np.sqrt(pooled_var)

    # Cochran's Q
    q = np.sum(weights * (effects - pooled) ** 2)
    k = len(effects)
    q_p = 1 - stats.chi2.cdf(q, df=k - 1) if k > 1 else 1.0

    return {
        "pooled_effect": pooled,
        "pooled_se": pooled_se,
        "ci_lower": pooled - 1.96 * pooled_se,
        "ci_upper": pooled + 1.96 * pooled_se,
        "q_statistic": q,
        "q_p_value": q_p,
        "weights": weights,
    }


def dersimonian_laird_meta(
    effects: np.ndarray,
    variances: np.ndarray,
) -> dict:
    """DerSimonian-Laird random-effects meta-analysis.

    Parameters
    ----------
    effects : np.ndarray
        Effect sizes from each study.
    variances : np.ndarray
        Variance of effect size from each study.

    Returns
    -------
    dict with pooled effect, SE, CI, τ², I², and Q statistic.
    """
    k = len(effects)

    # Fixed-effect first pass
    fe = fixed_effect_meta(effects, variances)
    q = fe["q_statistic"]
    w_fe = fe["weights"]

    # Estimate τ² (between-study variance)
    c = np.sum(w_fe) - np.sum(w_fe ** 2) / np.sum(w_fe)
    tau2 = max(0, (q - (k - 1)) / c) if c > 0 else 0.0

    # Random-effects weights
    w_re = 1.0 / (variances + tau2)
    pooled = np.sum(w_re * effects) / np.sum(w_re)
    pooled_var = 1.0 / np.sum(w_re)
    pooled_se = np.sqrt(pooled_var)

    # I² statistic
    i_squared = max(0, (q - (k - 1)) / q * 100) if q > 0 else 0.0

    # H² statistic
    h_squared = q / (k - 1) if k > 1 else 1.0

    return {
        "pooled_effect": pooled,
        "pooled_se": pooled_se,
        "ci_lower": pooled - 1.96 * pooled_se,
        "ci_upper": pooled + 1.96 * pooled_se,
        "tau_squared": tau2,
        "i_squared": i_squared,
        "h_squared": h_squared,
        "q_statistic": q,
        "q_p_value": fe["q_p_value"],
        "weights": w_re,
        "k_studies": k,
    }


def icr_weighted_meta(
    effects: np.ndarray,
    variances: np.ndarray,
    icr_values: np.ndarray,
    method: str = "multiplicative",
) -> dict:
    """ICR-weighted random-effects meta-analysis.

    Incorporates ICR as an additional weighting factor to account for
    differences in the information contribution of endpoints across studies.

    Parameters
    ----------
    effects : np.ndarray
        Effect sizes.
    variances : np.ndarray
        Variances of effect sizes.
    icr_values : np.ndarray
        ICR values for each study.
    method : str
        "multiplicative": weight_i = ICR_i / (variance_i + τ²)
        "additive": weight_i = 1 / (variance_i + τ² + f(ICRD))

    Returns
    -------
    dict with pooled effect, SE, CI, and comparison to standard method.
    """
    # First, run standard DL meta-analysis
    standard = dersimonian_laird_meta(effects, variances)
    tau2 = standard["tau_squared"]

    if method == "multiplicative":
        # Weight by ICR: studies with higher ICR contribute more
        w_icr = icr_values / (variances + tau2)
    elif method == "additive":
        # Penalize studies with extreme ICR deviations
        icr_mean = np.mean(icr_values)
        icr_penalty = (icr_values - icr_mean) ** 2
        w_icr = 1.0 / (variances + tau2 + icr_penalty)
    else:
        raise ValueError(f"Unknown method: {method}")

    pooled_icr = np.sum(w_icr * effects) / np.sum(w_icr)
    pooled_var_icr = 1.0 / np.sum(w_icr)
    pooled_se_icr = np.sqrt(pooled_var_icr)

    return {
        "pooled_effect_icr": pooled_icr,
        "pooled_se_icr": pooled_se_icr,
        "ci_lower_icr": pooled_icr - 1.96 * pooled_se_icr,
        "ci_upper_icr": pooled_icr + 1.96 * pooled_se_icr,
        "pooled_effect_standard": standard["pooled_effect"],
        "pooled_se_standard": standard["pooled_se"],
        "i_squared_standard": standard["i_squared"],
        "tau_squared_standard": tau2,
        "icr_weights": w_icr,
        "standard_weights": standard["weights"],
        "method": method,
    }


def compute_heterogeneity_metrics(
    effects: np.ndarray,
    variances: np.ndarray,
) -> dict:
    """Compute comprehensive heterogeneity metrics.

    Returns
    -------
    dict with Q, I², τ², H², prediction interval.
    """
    result = dersimonian_laird_meta(effects, variances)
    k = len(effects)

    # Prediction interval (for a future study)
    tau = np.sqrt(result["tau_squared"])
    if k > 2:
        t_crit = stats.t.ppf(0.975, df=k - 2)
        pred_se = np.sqrt(result["pooled_se"] ** 2 + tau ** 2)
        pred_lower = result["pooled_effect"] - t_crit * pred_se
        pred_upper = result["pooled_effect"] + t_crit * pred_se
    else:
        pred_lower = pred_upper = np.nan

    return {
        "q_statistic": result["q_statistic"],
        "q_p_value": result["q_p_value"],
        "i_squared": result["i_squared"],
        "tau_squared": result["tau_squared"],
        "tau": tau,
        "h_squared": result["h_squared"],
        "prediction_interval": (pred_lower, pred_upper),
        "pooled_effect": result["pooled_effect"],
        "pooled_se": result["pooled_se"],
    }


def sequential_meta_analysis(
    effects: np.ndarray,
    variances: np.ndarray,
    icr_values: Optional[np.ndarray] = None,
    step_sizes: Optional[list[int]] = None,
) -> pd.DataFrame:
    """Perform sequential (cumulative) meta-analysis.

    Adds studies one by one (or in batches) and tracks how
    heterogeneity and pooled estimates evolve.

    Parameters
    ----------
    effects, variances : np.ndarray
        Study-level data.
    icr_values : np.ndarray, optional
        ICR values for each study.
    step_sizes : list of int, optional
        Number of studies to include at each step. If None, adds one at a time.

    Returns
    -------
    pd.DataFrame with columns for each step's results.
    """
    k = len(effects)
    if step_sizes is None:
        step_sizes = list(range(2, k + 1))

    rows = []
    for n in step_sizes:
        if n > k:
            break
        sub_effects = effects[:n]
        sub_variances = variances[:n]

        result = dersimonian_laird_meta(sub_effects, sub_variances)

        row = {
            "n_studies": n,
            "pooled_effect": result["pooled_effect"],
            "pooled_se": result["pooled_se"],
            "ci_lower": result["ci_lower"],
            "ci_upper": result["ci_upper"],
            "i_squared": result["i_squared"],
            "tau_squared": result["tau_squared"],
            "q_statistic": result["q_statistic"],
        }

        if icr_values is not None:
            sub_icr = icr_values[:n]
            row["icr_mean"] = np.mean(sub_icr)
            row["icr_sd"] = np.std(sub_icr, ddof=1) if n > 1 else 0.0
            row["icr_cv"] = row["icr_sd"] / row["icr_mean"] if row["icr_mean"] > 0 else 0.0
            row["icrd"] = np.max(sub_icr) - np.min(sub_icr)

        rows.append(row)

    return pd.DataFrame(rows)

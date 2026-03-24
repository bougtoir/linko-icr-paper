"""
PCA-based ICR Calculator (ICR_pca)

Computes the Information Contribution Ratio using Principal Component Analysis
on individual patient data (IPD). This approach captures the covariance structure
and provides a more accurate measure of endpoint information contribution.

Two methods are provided:
1. Loading-based: Identifies PCs dominated by endpoint variables
2. Regression-based: Regresses endpoint on all PCs to measure contribution
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Optional


def compute_icr_pca_loading(
    df: pd.DataFrame,
    endpoint_cols: list[str],
    group_col: Optional[str] = None,
    threshold: float = 0.3,
) -> dict:
    """Compute ICR_pca using loading-based method.

    Identifies principal components where endpoint variables have high loadings,
    then computes the proportion of total variance explained by those components.

    Parameters
    ----------
    df : pd.DataFrame
        Raw IPD data with one row per subject.
    endpoint_cols : list of str
        Column names for endpoint variables.
    group_col : str, optional
        Column for group assignment (excluded from PCA).
    threshold : float
        Minimum absolute loading for an endpoint variable to be considered
        "dominant" in a principal component.

    Returns
    -------
    dict with keys:
        - "icr_pca": float
        - "endpoint_dominant_pcs": list of int (PC indices)
        - "explained_variance_ratios": np.ndarray
        - "loadings_matrix": pd.DataFrame
        - "n_components": int
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if group_col and group_col in numeric_cols:
        numeric_cols.remove(group_col)

    X = df[numeric_cols].dropna()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA()
    pca.fit(X_scaled)

    loadings = pd.DataFrame(
        pca.components_.T,
        index=numeric_cols,
        columns=[f"PC{i+1}" for i in range(len(numeric_cols))],
    )

    # Identify PCs where endpoint variables have dominant loadings
    endpoint_dominant_pcs = []
    for i, pc_col in enumerate(loadings.columns):
        endpoint_loadings = loadings.loc[
            loadings.index.isin(endpoint_cols), pc_col
        ].abs()
        if endpoint_loadings.max() >= threshold:
            endpoint_dominant_pcs.append(i)

    # ICR_pca = sum of explained variance ratios for endpoint-dominant PCs
    evr = pca.explained_variance_ratio_
    icr_pca = sum(evr[i] for i in endpoint_dominant_pcs)

    return {
        "icr_pca": icr_pca,
        "endpoint_dominant_pcs": endpoint_dominant_pcs,
        "explained_variance_ratios": evr,
        "loadings_matrix": loadings,
        "n_components": len(numeric_cols),
    }


def compute_icr_pca_regression(
    df: pd.DataFrame,
    endpoint_col: str,
    group_col: Optional[str] = None,
) -> dict:
    """Compute ICR_pca using regression-based method.

    Regresses the endpoint variable on all principal component scores,
    then computes the proportion of endpoint variance explained by
    each PC, weighted by that PC's eigenvalue.

    ICR_pca_reg = Σ_k (β_k² × λ_k) / Var(Y_endpoint)

    Parameters
    ----------
    df : pd.DataFrame
        Raw IPD data.
    endpoint_col : str
        Name of the single endpoint column.
    group_col : str, optional
        Column for group assignment (excluded from PCA).

    Returns
    -------
    dict with keys:
        - "icr_pca_reg": float
        - "pc_contributions": np.ndarray (contribution of each PC)
        - "beta_coefficients": np.ndarray
        - "eigenvalues": np.ndarray
        - "r_squared": float
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if group_col and group_col in numeric_cols:
        numeric_cols.remove(group_col)

    # Separate endpoint from predictors
    predictor_cols = [c for c in numeric_cols if c != endpoint_col]

    data = df[numeric_cols].dropna()
    y = data[endpoint_col].values
    X = data[predictor_cols].values

    # Standardize predictors
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # PCA on predictors only
    pca = PCA()
    pc_scores = pca.fit_transform(X_scaled)
    eigenvalues = pca.explained_variance_

    # Regress endpoint on PC scores using OLS
    # Since PCs are orthogonal, β_k = cov(Y, PC_k) / var(PC_k)
    var_y = np.var(y, ddof=1)
    betas = np.array([
        np.cov(y, pc_scores[:, k])[0, 1] / np.var(pc_scores[:, k], ddof=1)
        for k in range(pc_scores.shape[1])
    ])

    # Contribution of each PC to endpoint variance
    # contribution_k = β_k² × λ_k
    contributions = betas ** 2 * eigenvalues

    # R² = sum of contributions / Var(Y)
    r_squared = np.sum(contributions) / var_y if var_y > 0 else 0.0

    # ICR_pca_reg: proportion of total data variance that "flows to" the endpoint
    total_eigenvalue_sum = np.sum(eigenvalues)
    icr_pca_reg = np.sum(contributions) / (total_eigenvalue_sum + var_y) if (total_eigenvalue_sum + var_y) > 0 else 0.0

    return {
        "icr_pca_reg": icr_pca_reg,
        "pc_contributions": contributions,
        "beta_coefficients": betas,
        "eigenvalues": eigenvalues,
        "r_squared": r_squared,
    }


def compare_icr_methods(
    df: pd.DataFrame,
    endpoint_cols: list[str],
    group_col: Optional[str] = None,
) -> pd.DataFrame:
    """Compare ICR_v and ICR_pca methods on the same dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Raw IPD data.
    endpoint_cols : list of str
        Endpoint column names.
    group_col : str, optional
        Group column name.

    Returns
    -------
    pd.DataFrame
        Comparison table of ICR values from different methods.
    """
    from .icr_calculator import compute_icr_v_from_dataframe

    results = []

    # ICR_v
    icr_v_result = compute_icr_v_from_dataframe(df, endpoint_cols, group_col)
    results.append({
        "method": "ICR_v (variance-based)",
        "icr_value": icr_v_result["icr_v_all"],
        "n_variables": icr_v_result["n_variables_used"],
    })

    # ICR_pca (loading-based)
    icr_pca_loading = compute_icr_pca_loading(df, endpoint_cols, group_col)
    results.append({
        "method": "ICR_pca (loading-based)",
        "icr_value": icr_pca_loading["icr_pca"],
        "n_variables": icr_pca_loading["n_components"],
    })

    # ICR_pca (regression-based) for each endpoint
    for ep in endpoint_cols:
        icr_pca_reg = compute_icr_pca_regression(df, ep, group_col)
        results.append({
            "method": f"ICR_pca_reg ({ep})",
            "icr_value": icr_pca_reg["icr_pca_reg"],
            "n_variables": len(df.select_dtypes(include=[np.number]).columns) - 1,
        })

    return pd.DataFrame(results)

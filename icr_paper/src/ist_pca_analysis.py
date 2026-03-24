"""
IST (International Stroke Trial) PCA-based ICR Analysis

Validates the PCA-based ICR approach using the publicly available IST dataset
(19,435 patients, 112 variables). Countries are treated as sub-studies to
demonstrate how ICR_pca varies across different data contexts within the
same multi-national trial.

Data source: https://trialsjournal.biomedcentral.com/articles/10.1186/1745-6215-12-101
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional


def load_and_encode_ist(data_path: str) -> tuple[pd.DataFrame, list[str], str]:
    """Load IST data and encode categoricals for PCA.

    Returns
    -------
    tuple of (encoded_df, all_analysis_vars, endpoint_col)
    """
    df = pd.read_csv(data_path, encoding="latin-1", low_memory=False)

    # Binary encodings
    binary_maps = {
        "SEX": {"M": 1, "F": 0},
        "RSLEEP": {"Y": 1, "N": 0},
        "RATRIAL": {"Y": 1, "N": 0},
        "RCT": {"Y": 1, "N": 0},
        "RVISINF": {"Y": 1, "N": 0},
        "RHEP24": {"Y": 1, "N": 0},
        "RASP3": {"Y": 1, "N": 0},
        "RXASP": {"Y": 1, "N": 0},
    }
    for col, mapping in binary_maps.items():
        df[col + "_num"] = df[col].map(mapping)

    # Ordinal encodings
    df["RCONSC_num"] = df["RCONSC"].map({"F": 0, "D": 1, "U": 2})
    df["RXHEP_num"] = df["RXHEP"].map({"N": 0, "L": 1, "M": 2, "H": 3})

    # Deficit flags
    for i in range(1, 9):
        df[f"RDEF{i}_num"] = (df[f"RDEF{i}"] == "Y").astype(int)

    # Stroke subtype dummies
    for stype in ["TACS", "PACS", "POCS", "LACS"]:
        df[f"STYPE_{stype}"] = (df["STYPE"] == stype).astype(int)

    # Analysis variable list
    all_vars = (
        ["RDELAY", "AGE", "RSBP"]
        + [
            c + "_num"
            for c in [
                "SEX", "RSLEEP", "RATRIAL", "RCT", "RVISINF",
                "RHEP24", "RASP3", "RCONSC", "RXHEP",
            ]
        ]
        + [f"RDEF{i}_num" for i in range(1, 9)]
        + [f"STYPE_{s}" for s in ["TACS", "PACS", "POCS", "LACS"]]
        + ["DIED"]
    )

    endpoint_col = "DIED"
    return df, all_vars, endpoint_col


def compute_icr_pca_by_country(
    df: pd.DataFrame,
    all_vars: list[str],
    endpoint_col: str,
    countries: Optional[list[str]] = None,
    threshold: float = 0.3,
) -> pd.DataFrame:
    """Compute ICR_pca for each country sub-study.

    Parameters
    ----------
    df : pd.DataFrame
        Encoded IST data.
    all_vars : list of str
        All analysis variable names (including endpoint).
    endpoint_col : str
        Endpoint column name.
    countries : list of str, optional
        Countries to analyse. Defaults to top-8 by sample size.
    threshold : float
        Loading threshold for endpoint-dominant PC identification.

    Returns
    -------
    pd.DataFrame with columns: country, n, mortality_rate, icr_std,
        icr_pca_loading, icr_pca_reg, n_endpoint_pcs
    """
    analysis_df = df[all_vars + ["COUNTRY"]].dropna()
    D = len(all_vars)

    if countries is None:
        countries = (
            analysis_df["COUNTRY"].value_counts().head(8).index.tolist()
        )

    results = []
    for country in countries:
        sub = analysis_df[analysis_df["COUNTRY"] == country]
        n = len(sub)
        if n < 50:
            continue

        X_sub = sub[all_vars].values.astype(float)
        X_scaled = StandardScaler().fit_transform(X_sub)

        # Full PCA (loading-based)
        pca_sub = PCA()
        pca_sub.fit(X_scaled)
        loadings = pca_sub.components_.T
        evr = pca_sub.explained_variance_ratio_
        ep_idx = all_vars.index(endpoint_col)

        ep_pcs = [
            i for i in range(D) if abs(loadings[ep_idx, i]) >= threshold
        ]
        icr_pca_loading = sum(evr[i] for i in ep_pcs)

        # Regression-based: PCA on predictors, regress endpoint
        pred_vars = [v for v in all_vars if v != endpoint_col]
        X_pred = sub[pred_vars].values.astype(float)
        y = sub[endpoint_col].values.astype(float)
        X_pred_scaled = StandardScaler().fit_transform(X_pred)

        pca_pred = PCA()
        pc_scores = pca_pred.fit_transform(X_pred_scaled)
        eigenvalues = pca_pred.explained_variance_
        var_y = np.var(y, ddof=1)

        betas = np.array([
            (
                np.cov(y, pc_scores[:, k])[0, 1]
                / np.var(pc_scores[:, k], ddof=1)
            )
            if np.var(pc_scores[:, k], ddof=1) > 1e-10
            else 0.0
            for k in range(pc_scores.shape[1])
        ])
        contributions = betas**2 * eigenvalues
        total_info = np.sum(eigenvalues) + var_y
        icr_pca_reg = (
            np.sum(contributions) / total_info if total_info > 0 else 0.0
        )

        results.append(
            {
                "country": country,
                "n": n,
                "mortality_rate": sub[endpoint_col].mean(),
                "icr_std": 1.0 / D,
                "icr_pca_loading": icr_pca_loading,
                "icr_pca_reg": icr_pca_reg,
                "n_endpoint_pcs": len(ep_pcs),
            }
        )

    return pd.DataFrame(results)


def generate_ist_pca_figure(
    res_df: pd.DataFrame,
    all_vars: list[str],
    endpoint_col: str,
    analysis_df: pd.DataFrame,
    threshold: float = 0.3,
    output_dir: str = "icr_paper/figures",
) -> str:
    """Generate 4-panel PCA-ICR figure for the IST analysis."""
    D = len(all_vars)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "PCA-based ICR Analysis: International Stroke Trial (IST)\n"
        f"Countries as Sub-studies (D={D} variables, d=1 endpoint)",
        fontsize=13,
    )

    colors = plt.cm.Set2(np.linspace(0, 1, len(res_df)))

    # Panel A: ICR_pca by country
    bars = axes[0, 0].barh(
        res_df["country"], res_df["icr_pca_loading"], color=colors
    )
    axes[0, 0].axvline(
        x=res_df["icr_std"].iloc[0],
        color="red",
        linestyle="--",
        label=f"ICR_std = {res_df['icr_std'].iloc[0]:.3f}",
    )
    for bar_item, val in zip(bars, res_df["icr_pca_loading"]):
        axes[0, 0].text(
            val + 0.003,
            bar_item.get_y() + bar_item.get_height() / 2,
            f"{val:.3f}",
            va="center",
            fontsize=9,
        )
    axes[0, 0].set_xlabel("ICR_pca (loading-based)")
    axes[0, 0].set_title("A. ICR_pca by Country")
    axes[0, 0].legend(fontsize=9)

    # Panel B: ICR_pca vs mortality
    axes[0, 1].scatter(
        res_df["icr_pca_loading"],
        res_df["mortality_rate"],
        s=res_df["n"] / 20,
        alpha=0.7,
        c=colors,
    )
    for _, row in res_df.iterrows():
        axes[0, 1].annotate(
            row["country"],
            (row["icr_pca_loading"], row["mortality_rate"]),
            fontsize=9,
            ha="center",
            va="bottom",
        )
    r_load = res_df["icr_pca_loading"].corr(res_df["mortality_rate"])
    axes[0, 1].set_xlabel("ICR_pca (loading-based)")
    axes[0, 1].set_ylabel("14-day Mortality Rate")
    axes[0, 1].set_title(f"B. ICR_pca vs Mortality (r = {r_load:.3f})")

    # Panel C: Comparison of ICR methods
    x = np.arange(len(res_df))
    width = 0.35
    axes[1, 0].bar(
        x - width / 2,
        res_df["icr_pca_loading"],
        width,
        label="ICR_pca (loading)",
        color="steelblue",
    )
    axes[1, 0].bar(
        x + width / 2,
        res_df["icr_pca_reg"],
        width,
        label="ICR_pca (regression)",
        color="coral",
    )
    axes[1, 0].axhline(
        y=res_df["icr_std"].iloc[0],
        color="red",
        linestyle="--",
        label=f"ICR_std = {res_df['icr_std'].iloc[0]:.3f}",
    )
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(
        res_df["country"], rotation=45, ha="right"
    )
    axes[1, 0].set_ylabel("ICR Value")
    axes[1, 0].set_title("C. ICR Method Comparison")
    axes[1, 0].legend(fontsize=8)

    # Panel D: PCA variance explained (full dataset)
    X_full = analysis_df[all_vars].values.astype(float)
    X_full_scaled = StandardScaler().fit_transform(X_full)
    pca_full = PCA()
    pca_full.fit(X_full_scaled)
    evr_full = pca_full.explained_variance_ratio_
    loadings_full = pca_full.components_.T
    ep_idx = all_vars.index(endpoint_col)

    n_show = min(15, D)
    bar_colors = [
        "red" if abs(loadings_full[ep_idx, i]) >= threshold else "steelblue"
        for i in range(n_show)
    ]
    axes[1, 1].bar(range(1, n_show + 1), evr_full[:n_show], color=bar_colors)
    axes[1, 1].set_xlabel("Principal Component")
    axes[1, 1].set_ylabel("Explained Variance Ratio")
    axes[1, 1].set_title("D. PCA Variance (red = endpoint-dominant)")

    plt.tight_layout()
    out_path = Path(output_dir) / "fig_pca_ist_analysis.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close()
    return str(out_path)


def run_ist_pca_analysis(
    data_path: str = "icr_paper/data/ist_corrected.csv",
    output_dir: str = "icr_paper/figures",
) -> dict:
    """Run the full IST PCA-based ICR analysis.

    Returns
    -------
    dict with keys: country_results (DataFrame), summary (dict), figure_path (str)
    """
    df, all_vars, endpoint_col = load_and_encode_ist(data_path)
    res_df = compute_icr_pca_by_country(df, all_vars, endpoint_col)

    analysis_df = df[all_vars + ["COUNTRY"]].dropna()
    figure_path = generate_ist_pca_figure(
        res_df, all_vars, endpoint_col, analysis_df, output_dir=output_dir
    )

    summary = {
        "n_countries": len(res_df),
        "total_patients": res_df["n"].sum(),
        "n_variables": len(all_vars),
        "icr_std": 1.0 / len(all_vars),
        "icr_pca_loading_range": (
            res_df["icr_pca_loading"].min(),
            res_df["icr_pca_loading"].max(),
        ),
        "icr_pca_loading_cv": (
            res_df["icr_pca_loading"].std()
            / res_df["icr_pca_loading"].mean()
        ),
        "icr_pca_reg_range": (
            res_df["icr_pca_reg"].min(),
            res_df["icr_pca_reg"].max(),
        ),
        "icr_pca_reg_cv": (
            res_df["icr_pca_reg"].std() / res_df["icr_pca_reg"].mean()
        ),
        "corr_loading_mortality": res_df["icr_pca_loading"].corr(
            res_df["mortality_rate"]
        ),
        "corr_reg_mortality": res_df["icr_pca_reg"].corr(
            res_df["mortality_rate"]
        ),
    }

    return {
        "country_results": res_df,
        "summary": summary,
        "figure_path": figure_path,
    }


if __name__ == "__main__":
    result = run_ist_pca_analysis()
    print("\n=== IST PCA-based ICR Analysis Results ===\n")
    print(result["country_results"].to_string(index=False))
    print(f"\nSummary:")
    for k, v in result["summary"].items():
        print(f"  {k}: {v}")
    print(f"\nFigure: {result['figure_path']}")

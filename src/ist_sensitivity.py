"""Leave-one-out sensitivity analysis for the IST country sub-study results."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from .ist_pca_analysis import DEFAULT_FIGURE_DIR


def leave_one_out_correlations(res_df: pd.DataFrame) -> pd.DataFrame:
    """Correlation of ICR_pca with mortality, excluding one country at a time."""
    rows = []
    for excluded in list(res_df["country"]) + [None]:
        sub = res_df if excluded is None else res_df[res_df["country"] != excluded]
        row = {
            "excluded_country": "None (all countries)" if excluded is None else excluded,
            "n_countries": len(sub),
        }
        for measure, label in [
            ("icr_pca_loading", "loading"),
            ("icr_pca_reg", "regression"),
        ]:
            r, p = stats.pearsonr(sub[measure], sub["mortality_rate"])
            row[f"r_{label}"] = r
            row[f"p_{label}"] = p
        rows.append(row)
    return pd.DataFrame(rows)


def size_adjusted_association(res_df: pd.DataFrame) -> dict:
    """Check whether the ICR-mortality association is confounded by group size.

    Larger country groups give more stable covariance estimates, so the number
    of patients is a candidate common cause of both the PCA-based estimators
    and the observed mortality. Reports the correlation of log group size with
    each estimator and with mortality, plus the partial correlation of each
    estimator with mortality given log group size.
    """
    log_n = np.log(res_df["n"].to_numpy(dtype=float))
    mortality = res_df["mortality_rate"].to_numpy(dtype=float)
    out = {}
    r_size_mortality, p_size_mortality = stats.pearsonr(log_n, mortality)
    out["r_log_n_vs_mortality"] = float(r_size_mortality)
    out["p_log_n_vs_mortality"] = float(p_size_mortality)
    for measure, label in [("icr_pca_loading", "loading"), ("icr_pca_reg", "regression")]:
        values = res_df[measure].to_numpy(dtype=float)
        r_size, p_size = stats.pearsonr(log_n, values)
        r_full, _ = stats.pearsonr(values, mortality)
        denominator = np.sqrt((1 - r_size**2) * (1 - r_size_mortality**2))
        partial = (r_full - r_size * r_size_mortality) / denominator
        degrees = len(res_df) - 3
        t_statistic = partial * np.sqrt(degrees / (1 - partial**2))
        out[f"r_log_n_vs_{label}"] = float(r_size)
        out[f"p_log_n_vs_{label}"] = float(p_size)
        out[f"partial_r_{label}"] = float(partial)
        out[f"partial_p_{label}"] = float(2 * stats.t.sf(abs(t_statistic), degrees))
        out[f"partial_df_{label}"] = int(degrees)
    return out


def generate_loo_figure(
    loo_df: pd.DataFrame, output_dir: str = str(DEFAULT_FIGURE_DIR)
) -> str:
    """Two-panel figure: LOO correlation coefficients and p-values."""
    full = loo_df[loo_df["excluded_country"].str.startswith("None")]
    excl = loo_df[~loo_df["excluded_country"].str.startswith("None")]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(len(excl))
    width = 0.38

    axes[0].bar(x - width / 2, excl["r_loading"], width, label="ICR$_{pca}$ (loading)", color="steelblue")
    axes[0].bar(x + width / 2, excl["r_regression"], width, label="ICR$_{pca}$ (regression)", color="coral")
    for series, colour in [("r_loading", "steelblue"), ("r_regression", "coral")]:
        axes[0].axhline(float(full[series].iloc[0]), color=colour, linestyle="--", linewidth=1)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(excl["excluded_country"], rotation=45, ha="right")
    axes[0].set_ylabel("Pearson r with 14-day mortality")
    axes[0].set_title("A. Leave-one-out correlation (dashed = all countries)")
    axes[0].legend(fontsize=9)

    axes[1].bar(x - width / 2, excl["p_loading"], width, label="ICR$_{pca}$ (loading)", color="steelblue")
    axes[1].bar(x + width / 2, excl["p_regression"], width, label="ICR$_{pca}$ (regression)", color="coral")
    axes[1].axhline(0.05, color="red", linestyle="--", linewidth=1, label="p = 0.05")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(excl["excluded_country"], rotation=45, ha="right")
    axes[1].set_ylabel("p-value")
    axes[1].set_title("B. Leave-one-out p-values")
    axes[1].legend(fontsize=9)

    plt.tight_layout()
    out_path = Path(output_dir) / "fig_loo_sensitivity.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(out_path), dpi=600, bbox_inches="tight")
    plt.close()
    return str(out_path)

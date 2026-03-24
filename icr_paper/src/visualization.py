"""
Visualization utilities for ICR research paper.

Generates publication-quality figures for the simulation study,
real-world analysis, and method comparison.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from typing import Optional


FIGURE_DIR = Path(__file__).parent.parent / "figures"
FIGURE_DIR.mkdir(exist_ok=True)

# Style settings
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def plot_scenario_comparison(
    results_a: pd.DataFrame,
    results_b: pd.DataFrame,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Compare Scenario A (uniform ICR) vs Scenario B (heterogeneous ICR).

    Shows distributions of I², ICRD, and their relationship.
    """
    fig, axes = plt.subplots(2, 3, figsize=(14, 9))

    # Row 1: Distributions
    # I² distribution
    axes[0, 0].hist(results_a["i_squared"], bins=30, alpha=0.6, label="A: Uniform ICR", color="steelblue")
    axes[0, 0].hist(results_b["i_squared"], bins=30, alpha=0.6, label="B: Heterogeneous ICR", color="coral")
    axes[0, 0].set_xlabel("I² (%)")
    axes[0, 0].set_ylabel("Frequency")
    axes[0, 0].set_title("Distribution of Heterogeneity (I²)")
    axes[0, 0].legend()

    # ICRD distribution
    axes[0, 1].hist(results_a["icrd"], bins=30, alpha=0.6, label="A", color="steelblue")
    axes[0, 1].hist(results_b["icrd"], bins=30, alpha=0.6, label="B", color="coral")
    axes[0, 1].set_xlabel("ICRD (max ICR - min ICR)")
    axes[0, 1].set_ylabel("Frequency")
    axes[0, 1].set_title("Distribution of ICR Discrepancy")
    axes[0, 1].legend()

    # Pooled effect distribution
    axes[0, 2].hist(results_a["pooled_effect"], bins=30, alpha=0.6, label="A", color="steelblue")
    axes[0, 2].hist(results_b["pooled_effect"], bins=30, alpha=0.6, label="B", color="coral")
    axes[0, 2].axvline(x=0.5, color="black", linestyle="--", label="True effect")
    axes[0, 2].set_xlabel("Pooled Effect Size")
    axes[0, 2].set_ylabel("Frequency")
    axes[0, 2].set_title("Distribution of Pooled Effect Estimates")
    axes[0, 2].legend()

    # Row 2: Relationships
    # ICRD vs I²
    axes[1, 0].scatter(results_a["icrd"], results_a["i_squared"],
                       alpha=0.3, s=10, label="A", color="steelblue")
    axes[1, 0].scatter(results_b["icrd"], results_b["i_squared"],
                       alpha=0.3, s=10, label="B", color="coral")
    axes[1, 0].set_xlabel("ICRD")
    axes[1, 0].set_ylabel("I² (%)")
    axes[1, 0].set_title("ICRD vs Heterogeneity")
    axes[1, 0].legend()

    # ICR SD vs I²
    axes[1, 1].scatter(results_a["icr_sd"], results_a["i_squared"],
                       alpha=0.3, s=10, label="A", color="steelblue")
    axes[1, 1].scatter(results_b["icr_sd"], results_b["i_squared"],
                       alpha=0.3, s=10, label="B", color="coral")
    axes[1, 1].set_xlabel("ICR Standard Deviation")
    axes[1, 1].set_ylabel("I² (%)")
    axes[1, 1].set_title("ICR Variability vs Heterogeneity")
    axes[1, 1].legend()

    # ICR mean vs pooled effect bias
    bias_a = results_a["pooled_effect"] - 0.5
    bias_b = results_b["pooled_effect"] - 0.5
    axes[1, 2].scatter(results_a["icr_mean"], bias_a,
                       alpha=0.3, s=10, label="A", color="steelblue")
    axes[1, 2].scatter(results_b["icr_mean"], bias_b,
                       alpha=0.3, s=10, label="B", color="coral")
    axes[1, 2].axhline(y=0, color="black", linestyle="--")
    axes[1, 2].set_xlabel("Mean ICR")
    axes[1, 2].set_ylabel("Bias (Pooled - True)")
    axes[1, 2].set_title("Mean ICR vs Estimation Bias")
    axes[1, 2].legend()

    fig.suptitle("Simulation Study: Uniform vs Heterogeneous ICR", fontsize=15, y=1.02)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path)
    else:
        fig.savefig(FIGURE_DIR / "fig1_scenario_comparison.png")

    return fig


def plot_sequential_analysis(
    results_c: pd.DataFrame,
    example_sequential: Optional[pd.DataFrame] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot Scenario C: sequential meta-analysis with ICR shift."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # I² change distribution
    axes[0].hist(results_c["i_squared_change"], bins=30, color="mediumpurple", alpha=0.7)
    axes[0].axvline(x=0, color="black", linestyle="--")
    axes[0].set_xlabel("Change in I² (Final - Initial)")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("I² Change After Adding\nHeterogeneous-ICR Studies")

    # Initial vs final I²
    axes[1].scatter(results_c["initial_i_squared"], results_c["final_i_squared"],
                    alpha=0.3, s=10, color="mediumpurple")
    max_val = max(results_c["final_i_squared"].max(), results_c["initial_i_squared"].max())
    axes[1].plot([0, max_val], [0, max_val], "k--", alpha=0.5)
    axes[1].set_xlabel("Initial I² (5 uniform-ICR studies)")
    axes[1].set_ylabel("Final I² (+ 10 heterogeneous-ICR studies)")
    axes[1].set_title("Heterogeneity Before vs After\nAdding Diverse Studies")

    # ICR CV change vs I² change
    if "initial_icr_cv" in results_c.columns and "final_icr_cv" in results_c.columns:
        icr_cv_change = results_c["final_icr_cv"] - results_c["initial_icr_cv"]
        axes[2].scatter(icr_cv_change, results_c["i_squared_change"],
                        alpha=0.3, s=10, color="mediumpurple")
        axes[2].set_xlabel("Change in ICR CV")
        axes[2].set_ylabel("Change in I²")
        axes[2].set_title("ICR Variability Change\nvs Heterogeneity Change")

    fig.suptitle("Sequential Meta-Analysis: Effect of ICR Heterogeneity", fontsize=14, y=1.02)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path)
    else:
        fig.savefig(FIGURE_DIR / "fig2_sequential_analysis.png")

    return fig


def plot_real_world_icr(
    analysis_result: dict,
    title: str = "",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot ICR analysis results for a real-world dataset."""
    df = analysis_result["study_results"]
    seq = analysis_result["sequential_meta"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # ICR by study
    colors = plt.cm.Set2(np.linspace(0, 1, len(df)))
    bars = axes[0, 0].barh(df["study"], df["icr_std"], color=colors)
    axes[0, 0].set_xlabel("ICR_std (d/D)")
    axes[0, 0].set_title("Standardized ICR by Study")
    for bar_item, val in zip(bars, df["icr_std"]):
        axes[0, 0].text(val + 0.002, bar_item.get_y() + bar_item.get_height() / 2,
                        f"{val:.3f}", va="center", fontsize=9)

    # ICR vs Effect size
    axes[0, 1].scatter(df["icr_std"], df["effect_size"], s=df["n_total"] / 30, alpha=0.7)
    for _, row in df.iterrows():
        axes[0, 1].annotate(row["study"].split(" ")[0],
                            (row["icr_std"], row["effect_size"]),
                            fontsize=8, ha="center", va="bottom")
    axes[0, 1].set_xlabel("ICR_std (d/D)")
    axes[0, 1].set_ylabel("Effect Size")
    axes[0, 1].set_title("ICR vs Effect Size\n(bubble size = sample size)")

    # Sequential I²
    if len(seq) > 0:
        axes[1, 0].plot(seq["n_studies"], seq["i_squared"], "o-", color="darkred")
        axes[1, 0].set_xlabel("Number of Studies")
        axes[1, 0].set_ylabel("I² (%)")
        axes[1, 0].set_title("Sequential Heterogeneity (I²)")
        axes[1, 0].set_ylim(bottom=0)

    # Sequential ICR CV
    if "icr_cv" in seq.columns:
        axes[1, 1].plot(seq["n_studies"], seq["icr_cv"], "s-", color="teal")
        axes[1, 1].set_xlabel("Number of Studies")
        axes[1, 1].set_ylabel("ICR Coefficient of Variation")
        axes[1, 1].set_title("Sequential ICR Variability")

    fig.suptitle(f"Real-World Analysis: {title}", fontsize=14, y=1.02)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path)
    else:
        fig.savefig(FIGURE_DIR / f"fig_realworld_{title.lower().replace(' ', '_')}.png")

    return fig


def plot_number_of_variables_effect(
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Illustrative figure showing how D (number of variables) affects ICR.

    When d endpoints are fixed, ICR = d/D under standardization,
    so more variables measured means lower ICR.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    D_values = np.arange(5, 101)
    for d in [1, 2, 3]:
        icr = d / D_values
        ax.plot(D_values, icr, label=f"d = {d} endpoint(s)", linewidth=2)

    ax.set_xlabel("D (Total number of variables measured)")
    ax.set_ylabel("ICR (standardized)")
    ax.set_title("Theoretical ICR as a Function of Data Dimensionality\n"
                 "(assuming standardized variables with equal variance)")
    ax.legend()
    ax.set_ylim(0, 0.65)
    ax.grid(True, alpha=0.3)

    if save_path:
        fig.savefig(save_path)
    else:
        fig.savefig(FIGURE_DIR / "fig0_icr_dimension_relationship.png")

    return fig


def generate_all_figures(
    simulation_results: Optional[dict] = None,
    real_world_results: Optional[dict] = None,
) -> list[str]:
    """Generate all figures for the paper.

    Returns list of saved file paths.
    """
    saved = []

    # Figure 0: Conceptual
    fig0 = plot_number_of_variables_effect()
    saved.append(str(FIGURE_DIR / "fig0_icr_dimension_relationship.png"))
    plt.close(fig0)

    if simulation_results:
        # Figure 1: Scenario comparison
        fig1 = plot_scenario_comparison(
            simulation_results["A"],
            simulation_results["B"],
        )
        saved.append(str(FIGURE_DIR / "fig1_scenario_comparison.png"))
        plt.close(fig1)

        # Figure 2: Sequential analysis
        fig2 = plot_sequential_analysis(simulation_results["C"])
        saved.append(str(FIGURE_DIR / "fig2_sequential_analysis.png"))
        plt.close(fig2)

    if real_world_results:
        for key, result in real_world_results.items():
            fig = plot_real_world_icr(result, title=key.replace("_", " ").title())
            saved.append(str(FIGURE_DIR / f"fig_realworld_{key}.png"))
            plt.close(fig)

    return saved

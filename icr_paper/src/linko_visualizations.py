"""
LINKO (Latent Information Normalization for Key Outcomes) visualization tools.

Implements:
1. Prism Forest Plot: Enhanced forest plot with ICR dimensions (bar color + marker size)
2. Early Convergence Analysis: Can ICR-guided study selection reach conclusions faster?
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from scipy import stats
from typing import Optional
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def prism_forest_plot(
    effects, se, icr_values, study_labels=None,
    icr_label="ICR", pooled_effect=None, pooled_se=None,
    title="LINKO Prism Forest Plot",
    output_path="fig_prism_forest.png",
    icr_secondary=None, icr_secondary_label="ICR_pca",
):
    """
    Generate a LINKO Prism Forest Plot: an enhanced forest plot where
    each study's CI bar is colored by its ICR value (warm=high, cool=low),
    and point size encodes a secondary ICR measure if available.

    Like a prism decomposes light into a spectrum, this plot decomposes
    the standard forest plot to reveal the hidden ICR dimension.

    Parameters
    ----------
    effects : array-like - Effect sizes
    se : array-like - Standard errors
    icr_values : array-like - Primary ICR values (for color)
    study_labels : list of str
    icr_label : str - Label for primary ICR
    pooled_effect, pooled_se : float - Pooled estimate
    title : str
    output_path : str
    icr_secondary : array-like, optional - Secondary ICR (for point size)
    icr_secondary_label : str
    """
    effects = np.asarray(effects, dtype=float)
    se = np.asarray(se, dtype=float)
    icr_values = np.asarray(icr_values, dtype=float)
    n = len(effects)

    if study_labels is None:
        study_labels = [f"Study {i+1}" for i in range(n)]

    ci_lo = effects - 1.96 * se
    ci_hi = effects + 1.96 * se

    # Color map: ICR value -> color (cool blue=low, warm red=high)
    cmap = plt.cm.RdYlBu_r
    vmin = icr_values.min() * 0.9
    vmax = icr_values.max() * 1.1
    norm = Normalize(vmin=vmin, vmax=vmax)

    # Point sizes from secondary ICR if available
    if icr_secondary is not None:
        icr_secondary = np.asarray(icr_secondary, dtype=float)
        s_min, s_max = 60, 250
        sr = icr_secondary.max() - icr_secondary.min()
        if sr > 0:
            sizes = s_min + (icr_secondary - icr_secondary.min()) / sr * (s_max - s_min)
        else:
            sizes = np.full(n, (s_min + s_max) / 2)
    else:
        sizes = np.full(n, 120)

    # Figure with two panels: forest plot + ICR bar chart
    fig, (ax_forest, ax_icr) = plt.subplots(
        1, 2, figsize=(14, max(6, n * 0.7 + 2)),
        gridspec_kw={"width_ratios": [3, 1]}, sharey=True
    )

    y_positions = np.arange(n, 0, -1)

    # --- Left panel: Forest plot with colored CIs ---
    for i in range(n):
        color = cmap(norm(icr_values[i]))

        # CI line (colored by ICR)
        ax_forest.plot(
            [ci_lo[i], ci_hi[i]], [y_positions[i], y_positions[i]],
            color=color, linewidth=3, solid_capstyle="round", alpha=0.85
        )

        # Point estimate (size by secondary ICR)
        ax_forest.scatter(
            effects[i], y_positions[i], s=sizes[i],
            color=color, edgecolors="black", linewidths=0.8,
            zorder=5, alpha=0.9
        )

    # Pooled estimate diamond
    if pooled_effect is not None:
        p_lo = pooled_effect - 1.96 * (pooled_se if pooled_se else 0)
        p_hi = pooled_effect + 1.96 * (pooled_se if pooled_se else 0)
        diamond_y = 0.3
        diamond_x = [p_lo, pooled_effect, p_hi, pooled_effect]
        diamond_yy = [diamond_y, diamond_y + 0.3, diamond_y, diamond_y - 0.3]
        ax_forest.fill(diamond_x, diamond_yy, color="#2c3e50", alpha=0.7)
        ax_forest.text(
            pooled_effect, diamond_y - 0.6,
            f"Pooled: {pooled_effect:.3f} [{p_lo:.3f}, {p_hi:.3f}]",
            ha="center", va="top", fontsize=9, style="italic"
        )

    # Null effect line
    ax_forest.axvline(0, color="black", linewidth=0.5, linestyle="--", alpha=0.5)

    # Study labels
    ax_forest.set_yticks(y_positions)
    ax_forest.set_yticklabels(study_labels, fontsize=10)
    ax_forest.set_xlabel("Effect Size (95% CI)", fontsize=11)
    ax_forest.set_title(title, fontsize=13, fontweight="bold", pad=15)
    ax_forest.grid(True, axis="x", alpha=0.2)

    # Effect size annotations on right side of forest
    for i in range(n):
        ax_forest.text(
            ci_hi[i] + 0.01, y_positions[i],
            f"{effects[i]:.3f} [{ci_lo[i]:.3f}, {ci_hi[i]:.3f}]",
            va="center", fontsize=8, alpha=0.7
        )

    # --- Right panel: ICR bar chart (horizontal bars colored by ICR) ---
    for i in range(n):
        color = cmap(norm(icr_values[i]))
        ax_icr.barh(
            y_positions[i], icr_values[i], height=0.5,
            color=color, edgecolor="black", linewidth=0.5, alpha=0.85
        )
        ax_icr.text(
            icr_values[i] + 0.002, y_positions[i],
            f"{icr_values[i]:.3f}", va="center", fontsize=9
        )

    ax_icr.set_xlabel(icr_label, fontsize=11)
    ax_icr.set_title(f"{icr_label} Values", fontsize=12)
    ax_icr.grid(True, axis="x", alpha=0.2)

    # Colorbar
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax_icr, pad=0.15, shrink=0.6, aspect=20)
    cbar.set_label(icr_label, fontsize=10)

    # Size legend if secondary ICR
    if icr_secondary is not None:
        legend_vals = [icr_secondary.min(), np.median(icr_secondary), icr_secondary.max()]
        legend_handles = []
        for v in legend_vals:
            if sr > 0:
                s = s_min + (v - icr_secondary.min()) / sr * (s_max - s_min)
            else:
                s = (s_min + s_max) / 2
            legend_handles.append(
                ax_forest.scatter([], [], s=s, c="gray", edgecolors="black",
                                  linewidths=0.8, label=f"{icr_secondary_label}={v:.3f}")
            )
        ax_forest.legend(
            handles=legend_handles, loc="lower left",
            title=f"Point size = {icr_secondary_label}",
            fontsize=8, title_fontsize=9, framealpha=0.9
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    return output_path


def dersimonian_laird(effects, se):
    """Minimal DL meta-analysis for use in convergence simulation."""
    variances = se ** 2
    k = len(effects)
    w_fe = 1.0 / variances
    pooled_fe = np.sum(w_fe * effects) / np.sum(w_fe)
    q = np.sum(w_fe * (effects - pooled_fe) ** 2)
    c = np.sum(w_fe) - np.sum(w_fe ** 2) / np.sum(w_fe)
    tau2 = max(0, (q - (k - 1)) / c) if c > 0 else 0.0
    w_re = 1.0 / (variances + tau2)
    pooled = np.sum(w_re * effects) / np.sum(w_re)
    pooled_var = 1.0 / np.sum(w_re)
    pooled_se = np.sqrt(pooled_var)
    i_squared = max(0, (q - (k - 1)) / q * 100) if q > 0 else 0.0
    return {
        "pooled_effect": pooled,
        "pooled_se": pooled_se,
        "i_squared": i_squared,
    }


def early_convergence_simulation(
    n_iterations=500,
    n_studies_total=15,
    true_delta=0.2,
    n_per_study=80,
    output_path="fig_linko_early_convergence.png",
):
    """
    Simulate whether ICR-guided study selection can reach conclusive
    meta-analysis results with fewer studies.

    Three strategies:
    1. Random order: studies added in random order
    2. ICR-matched first: prioritize studies with similar ICR (moderate D)
    3. LINKO optimized: sort by ICR closest to median, reducing ICRD early

    Tracks how many studies are needed before 95% CI excludes zero.
    """
    results_data = {"random": [], "matched": [], "linko": []}

    for iteration in range(n_iterations):
        rng = np.random.default_rng(seed=iteration * 7 + 42)

        D_values = rng.choice([5, 10, 15, 20, 30, 40, 60], size=n_studies_total)
        icr_std = 1.0 / D_values

        effects = []
        ses = []
        for i in range(n_studies_total):
            D = int(D_values[i])
            corr = np.zeros((D, D))
            for r in range(D):
                for c in range(D):
                    corr[r, c] = 0.5 ** abs(r - c)

            mean_ctrl = np.zeros(D)
            mean_trt = np.zeros(D)
            mean_trt[0] = true_delta
            for j in range(1, D):
                mean_trt[j] = 0.3 * true_delta * corr[0, j]

            data_ctrl = rng.multivariate_normal(mean_ctrl, corr, size=n_per_study)
            data_trt = rng.multivariate_normal(mean_trt, corr, size=n_per_study)

            eff = data_trt[:, 0].mean() - data_ctrl[:, 0].mean()
            se_val = np.sqrt(
                data_trt[:, 0].var(ddof=1) / n_per_study
                + data_ctrl[:, 0].var(ddof=1) / n_per_study
            )
            effects.append(eff)
            ses.append(se_val)

        effects = np.array(effects)
        ses = np.array(ses)

        random_order = rng.permutation(n_studies_total)
        matched_order = np.argsort(np.abs(D_values - 20))
        median_icr = np.median(icr_std)
        linko_order = np.argsort(np.abs(icr_std - median_icr))

        for strategy_name, order in [
            ("random", random_order),
            ("matched", matched_order),
            ("linko", linko_order),
        ]:
            conclusive_at = None
            stable_at = None

            for k in range(2, n_studies_total + 1):
                idx = order[:k]
                eff_k = effects[idx]
                se_k = ses[idx]

                ma = dersimonian_laird(eff_k, se_k)
                pooled = ma["pooled_effect"]
                pooled_se_val = ma["pooled_se"]
                i_sq = ma["i_squared"]
                ci_lo = pooled - 1.96 * pooled_se_val
                ci_hi = pooled + 1.96 * pooled_se_val

                if conclusive_at is None and (ci_lo > 0 or ci_hi < 0):
                    conclusive_at = k
                if stable_at is None and i_sq < 25.0:
                    stable_at = k

            results_data[strategy_name].append({
                "conclusive_at": conclusive_at if conclusive_at else n_studies_total + 1,
                "stable_at": stable_at if stable_at else n_studies_total + 1,
            })

    # Summarize
    summary = {}
    for strategy in ["random", "matched", "linko"]:
        df = pd.DataFrame(results_data[strategy])
        summary[strategy] = {
            "mean_conclusive": df["conclusive_at"].mean(),
            "median_conclusive": float(df["conclusive_at"].median()),
            "pct_conclusive_by_5": float((df["conclusive_at"] <= 5).mean() * 100),
            "pct_conclusive_by_10": float((df["conclusive_at"] <= 10).mean() * 100),
            "mean_stable": df["stable_at"].mean(),
            "median_stable": float(df["stable_at"].median()),
        }

    # ---- Generate figure ----
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(
        "LINKO Early Convergence Analysis:\n"
        "Can ICR-Guided Study Selection Reach Conclusions Faster?",
        fontsize=14, fontweight="bold", y=1.02
    )

    strategy_labels = {
        "random": "Random Order",
        "matched": "ICR-Matched First",
        "linko": "LINKO Optimized",
    }
    colors = {"random": "#7f8c8d", "matched": "#3498db", "linko": "#e74c3c"}

    # Panel A: Distribution of studies needed for conclusive result
    for strategy in ["random", "matched", "linko"]:
        vals = [r["conclusive_at"] for r in results_data[strategy]]
        axes[0].hist(
            vals, bins=range(2, n_studies_total + 3), alpha=0.5,
            label=strategy_labels[strategy], color=colors[strategy],
            edgecolor="white", linewidth=0.5
        )
    axes[0].set_xlabel("Number of Studies to Conclusive Result", fontsize=11)
    axes[0].set_ylabel("Frequency", fontsize=11)
    axes[0].set_title("A. Studies Needed for Significance", fontsize=12)
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3)

    # Panel B: Cumulative probability of conclusive result
    for strategy in ["random", "matched", "linko"]:
        vals = sorted([r["conclusive_at"] for r in results_data[strategy]])
        x_vals = list(range(2, n_studies_total + 2))
        cum_prob = [sum(1 for v in vals if v <= x) / len(vals) * 100 for x in x_vals]
        axes[1].plot(
            x_vals, cum_prob, "o-", label=strategy_labels[strategy],
            color=colors[strategy], linewidth=2, markersize=4
        )
    axes[1].set_xlabel("Number of Studies Included", fontsize=11)
    axes[1].set_ylabel("Cumulative % Reaching Conclusion", fontsize=11)
    axes[1].set_title("B. Cumulative Convergence Rate", fontsize=12)
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_ylim(0, 105)

    # Panel C: Summary bar chart
    strategies = ["random", "matched", "linko"]
    x = np.arange(3)
    width = 0.35
    mean_conclusive = [summary[s]["mean_conclusive"] for s in strategies]
    mean_stable = [summary[s]["mean_stable"] for s in strategies]

    bars1 = axes[2].bar(
        x - width / 2, mean_conclusive, width,
        label="Mean studies to conclusion",
        color=[colors[s] for s in strategies], alpha=0.8,
        edgecolor="black", linewidth=0.5
    )
    bars2 = axes[2].bar(
        x + width / 2, mean_stable, width,
        label="Mean studies to I$^2$ < 25%",
        color=[colors[s] for s in strategies], alpha=0.4,
        edgecolor="black", linewidth=0.5, hatch="//"
    )

    axes[2].set_xticks(x)
    axes[2].set_xticklabels([strategy_labels[s] for s in strategies], fontsize=9)
    axes[2].set_ylabel("Mean Number of Studies", fontsize=11)
    axes[2].set_title("C. Average Studies Required", fontsize=12)
    axes[2].legend(fontsize=9)
    axes[2].grid(True, alpha=0.3, axis="y")

    for bar, val in zip(bars1, mean_conclusive):
        axes[2].text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
            f"{val:.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold"
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()

    return {"summary": summary, "figure_path": output_path}


def generate_all_linko_figures(output_dir="icr_paper/figures"):
    """Generate all LINKO visualization figures."""
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    # --- 1. Statin Prism Forest Plot ---
    statin_effects = np.array([-0.370, -0.250, -0.100, -0.250, -0.110])
    statin_se = np.array([0.08, 0.07, 0.06, 0.05, 0.05])
    statin_icr_std = np.array([0.100, 0.100, 0.091, 0.100, 0.100])
    statin_labels = ["4S (1994)", "WOSCOPS (1995)", "CARE (1996)",
                     "LIPID (1998)", "AFCAPS (1998)"]

    p1 = prism_forest_plot(
        effects=statin_effects, se=statin_se,
        icr_values=statin_icr_std, study_labels=statin_labels,
        icr_label="ICR$_{std}$", pooled_effect=-0.251, pooled_se=0.057,
        title="LINKO Prism Forest Plot: Statin Therapy\n(Low ICRD = 0.009, I$^2$ = 0%)",
        output_path=os.path.join(output_dir, "fig_linko_prism_statin.png"),
    )
    results["statin_prism"] = p1
    print(f"  Statin Prism Forest Plot: {p1}")

    # --- 2. Glucose Control Prism Forest Plot ---
    glucose_effects = np.array([-0.060, +0.220, -0.070, -0.020])
    glucose_se = np.array([0.05, 0.06, 0.04, 0.10])
    glucose_icr_std = np.array([0.125, 0.077, 0.083, 0.083])
    glucose_labels = ["UKPDS 33 (1998)", "ACCORD (2008)",
                      "ADVANCE (2008)", "VADT (2009)"]

    p2 = prism_forest_plot(
        effects=glucose_effects, se=glucose_se,
        icr_values=glucose_icr_std, study_labels=glucose_labels,
        icr_label="ICR$_{std}$", pooled_effect=-0.003, pooled_se=0.065,
        title="LINKO Prism Forest Plot: Intensive Glucose Control\n(High ICRD = 0.048, I$^2$ = 17%)",
        output_path=os.path.join(output_dir, "fig_linko_prism_glucose.png"),
    )
    results["glucose_prism"] = p2
    print(f"  Glucose Prism Forest Plot: {p2}")

    # --- 3. IST Prism Forest Plot (color=ICR_pca, size=ICR_pca_reg) ---
    ist_mortality = np.array([0.286, 0.200, 0.231, 0.296, 0.183, 0.127, 0.150, 0.218])
    # Use mortality as "effect" (event rate), SE from binomial
    ist_n = np.array([5787, 3112, 1631, 759, 728, 636, 568, 545])
    ist_se = np.sqrt(ist_mortality * (1 - ist_mortality) / ist_n)
    ist_icr_pca_loading = np.array([0.138, 0.046, 0.121, 0.139, 0.180, 0.096, 0.109, 0.079])
    ist_icr_pca_reg = np.array([0.00162, 0.00153, 0.00135, 0.00230, 0.00136, 0.00073, 0.00096, 0.00157])
    ist_labels = ["UK (n=5787)", "Italy (n=3112)", "Switzerland (n=1631)",
                  "Poland (n=759)", "Netherlands (n=728)", "Sweden (n=636)",
                  "Australia (n=568)", "Argentina (n=545)"]

    p3 = prism_forest_plot(
        effects=ist_mortality, se=ist_se,
        icr_values=ist_icr_pca_loading, study_labels=ist_labels,
        icr_label="ICR$_{pca}$ (loading)",
        pooled_effect=np.average(ist_mortality, weights=ist_n),
        pooled_se=0.003,
        title="LINKO Prism Forest Plot: IST Country Sub-Studies\n"
              "(color = ICR$_{pca}$ loading, size = ICR$_{pca}$ regression)",
        output_path=os.path.join(output_dir, "fig_linko_prism_ist.png"),
        icr_secondary=ist_icr_pca_reg,
        icr_secondary_label="ICR$_{pca,reg}$",
    )
    results["ist_prism"] = p3
    print(f"  IST Prism Forest Plot: {p3}")

    # --- 4. Early Convergence Analysis ---
    print("  Running early convergence simulation (500 iterations)...")
    conv_result = early_convergence_simulation(
        n_iterations=500,
        output_path=os.path.join(output_dir, "fig_linko_early_convergence.png"),
    )
    results["early_convergence"] = conv_result
    print(f"  Early Convergence figure: {conv_result['figure_path']}")

    return results


if __name__ == "__main__":
    print("=== Generating LINKO Figures ===")
    results = generate_all_linko_figures()
    print("\n=== Summary ===")
    if "early_convergence" in results:
        ec = results["early_convergence"]["summary"]
        for strategy, s in ec.items():
            print(f"\n  {strategy}:")
            for k, v in s.items():
                print(f"    {k}: {v:.2f}")
    print("\nDone.")

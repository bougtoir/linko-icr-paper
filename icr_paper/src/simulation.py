"""
Simulation study for ICR (Information Contribution Ratio) research.

Generates synthetic RCT data with controlled ICR values to demonstrate
how ICR discrepancies across studies affect meta-analysis heterogeneity.

Key mechanism: The treatment operates through a latent factor that affects
multiple dimensions. The endpoint captures only a fraction of this effect.
When studies have different dimensionalities (different ICR), the endpoint's
marginal effect size changes due to different correlation structures,
creating genuine heterogeneity in meta-analysis.
"""

import numpy as np
import pandas as pd
from typing import Optional
from .icr_calculator import compute_icr_v_from_dataframe
from .meta_analysis import (
    dersimonian_laird_meta,
    sequential_meta_analysis,
    icr_weighted_meta,
)


def generate_rct_data(
    n_subjects: int,
    n_dimensions: int,
    endpoint_indices: list[int],
    true_effect: float,
    spillover_fraction: float = 0.0,
    covariance_strength: float = 0.3,
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Generate synthetic RCT data with controlled properties.

    The treatment affects the endpoint directly with effect `true_effect`.
    Additionally, a fraction of the treatment effect "spills over" to other
    dimensions (proportional to their correlation with the endpoint).
    Through the multivariate correlation structure, these spillover effects
    feed back into the observed marginal endpoint effect.

    When spillover_fraction > 0 and D varies across studies, this creates
    genuine heterogeneity in the observed effect sizes because:
    - More dimensions → more spillover channels → different marginal effect
    - Different correlation structures → different indirect contributions

    Parameters
    ----------
    n_subjects : int
        Total number of subjects (split equally between groups).
    n_dimensions : int
        Total number of variables (including endpoints).
    endpoint_indices : list of int
        Indices of endpoint variables (0-based).
    true_effect : float
        True direct treatment effect (standardized) on endpoints.
    spillover_fraction : float
        Fraction of the treatment effect that spills over to correlated
        non-endpoint dimensions. 0 = no spillover (classic model),
        1 = full proportional spillover.
    covariance_strength : float
        Strength of correlations between variables (0 = independent).
    seed : int, optional
        Random seed.

    Returns
    -------
    pd.DataFrame with columns: group, var_0, var_1, ..., var_{D-1}
    """
    rng = np.random.default_rng(seed)

    n_per_group = n_subjects // 2

    # Build covariance matrix with structured correlations
    cov = np.eye(n_dimensions)
    for i in range(n_dimensions):
        for j in range(i + 1, n_dimensions):
            rho = covariance_strength * rng.uniform(0.1, 1.0)
            cov[i, j] = rho
            cov[j, i] = rho

    # Ensure positive definiteness
    eigvals = np.linalg.eigvalsh(cov)
    if eigvals.min() <= 0:
        cov += (abs(eigvals.min()) + 0.01) * np.eye(n_dimensions)

    # Generate control group
    mean_control = np.zeros(n_dimensions)
    data_control = rng.multivariate_normal(mean_control, cov, size=n_per_group)

    # Generate intervention group
    mean_intervention = np.zeros(n_dimensions)
    for idx in endpoint_indices:
        mean_intervention[idx] = true_effect * np.sqrt(cov[idx, idx])

    # Spillover: treatment also affects non-endpoint dimensions
    # proportional to their correlation with endpoints
    if spillover_fraction > 0:
        ep_set = set(endpoint_indices)
        for idx in endpoint_indices:
            for j in range(n_dimensions):
                if j not in ep_set:
                    rho_ej = cov[idx, j] / np.sqrt(cov[idx, idx] * cov[j, j])
                    mean_intervention[j] += (
                        spillover_fraction * true_effect
                        * rho_ej * np.sqrt(cov[j, j])
                    )

    data_intervention = rng.multivariate_normal(
        mean_intervention, cov, size=n_per_group
    )

    # Combine
    data = np.vstack([data_control, data_intervention])
    groups = np.array(["control"] * n_per_group + ["intervention"] * n_per_group)

    col_names = [f"var_{i}" for i in range(n_dimensions)]
    df = pd.DataFrame(data, columns=col_names)
    df.insert(0, "group", groups)

    return df


def compute_study_effect_size(
    df: pd.DataFrame,
    endpoint_col: str,
    group_col: str = "group",
    intervention_label: str = "intervention",
    control_label: str = "control",
) -> tuple[float, float]:
    """Compute standardized mean difference (Cohen's d) and its variance.

    Parameters
    ----------
    df : pd.DataFrame
    endpoint_col : str
    group_col, intervention_label, control_label : str

    Returns
    -------
    d : float
        Cohen's d (standardized mean difference).
    var_d : float
        Variance of d.
    """
    intervention = df[df[group_col] == intervention_label][endpoint_col]
    control = df[df[group_col] == control_label][endpoint_col]

    n_i = len(intervention)
    n_c = len(control)
    mean_i = intervention.mean()
    mean_c = control.mean()
    sd_pooled = np.sqrt(
        ((n_i - 1) * intervention.var(ddof=1) + (n_c - 1) * control.var(ddof=1))
        / (n_i + n_c - 2)
    )

    d = (mean_i - mean_c) / sd_pooled if sd_pooled > 0 else 0.0

    # Variance of d (Hedges' approximation)
    var_d = (n_i + n_c) / (n_i * n_c) + d ** 2 / (2 * (n_i + n_c))

    return d, var_d


def run_simulation_scenario(
    n_studies: int,
    n_subjects_per_study: int,
    dimensions_per_study: list[int],
    endpoint_indices_per_study: list[list[int]],
    true_effect: float,
    endpoint_variance_scales: list[float],
    covariance_strength: float = 0.3,
    spillover_fraction: float = 0.0,
    seed: Optional[int] = None,
) -> dict:
    """Run a single simulation scenario.

    Parameters
    ----------
    n_studies : int
        Number of RCTs to simulate.
    n_subjects_per_study : int
        Subjects per study.
    dimensions_per_study : list of int
        Dimensionality of each study.
    endpoint_indices_per_study : list of list of int
        Endpoint variable indices for each study.
    true_effect : float
        True effect size.
    endpoint_variance_scales : list of float
        Variance scale for endpoints in each study.
    covariance_strength : float
        Correlation strength.
    seed : int, optional

    Returns
    -------
    dict with study-level results, meta-analysis results, ICR values.
    """
    rng = np.random.default_rng(seed)

    effects = []
    variances = []
    icr_values = []
    study_details = []

    for i in range(n_studies):
        study_seed = rng.integers(0, 2**31)

        df = generate_rct_data(
            n_subjects=n_subjects_per_study,
            n_dimensions=dimensions_per_study[i],
            endpoint_indices=endpoint_indices_per_study[i],
            true_effect=true_effect,
            spillover_fraction=spillover_fraction,
            covariance_strength=covariance_strength,
            seed=study_seed,
        )

        # Compute effect size for first endpoint
        ep_col = f"var_{endpoint_indices_per_study[i][0]}"
        d, var_d = compute_study_effect_size(df, ep_col)

        # Compute ICR
        endpoint_cols = [f"var_{idx}" for idx in endpoint_indices_per_study[i]]
        icr_result = compute_icr_v_from_dataframe(
            df, endpoint_cols, group_col="group"
        )
        icr_std = icr_result["icr_std"]
        icr_raw = icr_result["icr_raw"]

        effects.append(d)
        variances.append(var_d)
        icr_values.append(icr_std)
        study_details.append({
            "study_id": i + 1,
            "n_subjects": n_subjects_per_study,
            "n_dimensions": dimensions_per_study[i],
            "n_endpoints": len(endpoint_indices_per_study[i]),
            "endpoint_variance_scale": endpoint_variance_scales[i],
            "effect_size_d": d,
            "var_d": var_d,
            "icr_std": icr_std,
            "icr_raw": icr_raw,
        })

    effects = np.array(effects)
    variances = np.array(variances)
    icr_values = np.array(icr_values)

    # Standard meta-analysis
    meta_result = dersimonian_laird_meta(effects, variances)

    # ICR-weighted meta-analysis
    icr_meta_result = icr_weighted_meta(effects, variances, icr_values)

    # Sequential meta-analysis
    seq_result = sequential_meta_analysis(effects, variances, icr_values)

    return {
        "study_details": pd.DataFrame(study_details),
        "meta_analysis": meta_result,
        "icr_weighted_meta": icr_meta_result,
        "sequential_meta": seq_result,
        "effects": effects,
        "variances": variances,
        "icr_values": icr_values,
        "true_effect": true_effect,
    }


def scenario_a_uniform_icr(
    n_studies: int = 10,
    n_subjects: int = 200,
    n_dimensions: int = 20,
    true_effect: float = 0.5,
    spillover_fraction: float = 0.3,
    seed: Optional[int] = None,
) -> dict:
    """Scenario A: All studies have similar ICR (uniform dimensions and structure).

    All studies measure the same number of dimensions with the same structure.
    Expected: low heterogeneity, stable meta-analysis.
    """
    return run_simulation_scenario(
        n_studies=n_studies,
        n_subjects_per_study=n_subjects,
        dimensions_per_study=[n_dimensions] * n_studies,
        endpoint_indices_per_study=[[0]] * n_studies,
        true_effect=true_effect,
        endpoint_variance_scales=[1.0] * n_studies,
        spillover_fraction=spillover_fraction,
        seed=seed,
    )


def scenario_b_heterogeneous_icr(
    n_studies: int = 10,
    n_subjects: int = 200,
    true_effect: float = 0.5,
    spillover_fraction: float = 0.3,
    seed: Optional[int] = None,
) -> dict:
    """Scenario B: Studies have varying ICR (different dimensions and structures).

    Studies measure different numbers of variables → different ICR values.
    With spillover > 0, the different data structures lead to different
    observed marginal effects, creating genuine heterogeneity.
    Expected: increased heterogeneity compared to Scenario A.
    """
    rng = np.random.default_rng(seed)

    # Varying dimensions: some studies measure many variables, some few
    dimensions = rng.choice([5, 10, 20, 40, 80], size=n_studies).tolist()

    # Endpoint variance scales uniform (variation comes from D)
    ep_var_scales = [1.0] * n_studies

    return run_simulation_scenario(
        n_studies=n_studies,
        n_subjects_per_study=n_subjects,
        dimensions_per_study=dimensions,
        endpoint_indices_per_study=[[0]] * n_studies,
        true_effect=true_effect,
        endpoint_variance_scales=ep_var_scales,
        spillover_fraction=spillover_fraction,
        seed=seed,
    )


def scenario_c_sequential(
    n_initial: int = 5,
    n_additional: int = 10,
    n_subjects: int = 200,
    true_effect: float = 0.5,
    spillover_fraction: float = 0.3,
    seed: Optional[int] = None,
) -> dict:
    """Scenario C: Sequential meta-analysis with ICR shift.

    First n_initial studies have uniform ICR (consistent results).
    Then n_additional studies with heterogeneous ICR are added.

    Expected: initial stability, then increased heterogeneity.
    This mimics the real-world pattern: "5 RCTs agree, then 10 more add
    heterogeneity" because the later studies have different data structures.
    """
    rng = np.random.default_rng(seed)
    n_total = n_initial + n_additional

    # Initial studies: uniform D=20 (ICR_std = 1/20 = 0.05)
    dims_initial = [20] * n_initial
    scales_initial = [1.0] * n_initial

    # Additional studies: heterogeneous dimensions
    dims_additional = rng.choice([5, 10, 40, 60, 80], size=n_additional).tolist()
    scales_additional = [1.0] * n_additional

    dimensions = dims_initial + dims_additional
    scales = scales_initial + scales_additional

    return run_simulation_scenario(
        n_studies=n_total,
        n_subjects_per_study=n_subjects,
        dimensions_per_study=dimensions,
        endpoint_indices_per_study=[[0]] * n_total,
        true_effect=true_effect,
        endpoint_variance_scales=scales,
        spillover_fraction=spillover_fraction,
        seed=seed,
    )


def run_full_simulation(
    n_iterations: int = 1000,
    seed: int = 42,
) -> dict:
    """Run the complete simulation study across all scenarios.

    Parameters
    ----------
    n_iterations : int
        Number of Monte Carlo iterations per scenario.
    seed : int

    Returns
    -------
    dict with aggregated results for each scenario.
    """
    rng = np.random.default_rng(seed)
    results = {"A": [], "B": [], "C": []}

    for i in range(n_iterations):
        iter_seed = rng.integers(0, 2**31)

        # Scenario A
        res_a = scenario_a_uniform_icr(seed=iter_seed)
        results["A"].append({
            "iteration": i,
            "pooled_effect": res_a["meta_analysis"]["pooled_effect"],
            "i_squared": res_a["meta_analysis"]["i_squared"],
            "tau_squared": res_a["meta_analysis"]["tau_squared"],
            "icr_mean": np.mean(res_a["icr_values"]),
            "icr_sd": np.std(res_a["icr_values"]),
            "icrd": np.max(res_a["icr_values"]) - np.min(res_a["icr_values"]),
        })

        # Scenario B
        res_b = scenario_b_heterogeneous_icr(seed=iter_seed + 1)
        results["B"].append({
            "iteration": i,
            "pooled_effect": res_b["meta_analysis"]["pooled_effect"],
            "i_squared": res_b["meta_analysis"]["i_squared"],
            "tau_squared": res_b["meta_analysis"]["tau_squared"],
            "icr_mean": np.mean(res_b["icr_values"]),
            "icr_sd": np.std(res_b["icr_values"]),
            "icrd": np.max(res_b["icr_values"]) - np.min(res_b["icr_values"]),
        })

        # Scenario C
        res_c = scenario_c_sequential(seed=iter_seed + 2)
        seq = res_c["sequential_meta"]
        results["C"].append({
            "iteration": i,
            "initial_i_squared": seq.iloc[3]["i_squared"] if len(seq) > 3 else np.nan,
            "final_i_squared": seq.iloc[-1]["i_squared"],
            "initial_icr_cv": seq.iloc[3]["icr_cv"] if len(seq) > 3 and "icr_cv" in seq.columns else np.nan,
            "final_icr_cv": seq.iloc[-1]["icr_cv"] if "icr_cv" in seq.columns else np.nan,
            "i_squared_change": (
                seq.iloc[-1]["i_squared"] - (seq.iloc[3]["i_squared"] if len(seq) > 3 else 0)
            ),
        })

    return {
        "A": pd.DataFrame(results["A"]),
        "B": pd.DataFrame(results["B"]),
        "C": pd.DataFrame(results["C"]),
    }


def run_quick_simulation(
    n_iterations: int = 100,
    seed: int = 42,
) -> dict:
    """Run a quick version of the simulation for testing (fewer iterations)."""
    return run_full_simulation(n_iterations=n_iterations, seed=seed)

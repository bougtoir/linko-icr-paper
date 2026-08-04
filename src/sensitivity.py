"""Sensitivity analyses requested by peer review.

Contains:
* alternative between-study variance estimators (DerSimonian-Laird, REML,
  Paule-Mandel) with Hartung-Knapp intervals and prediction intervals;
* Monte Carlo standard errors for simulation summaries;
* a negative-control simulation (ICR varies, no structural mechanism);
* a redundant-variable simulation (D inflated by copies of existing
  variables) probing the fragility of ICR_std = d/D.
"""

import numpy as np
import pandas as pd
from scipy import stats

from .icr_calculator import compute_icr_v_from_dataframe
from .meta_analysis import dersimonian_laird_meta
from .simulation import compute_study_effect_size, generate_rct_data


# ----------------------------------------------------------------------
# Between-study variance estimators
# ----------------------------------------------------------------------
def _pooled(effects, variances, tau2):
    w = 1.0 / (variances + tau2)
    mu = np.sum(w * effects) / np.sum(w)
    se = np.sqrt(1.0 / np.sum(w))
    return mu, se, w


def tau2_dersimonian_laird(effects, variances):
    k = len(effects)
    w = 1.0 / variances
    mu = np.sum(w * effects) / np.sum(w)
    q = np.sum(w * (effects - mu) ** 2)
    c = np.sum(w) - np.sum(w**2) / np.sum(w)
    return max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0


def tau2_paule_mandel(effects, variances, tol=1e-10, max_iter=200):
    """Paule-Mandel estimator: solve generalised Q(tau2) = k - 1."""
    k = len(effects)
    if k < 2:
        return 0.0

    def q_stat(tau2):
        mu, _, w = _pooled(effects, variances, tau2)
        return np.sum(w * (effects - mu) ** 2)

    if q_stat(0.0) <= k - 1:
        return 0.0
    lo, hi = 0.0, max(variances) + np.var(effects, ddof=1) + 1.0
    while q_stat(hi) > k - 1 and hi < 1e6:
        hi *= 2
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        if q_stat(mid) > k - 1:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def tau2_reml(effects, variances, tol=1e-10, max_iter=500):
    """REML estimator via fixed-point iteration."""
    k = len(effects)
    if k < 2:
        return 0.0
    tau2 = max(0.0, np.var(effects, ddof=1) - np.mean(variances))
    for _ in range(max_iter):
        w = 1.0 / (variances + tau2)
        mu = np.sum(w * effects) / np.sum(w)
        num = np.sum(w**2 * ((effects - mu) ** 2 + 1.0 / np.sum(w) - variances))
        den = np.sum(w**2)
        new = max(0.0, num / den)
        if abs(new - tau2) < tol:
            tau2 = new
            break
        tau2 = new
    return tau2


def meta_with_tau2(effects, variances, tau2, hartung_knapp=False):
    """Random-effects pooling for a given tau2, optionally Hartung-Knapp."""
    effects = np.asarray(effects, dtype=float)
    variances = np.asarray(variances, dtype=float)
    k = len(effects)
    mu, se, w = _pooled(effects, variances, tau2)

    if hartung_knapp and k > 1:
        q_gen = np.sum(w * (effects - mu) ** 2) / (k - 1)
        se = se * np.sqrt(q_gen)
        crit = stats.t.ppf(0.975, df=k - 1)
    else:
        crit = stats.norm.ppf(0.975)

    q0 = np.sum((1.0 / variances) * (effects - np.sum(effects / variances) / np.sum(1.0 / variances)) ** 2)
    i2 = max(0.0, (q0 - (k - 1)) / q0 * 100) if q0 > 0 else 0.0

    out = {
        "tau_squared": tau2,
        "pooled_effect": mu,
        "pooled_se": se,
        "ci_lower": mu - crit * se,
        "ci_upper": mu + crit * se,
        "i_squared": i2,
    }
    if k > 2:
        t_crit = stats.t.ppf(0.975, df=k - 2)
        pred_se = np.sqrt(se**2 + tau2)
        out["pi_lower"] = mu - t_crit * pred_se
        out["pi_upper"] = mu + t_crit * pred_se
    else:
        out["pi_lower"] = out["pi_upper"] = np.nan
    return out


def meta_sensitivity_table(effects, variances) -> pd.DataFrame:
    """Pooled effect under DL / REML / Paule-Mandel, with and without HK."""
    effects = np.asarray(effects, dtype=float)
    variances = np.asarray(variances, dtype=float)
    estimators = {
        "DerSimonian-Laird": tau2_dersimonian_laird(effects, variances),
        "REML": tau2_reml(effects, variances),
        "Paule-Mandel": tau2_paule_mandel(effects, variances),
    }
    rows = []
    for name, tau2 in estimators.items():
        for hk in (False, True):
            res = meta_with_tau2(effects, variances, tau2, hartung_knapp=hk)
            rows.append(
                {
                    "tau2_estimator": name,
                    "interval": "Hartung-Knapp" if hk else "Wald",
                    **res,
                }
            )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Monte Carlo standard errors
# ----------------------------------------------------------------------
def monte_carlo_se(values: np.ndarray) -> dict:
    """Mean, SD and Monte Carlo SE of a simulation performance measure."""
    values = np.asarray(values, dtype=float)
    n = len(values)
    sd = values.std(ddof=1)
    return {
        "mean": values.mean(),
        "sd": sd,
        "mcse": sd / np.sqrt(n),
        "n_iterations": n,
    }


def difference_mcse(a: np.ndarray, b: np.ndarray) -> dict:
    """Paired difference (a - b) with its Monte Carlo SE."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n = min(len(a), len(b))
    diff = a[:n] - b[:n]
    sd = diff.std(ddof=1)
    mcse = sd / np.sqrt(n)
    return {
        "mean_difference": diff.mean(),
        "sd": sd,
        "mcse": mcse,
        "ci_lower": diff.mean() - 1.96 * mcse,
        "ci_upper": diff.mean() + 1.96 * mcse,
        "n_iterations": n,
    }


# ----------------------------------------------------------------------
# Negative control: ICR varies but no structural mechanism (no spillover)
# ----------------------------------------------------------------------
def negative_control_simulation(
    n_iterations: int = 200,
    n_studies: int = 10,
    n_subjects: int = 200,
    true_effect: float = 0.5,
    dimensions=(5, 10, 20, 40, 80),
    seed: int = 42,
) -> pd.DataFrame:
    """Studies differ in D (hence in ICR_std) but the treatment acts only on
    the endpoint, so no structural heterogeneity should be induced."""
    rng = np.random.default_rng(seed)
    rows = []
    for it in range(n_iterations):
        dims = rng.choice(dimensions, size=n_studies)
        effects, variances, icrs = [], [], []
        for d in dims:
            df = generate_rct_data(
                n_subjects=n_subjects,
                n_dimensions=int(d),
                endpoint_indices=[0],
                true_effect=true_effect,
                spillover_fraction=0.0,
                seed=int(rng.integers(0, 2**31)),
            )
            eff, var = compute_study_effect_size(df, "var_0")
            effects.append(eff)
            variances.append(var)
            icrs.append(1.0 / int(d))
        meta = dersimonian_laird_meta(np.array(effects), np.array(variances))
        rows.append(
            {
                "iteration": it,
                "i_squared": meta["i_squared"],
                "tau_squared": meta["tau_squared"],
                "pooled_effect": meta["pooled_effect"],
                "icrd": max(icrs) - min(icrs),
            }
        )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# Redundant variables: how fragile is ICR_std = d/D?
# ----------------------------------------------------------------------
def redundant_variable_simulation(
    n_iterations: int = 200,
    n_subjects: int = 400,
    n_base_variables: int = 20,
    duplication_factors=(0, 5, 10, 20),
    noise_sd: float = 0.05,
    seed: int = 42,
) -> pd.DataFrame:
    """Add near-duplicate copies of existing covariates to a single study.

    The information content of the data is essentially unchanged, but D grows,
    so ICR_std = d/D shrinks mechanically. Reported alongside the
    variance-ratio ICR and an eigenvalue-based effective dimensionality
    (participation ratio) that is insensitive to duplication.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for it in range(n_iterations):
        base = generate_rct_data(
            n_subjects=n_subjects,
            n_dimensions=n_base_variables,
            endpoint_indices=[0],
            true_effect=0.5,
            spillover_fraction=0.3,
            seed=int(rng.integers(0, 2**31)),
        )
        for extra in duplication_factors:
            df = base.copy()
            for j in range(extra):
                src = f"var_{1 + j % (n_base_variables - 1)}"
                df[f"dup_{j}"] = df[src] + rng.normal(0, noise_sd, len(df))
            icr = compute_icr_v_from_dataframe(df, ["var_0"], group_col="group")
            values = df.drop(columns=["group"]).to_numpy(dtype=float)
            corr = np.corrcoef(values, rowvar=False)
            eig = np.linalg.eigvalsh(corr)
            eig = np.clip(eig, 0, None)
            effective_dim = eig.sum() ** 2 / np.sum(eig**2)
            rows.append(
                {
                    "iteration": it,
                    "n_redundant": extra,
                    "n_variables": int(icr["n_variables_used"]),
                    "icr_std": icr["icr_std"],
                    "icr_raw": icr["icr_raw"],
                    "effective_dimension": effective_dim,
                    "icr_effective": 1.0 / effective_dim,
                }
            )
    return pd.DataFrame(rows)

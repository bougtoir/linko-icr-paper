#!/usr/bin/env python3
"""LINKO analysis pipeline.

Runs every analysis reported in the manuscript and writes each number to
``results/`` (CSV tables plus ``results/results.json``). The manuscript
builders (``generate_docx.py``, ``generate_pptx.py``) read only those files,
so no result value is ever written as a literal in a manuscript script.

Usage
-----
    python run_analysis.py [--iterations 1000] [--convergence-iterations 500]

The IST individual patient data must be downloaded first::

    bash scripts/download_ist.sh
"""

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

from icr_paper.src.data_io import DATA_DIR
from icr_paper.src.ist_pca_analysis import (
    DEFAULT_IST_PATH,
    run_ist_pca_analysis,
)
from icr_paper.src.ist_sensitivity import (
    generate_loo_figure,
    leave_one_out_correlations,
    size_adjusted_association,
)
from icr_paper.src.linko_visualizations import generate_all_linko_figures
from icr_paper.src.real_world_analysis import run_real_world_analyses
from icr_paper.src.sensitivity import (
    difference_mcse,
    meta_sensitivity_table,
    monte_carlo_se,
    negative_control_simulation,
    redundant_variable_simulation,
)
from icr_paper.src.simulation import run_full_simulation
from icr_paper.src.visualization import generate_all_figures

RESULTS_DIR = BASE / "results"
FIGURE_DIR = BASE / "figures"

SIMULATION_SETTINGS = {
    "n_studies_scenario_ab": 10,
    "n_studies_scenario_c_initial": 5,
    "n_studies_scenario_c_additional": 10,
    "n_subjects_per_study": 200,
    "true_effect": 0.5,
    "spillover_fraction": 0.3,
    "dimensions_scenario_a": 20,
    "dimensions_scenario_b": [5, 10, 20, 40, 80],
    "dimensions_scenario_c_additional": [5, 10, 40, 60, 80],
    "seed": 42,
}
CONVERGENCE_SETTINGS = {
    "n_studies_total": 15,
    "true_delta": 0.2,
    "n_per_arm": 80,
    "dimensions": [5, 10, 15, 20, 30, 40, 60],
    "i_squared_threshold": 25.0,
}
LOADING_THRESHOLD = 0.3


def _json_safe(obj):
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return [_json_safe(v) for v in obj.tolist()]
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    return obj


def _relative(obj):
    """Rewrite absolute paths under the repository as relative ones.

    Keeps results.json identical between machines so that a clean rerun can be
    compared directly against the committed results.
    """
    if isinstance(obj, dict):
        return {k: _relative(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_relative(v) for v in obj]
    if isinstance(obj, str) and obj.startswith(str(BASE) + "/"):
        return obj[len(str(BASE)) + 1 :]
    return obj


def _write_table(df: pd.DataFrame, name: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_DIR / name, index=False)


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(BASE), text=True
        ).strip()
    except Exception:
        return "unknown"


def run_simulation_block(n_iterations: int) -> dict:
    sim = run_full_simulation(n_iterations=n_iterations, seed=SIMULATION_SETTINGS["seed"])
    for scenario, df in sim.items():
        _write_table(df, f"simulation_scenario_{scenario.lower()}.csv")

    a, b, c = sim["A"], sim["B"], sim["C"]
    icrd_all = np.concatenate([a["icrd"], b["icrd"]])
    i2_all = np.concatenate([a["i_squared"], b["i_squared"]])
    r_icrd_i2, p_icrd_i2 = stats.pearsonr(icrd_all, i2_all)

    block = {
        "n_iterations": n_iterations,
        "settings": SIMULATION_SETTINGS,
        "scenario_a": {
            "i_squared": monte_carlo_se(a["i_squared"]),
            "icrd": monte_carlo_se(a["icrd"]),
            "pooled_effect": monte_carlo_se(a["pooled_effect"]),
            "tau_squared": monte_carlo_se(a["tau_squared"]),
            "bias": monte_carlo_se(a["pooled_effect"] - SIMULATION_SETTINGS["true_effect"]),
        },
        "scenario_b": {
            "i_squared": monte_carlo_se(b["i_squared"]),
            "icrd": monte_carlo_se(b["icrd"]),
            "pooled_effect": monte_carlo_se(b["pooled_effect"]),
            "tau_squared": monte_carlo_se(b["tau_squared"]),
            "bias": monte_carlo_se(b["pooled_effect"] - SIMULATION_SETTINGS["true_effect"]),
        },
        "difference_b_minus_a": {
            "i_squared": difference_mcse(b["i_squared"], a["i_squared"]),
            "tau_squared": difference_mcse(b["tau_squared"], a["tau_squared"]),
        },
        "scenario_c": {
            "i_squared_change": monte_carlo_se(c["i_squared_change"]),
            "proportion_increased": float((c["i_squared_change"] > 0).mean()),
            "proportion_increased_se": float(
                np.sqrt(
                    (c["i_squared_change"] > 0).mean()
                    * (1 - (c["i_squared_change"] > 0).mean())
                    / len(c)
                )
            ),
        },
        "correlation_icrd_i_squared": {"r": float(r_icrd_i2), "p": float(p_icrd_i2)},
    }
    return block


def run_negative_control_block(n_iterations: int) -> dict:
    df = negative_control_simulation(n_iterations=n_iterations)
    _write_table(df, "simulation_negative_control.csv")
    return {
        "n_iterations": int(len(df)),
        "i_squared": monte_carlo_se(df["i_squared"]),
        "tau_squared": monte_carlo_se(df["tau_squared"]),
        "icrd": monte_carlo_se(df["icrd"]),
    }


def run_redundancy_block(n_iterations: int) -> dict:
    df = redundant_variable_simulation(n_iterations=n_iterations)
    summary = (
        df.groupby("n_redundant")
        .agg(
            n_variables=("n_variables", "mean"),
            icr_std=("icr_std", "mean"),
            icr_raw=("icr_raw", "mean"),
            effective_dimension=("effective_dimension", "mean"),
            icr_effective=("icr_effective", "mean"),
        )
        .reset_index()
    )
    _write_table(df, "simulation_redundant_variables_raw.csv")
    _write_table(summary, "simulation_redundant_variables.csv")
    base = summary.iloc[0]
    top = summary.iloc[-1]
    return {
        "n_iterations": n_iterations,
        "summary": summary.to_dict(orient="records"),
        "icr_std_ratio_max_to_base": float(top["icr_std"] / base["icr_std"]),
        "icr_effective_ratio_max_to_base": float(
            top["icr_effective"] / base["icr_effective"]
        ),
    }


def run_real_world_block() -> tuple[dict, dict]:
    rw = run_real_world_analyses()
    block = {}
    for tag, result in rw.items():
        df = result["study_results"]
        _write_table(
            df[
                [
                    "study",
                    "n_total",
                    "n_variables",
                    "n_endpoints",
                    "icr_std",
                    "icr_raw",
                    "effect_size",
                    "effect_var",
                ]
            ],
            f"realworld_{tag}_studies.csv",
        )
        sens = meta_sensitivity_table(
            df["effect_size"].to_numpy(), df["effect_var"].to_numpy()
        )
        _write_table(sens, f"realworld_{tag}_meta_sensitivity.csv")
        _write_table(result["sequential_meta"], f"realworld_{tag}_sequential.csv")

        block[tag] = {
            "description": result["description"],
            "n_studies": int(len(df)),
            "meta_analysis": _json_safe(
                {k: v for k, v in result["meta_analysis"].items() if k != "weights"}
            ),
            "icr_statistics": _json_safe(
                {k: v for k, v in result["icr_statistics"].items() if k != "icr_values"}
            ),
            "icr_std_range": [float(df["icr_std"].min()), float(df["icr_std"].max())],
            "icr_raw_range": [float(df["icr_raw"].min()), float(df["icr_raw"].max())],
            "n_variables_range": [int(df["n_variables"].min()), int(df["n_variables"].max())],
            "correlation_icr_effect": _json_safe(result["correlation"]),
            "studies": _json_safe(df.drop(columns=["unusable"]).to_dict(orient="records")),
            "meta_sensitivity": _json_safe(sens.to_dict(orient="records")),
        }
    return rw, block


def run_ist_block() -> tuple[dict, dict]:
    if not Path(DEFAULT_IST_PATH).exists():
        raise SystemExit(
            f"IST data not found at {DEFAULT_IST_PATH}.\n"
            "Run: bash scripts/download_ist.sh"
        )
    ist = run_ist_pca_analysis()
    res_df = ist["country_results"]
    _write_table(res_df, "ist_country_results.csv")

    loo = leave_one_out_correlations(res_df)
    _write_table(loo, "ist_leave_one_out.csv")
    loo_figure = generate_loo_figure(loo)

    excl = loo[~loo["excluded_country"].str.startswith("None")]
    block = {
        "summary": _json_safe(ist["summary"]),
        "loading_threshold": LOADING_THRESHOLD,
        "countries": _json_safe(res_df.to_dict(orient="records")),
        "leave_one_out": _json_safe(loo.to_dict(orient="records")),
        "loo_ranges": {
            "r_loading": [float(excl["r_loading"].min()), float(excl["r_loading"].max())],
            "p_loading": [float(excl["p_loading"].min()), float(excl["p_loading"].max())],
            "r_regression": [
                float(excl["r_regression"].min()),
                float(excl["r_regression"].max()),
            ],
            "p_regression": [
                float(excl["p_regression"].min()),
                float(excl["p_regression"].max()),
            ],
        },
        "figures": {"pca": ist["figure_path"], "loo": loo_figure},
        "size_adjusted": size_adjusted_association(res_df),
    }
    # correlation p-values for the full set
    full = loo[loo["excluded_country"].str.startswith("None")].iloc[0]
    block["correlation_full"] = {
        "r_loading": float(full["r_loading"]),
        "p_loading": float(full["p_loading"]),
        "r_regression": float(full["r_regression"]),
        "p_regression": float(full["p_regression"]),
    }
    return ist, block


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--convergence-iterations", type=int, default=500)
    parser.add_argument("--sensitivity-iterations", type=int, default=200)
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    print(f"[1/6] Simulation study ({args.iterations} iterations)...")
    simulation = run_simulation_block(args.iterations)

    print(f"[2/6] Negative control and redundancy checks ({args.sensitivity_iterations} iterations)...")
    negative_control = run_negative_control_block(args.sensitivity_iterations)
    redundancy = run_redundancy_block(args.sensitivity_iterations)

    print("[3/6] Real-world Table 1 analyses...")
    rw_results, realworld = run_real_world_block()

    print("[4/6] IST individual patient data (PCA + leave-one-out)...")
    ist_results, ist = run_ist_block()

    print("[5/6] Figures...")
    sim_frames = {
        key: pd.read_csv(RESULTS_DIR / f"simulation_scenario_{key.lower()}.csv")
        for key in ("A", "B", "C")
    }
    figure_paths = list(generate_all_figures(sim_frames, rw_results))
    linko_figures = generate_all_linko_figures(
        rw_results,
        ist_results,
        output_dir=str(FIGURE_DIR),
        n_convergence_iterations=args.convergence_iterations,
    )
    convergence = linko_figures["early_convergence"]["summary"]
    convergence_df = pd.DataFrame(convergence).T.reset_index().rename(
        columns={"index": "strategy"}
    )
    _write_table(convergence_df, "early_convergence.csv")

    print("[6/6] Writing results...")
    payload = {
        "metadata": {
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_commit": _git_commit(),
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
            "runtime_seconds": round(time.time() - t_start, 1),
            "data_dir": str(DATA_DIR),
        },
        "simulation": _json_safe(simulation),
        "negative_control": _json_safe(negative_control),
        "redundancy": _json_safe(redundancy),
        "realworld": _json_safe(realworld),
        "ist": _json_safe(ist),
        "early_convergence": {
            "settings": CONVERGENCE_SETTINGS,
            "n_iterations": args.convergence_iterations,
            "strategies": _json_safe(convergence),
        },
        "figures": _json_safe(
            {
                "core": figure_paths,
                "linko": {k: v for k, v in linko_figures.items() if k != "early_convergence"},
                "early_convergence": linko_figures["early_convergence"]["figure_path"],
                "ist": ist["figures"],
            }
        ),
    }
    with open(RESULTS_DIR / "results.json", "w") as fh:
        json.dump(_relative(payload), fh, indent=2)

    print(f"Wrote {RESULTS_DIR / 'results.json'} in {payload['metadata']['runtime_seconds']}s")


if __name__ == "__main__":
    main()

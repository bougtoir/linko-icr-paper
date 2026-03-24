#!/usr/bin/env python3
"""
Main runner script for the ICR paper analysis.

Executes:
1. Quick simulation study (100 iterations for fast results)
2. Real-world data analysis (statin and glucose control examples)
3. Figure generation
4. Summary report
"""

import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from icr_paper.src.simulation import run_quick_simulation
from icr_paper.src.real_world_analysis import run_real_world_analyses
from icr_paper.src.visualization import generate_all_figures

import numpy as np
import pandas as pd


def main():
    print("=" * 70)
    print("ICR Paper Analysis: Information Contribution Ratio")
    print("=" * 70)

    # ----------------------------------------------------------------
    # 1. Simulation Study
    # ----------------------------------------------------------------
    print("\n[1/3] Running simulation study (100 iterations)...")
    t0 = time.time()
    sim_results = run_quick_simulation(n_iterations=100, seed=42)
    t1 = time.time()
    print(f"  Completed in {t1 - t0:.1f}s")

    # Summary statistics
    for scenario, label in [("A", "Uniform ICR"), ("B", "Heterogeneous ICR")]:
        df = sim_results[scenario]
        print(f"\n  Scenario {scenario} ({label}):")
        print(f"    Mean I²:           {df['i_squared'].mean():.1f}% (SD={df['i_squared'].std():.1f})")
        print(f"    Mean ICRD:         {df['icrd'].mean():.4f} (SD={df['icrd'].std():.4f})")
        print(f"    Mean Pooled Effect: {df['pooled_effect'].mean():.3f} (True=0.5)")
        print(f"    Effect Bias:       {df['pooled_effect'].mean() - 0.5:.4f}")

    df_c = sim_results["C"]
    print(f"\n  Scenario C (Sequential):")
    print(f"    Mean I² change:    {df_c['i_squared_change'].mean():.1f}%")
    print(f"    I² increased in:   {(df_c['i_squared_change'] > 0).mean() * 100:.0f}% of simulations")

    # ----------------------------------------------------------------
    # 2. Real-World Analysis
    # ----------------------------------------------------------------
    print("\n[2/3] Running real-world data analysis...")
    t0 = time.time()
    rw_results = run_real_world_analyses()
    t1 = time.time()
    print(f"  Completed in {t1 - t0:.1f}s")

    for key, result in rw_results.items():
        print(f"\n  {key.replace('_', ' ').title()} Analysis:")
        df = result["study_results"]
        meta = result["meta_analysis"]
        icr_stats = result["icr_statistics"]

        print(f"    Studies: {len(df)}")
        print(f"    ICR_std range: [{df['icr_std'].min():.4f}, {df['icr_std'].max():.4f}]")
        print(f"    ICR_raw range: [{df['icr_raw'].min():.4f}, {df['icr_raw'].max():.4f}]")
        print(f"    ICR CV:    {icr_stats['icr_cv']:.4f}")
        print(f"    ICRD:      {icr_stats['icrd']:.4f}")
        print(f"    Meta I²:   {meta['i_squared']:.1f}%")
        print(f"    Pooled:    {meta['pooled_effect']:.3f} [{meta['ci_lower']:.3f}, {meta['ci_upper']:.3f}]")

        print(f"\n    Per-study ICR values:")
        for _, row in df.iterrows():
            print(f"      {row['study']}: ICR_std={row['icr_std']:.4f} "
                  f"ICR_raw={row['icr_raw']:.4f} "
                  f"(D={row['n_variables']}, d={row['n_endpoints']}), "
                  f"effect={row['effect_size']:.3f}")

    # ----------------------------------------------------------------
    # 3. Generate Figures
    # ----------------------------------------------------------------
    print("\n[3/3] Generating figures...")
    t0 = time.time()
    saved_figs = generate_all_figures(sim_results, rw_results)
    t1 = time.time()
    print(f"  Completed in {t1 - t0:.1f}s")
    for fig_path in saved_figs:
        print(f"    Saved: {fig_path}")

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SUMMARY OF KEY FINDINGS")
    print("=" * 70)

    mean_i2_a = sim_results["A"]["i_squared"].mean()
    mean_i2_b = sim_results["B"]["i_squared"].mean()
    print(f"\n1. Simulation: Mean I² with uniform ICR = {mean_i2_a:.1f}%, "
          f"with heterogeneous ICR = {mean_i2_b:.1f}%")
    print(f"   -> Heterogeneous ICR increases I² by {mean_i2_b - mean_i2_a:.1f} percentage points")

    corr_icrd_i2 = np.corrcoef(
        np.concatenate([sim_results["A"]["icrd"], sim_results["B"]["icrd"]]),
        np.concatenate([sim_results["A"]["i_squared"], sim_results["B"]["i_squared"]])
    )[0, 1]
    print(f"   -> Correlation between ICRD and I²: r = {corr_icrd_i2:.3f}")

    pct_increase = (sim_results["C"]["i_squared_change"] > 0).mean() * 100
    print(f"\n2. Sequential: Adding heterogeneous-ICR studies increased I² "
          f"in {pct_increase:.0f}% of simulations")

    print(f"\n3. Real-world:")
    for key, result in rw_results.items():
        icr_stats = result["icr_statistics"]
        meta = result["meta_analysis"]
        print(f"   {key}: ICRD={icr_stats['icrd']:.4f}, I²={meta['i_squared']:.1f}%")

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()

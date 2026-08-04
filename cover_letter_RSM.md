[Date]

Professor Dimitris Mavridis
Professor Terri Pigott
Editors-in-Chief
*Research Synthesis Methods*
Cambridge University Press

Dear Professors Mavridis and Pigott,

We are pleased to submit our manuscript entitled **"LINKO (Latent Information Normalization for Key Outcomes): A Framework for Evaluating the Validity of Meta-Analytic Pooling Across Heterogeneous RCT Data Structures"** for consideration for publication in *Research Synthesis Methods*.

### Summary

Meta-analysis pools endpoint-level effect sizes from multiple randomized controlled trials (RCTs), yet each contributing study collects a different number of variables -- meaning the endpoint may represent vastly different proportions of each study's total information space. We introduce the **LINKO framework** and its core metric, the **Information Contribution Ratio (ICR)**, which quantifies how much of a study's total data information is captured by its endpoint. We further propose the **ICR Discrepancy (ICRD)** as a new diagnostic for assessing the structural comparability of studies entering a meta-analysis.

### Relevance to *Research Synthesis Methods*

We believe this manuscript is well suited for *Research Synthesis Methods* for the following reasons:

1. **Novel methodological contribution to research synthesis**: The LINKO framework identifies a previously unrecognized source of heterogeneity in meta-analysis -- structural diversity arising from differences in data dimensionality across studies. This complements existing heterogeneity diagnostics (I-squared, tau-squared) and extends the methodological toolkit available to systematic reviewers.

2. **Practical and broadly applicable**: ICR_std can be computed from published Table 1 summary statistics without requiring individual patient data, making retrospective application feasible for any published meta-analysis. This aligns with the journal's emphasis on methods that are of "general interest or utility for the many fields and disciplines in which research synthesis is undertaken."

3. **Novel visualization**: We propose the **Prism Forest Plot**, an extension of the standard forest plot that encodes ICR information through color and point size, enabling immediate visual detection of structural heterogeneity.

4. **Multidisciplinary validation**: Our evidence base spans Monte Carlo simulation, real-world RCT meta-analyses (statin therapy and intensive glucose control), and PCA-based validation using individual patient data from the International Stroke Trial (19,435 patients, 8 country sub-studies). The PCA-based ICR showed a strong correlation with 14-day mortality (r = 0.90), robust across leave-one-out sensitivity analysis (r = 0.84--0.95, all p < 0.02).

5. **Convergence analysis**: We demonstrate that ICR-guided study selection can improve the homogeneity of early evidence synthesis, a consideration relevant to living systematic reviews and cumulative meta-analyses.

### Key Findings

- Studies with heterogeneous ICR show increased meta-analysis heterogeneity (I-squared 11.7% vs 11.0% in simulation)
- Real-world meta-analyses with known heterogeneity patterns are consistent with ICR-based predictions: statin therapy (low ICRD = 0.009, I-squared = 0.0%) vs glucose control (high ICRD = 0.048, I-squared = 17.0%)
- PCA-based ICR varies 4-fold across IST country sub-studies (0.046--0.180) despite identical variable sets, with regression-based ICR_pca strongly correlated with mortality (r = 0.90)

### Declarations

This manuscript has not been published previously and is not under consideration for publication elsewhere. All authors have read and approved the submitted version. All analysis code is publicly available on GitHub.

We believe that the LINKO framework addresses a gap in the methodological literature on research synthesis and will be of broad interest to the readership of *Research Synthesis Methods*. We look forward to your consideration.

Sincerely,

Tatsuki Onishi
[Affiliation]
[Email]

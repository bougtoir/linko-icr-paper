[Date]

Dr. Lan Lan
Lead Editor
*BMC Medical Research Methodology*
Springer Nature

Dear Dr. Lan,

We are pleased to submit our manuscript entitled **"LINKO (Latent Information Normalization for Key Outcomes): A Framework for Evaluating the Validity of Meta-Analytic Pooling Across Heterogeneous RCT Data Structures"** for consideration for publication in *BMC Medical Research Methodology*.

### Summary

Meta-analysis pools endpoint-level effect sizes from multiple randomized controlled trials (RCTs), yet each contributing study collects a different number of variables -- meaning the endpoint may represent vastly different proportions of each study's total information space. We introduce the **LINKO framework** and its core metric, the **Information Contribution Ratio (ICR)**, which quantifies how much of a study's total data information is captured by its endpoint. We further propose the **ICR Discrepancy (ICRD)** as a new diagnostic for assessing the structural comparability of studies entering a meta-analysis, and the **Prism Forest Plot** as a novel visualization tool.

### Relevance to *BMC Medical Research Methodology*

We believe this manuscript is well suited for *BMC Medical Research Methodology* for the following reasons:

1. **Methodological innovation for meta-analysis**: The LINKO framework identifies a previously unrecognized source of heterogeneity in meta-analysis -- structural diversity arising from differences in data dimensionality across studies. This directly addresses the journal's scope of publishing "original research articles in methodological approaches to healthcare research," with particular emphasis on meta-analysis methodology.

2. **Empirical evaluation of methodology and study outcomes**: Our study empirically demonstrates the association between ICR heterogeneity and meta-analysis outcomes across simulation and real-world data, aligning with the journal's interest in "empirical studies of the associations between choice of methodology and study outcomes."

3. **Practical and broadly applicable**: ICR_std can be computed from published Table 1 summary statistics without requiring individual patient data, making retrospective application feasible for any published meta-analysis.

4. **Dual-approach validation**: We provide both a variance-based approach (computable from summary statistics) and a PCA-based approach (using individual patient data from the International Stroke Trial, 19,435 patients, 8 country sub-studies). The PCA-based ICR showed a strong correlation with 14-day mortality (r = 0.90), robust across leave-one-out sensitivity analysis (r = 0.84--0.95, all p < 0.02).

5. **Novel visualization**: The Prism Forest Plot extends the standard forest plot by encoding ICR information through color and point size, enabling immediate visual detection of structural heterogeneity.

### Key Findings

- Studies with heterogeneous ICR show increased meta-analysis heterogeneity (I-squared 11.7% vs 11.0% in simulation)
- Real-world meta-analyses with known heterogeneity patterns are consistent with ICR-based predictions: statin therapy (low ICRD = 0.009, I-squared = 0.0%) vs glucose control (high ICRD = 0.048, I-squared = 17.0%)
- PCA-based ICR varies 4-fold across IST country sub-studies (0.046--0.180) despite identical variable sets, with regression-based ICR_pca strongly correlated with mortality (r = 0.90)

### Declarations

This manuscript has not been published previously and is not under consideration for publication elsewhere. All authors have read and approved the submitted version. All analysis code is publicly available on GitHub.

We believe that the LINKO framework addresses a gap in the methodological literature on meta-analysis and will be of broad interest to the readership of *BMC Medical Research Methodology*. We look forward to your consideration.

Sincerely,

Tatsuki Onishi
[Affiliation]
[Email]

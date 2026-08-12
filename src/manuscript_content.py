"""Manuscript content for the LINKO paper (Health Services and Outcomes
Research Methodology format).

The text is written here once as a language-neutral block list; every numeric
value is interpolated from ``results/results.json`` and the CSV tables in
``results/`` through :mod:`icr_paper.src.results_loader`. No analysis result
is written as a literal in this file.

Block grammar
-------------
``("h1"|"h2"|"h3", text)``    heading
``("p", text)``               paragraph
``("eq", text)``              display equation (italic, indented)
``("table", dict)``           table: keys ``label``, ``caption``, ``headers``, ``rows``
``("figure", dict)``          figure: keys ``label``, ``caption``, ``path``
``("pagebreak", None)``
"""

import re
from pathlib import Path

from .results_loader import (
    ci,
    load_results,
    mean_mcse,
    num,
    pct,
    pval,
    pval_plain,
    rate_pct,
    signed,
    thousands,
)

FIGURE_DIR = Path(__file__).resolve().parent.parent / "figures"

REFERENCES = [
    "Higgins JPT, Thompson SG, Deeks JJ, Altman DG. Measuring inconsistency in meta-analyses. *BMJ.* 2003;327:557-560.",
    "Higgins JPT, Thomas J, Chandler J, et al. *Cochrane Handbook for Systematic Reviews of Interventions.* Version 6.4. Chichester: Wiley; 2023.",
    "DerSimonian R, Laird N. Meta-analysis in clinical trials. *Control Clin Trials.* 1986;7:177-188.",
    "Veroniki AA, Jackson D, Viechtbauer W, et al. Methods to estimate the between-study variance and its uncertainty in meta-analysis. *Res Synth Methods.* 2016;7:55-79.",
    "Paule RC, Mandel J. Consensus values and weighting factors. *J Res Natl Bur Stand.* 1982;87:377-385.",
    "Hartung J, Knapp G. A refined method for the meta-analysis of controlled clinical trials with binary outcome. *Stat Med.* 2001;20:3875-3889.",
    "IntHout J, Ioannidis JPA, Rovers MM, Goeman JJ. Plea for routinely presenting prediction intervals in meta-analysis. *BMJ Open.* 2016;6:e010247.",
    "Riley RD, Higgins JPT, Deeks JJ. Interpretation of random effects meta-analyses. *BMJ.* 2011;342:d549.",
    "Morris TP, White IR, Crowther MJ. Using simulation studies to evaluate statistical methods. *Stat Med.* 2019;38:2074-2102.",
    "Rubin DB. Causal inference using potential outcomes. *J Am Stat Assoc.* 2005;100:322-331.",
    "Scandinavian Simvastatin Survival Study Group. Randomised trial of cholesterol lowering in 4444 patients with coronary heart disease (4S). *Lancet.* 1994;344:1383-1389.",
    "Shepherd J, Cobbe SM, Ford I, et al. Prevention of coronary heart disease with pravastatin in men with hypercholesterolemia. *N Engl J Med.* 1995;333:1301-1307.",
    "Sacks FM, Pfeffer MA, Moye LA, et al. The effect of pravastatin on coronary events after myocardial infarction in patients with average cholesterol levels. *N Engl J Med.* 1996;335:1001-1009.",
    "The Long-Term Intervention with Pravastatin in Ischaemic Disease (LIPID) Study Group. Prevention of cardiovascular events and death with pravastatin in patients with coronary heart disease. *N Engl J Med.* 1998;339:1349-1357.",
    "Downs JR, Clearfield M, Weis S, et al. Primary prevention of acute coronary events with lovastatin in men and women with average cholesterol levels (AFCAPS/TexCAPS). *JAMA.* 1998;279:1615-1622.",
    "UK Prospective Diabetes Study (UKPDS) Group. Intensive blood-glucose control with sulphonylureas or insulin compared with conventional treatment (UKPDS 33). *Lancet.* 1998;352:837-853.",
    "The Action to Control Cardiovascular Risk in Diabetes Study Group. Effects of intensive glucose lowering in type 2 diabetes. *N Engl J Med.* 2008;358:2545-2559.",
    "The ADVANCE Collaborative Group. Intensive blood glucose control and vascular outcomes in patients with type 2 diabetes. *N Engl J Med.* 2008;358:2560-2572.",
    "Duckworth W, Abraira C, Moritz T, et al. Glucose control and vascular complications in veterans with type 2 diabetes. *N Engl J Med.* 2009;360:129-139.",
    "International Stroke Trial Collaborative Group. The International Stroke Trial (IST). *Lancet.* 1997;349:1569-1581.",
    "Sandercock PAG, Niewada M, Czlonkowska A. The International Stroke Trial database. *Trials.* 2011;12:101.",
    "Jolliffe IT, Cadima J. Principal component analysis: a review and recent developments. *Philos Trans R Soc A.* 2016;374:20150202.",
    "Schild AHE, Voracek M. Less is less: a systematic review of graph use in meta-analyses. *Res Synth Methods.* 2013;4:209-219.",
    "Thompson SG, Higgins JPT. How should meta-regression analyses be undertaken and interpreted? *Stat Med.* 2002;21:1559-1573.",
    "Sterne JAC, Sutton AJ, Ioannidis JPA, et al. Recommendations for examining and interpreting funnel plot asymmetry. *BMJ.* 2011;343:d4002.",
]

# Reference numbers are assigned by first appearance below.
R = {name: i + 1 for i, name in enumerate(
    [
        "higgins2003", "cochrane", "dl1986", "veroniki", "paule", "hk",
        "inthout", "riley", "morris", "rubin", "s4", "woscops", "care",
        "lipid", "afcaps", "ukpds", "accord", "advance", "vadt", "ist1997",
        "ist2011", "jolliffe", "schild", "thompson", "sterne",
    ]
)}

# ----------------------------------------------------------------------
# Author-year reference style (Health Services and Outcomes Research
# Methodology / Springer).
# ----------------------------------------------------------------------
AUTHOR_OVERRIDES = {
    "s4": "4S Study Group",
    "lipid": "LIPID Study Group",
    "ukpds": "UKPDS Study Group",
    "accord": "ACCORD Study Group",
    "advance": "ADVANCE Collaborative Group",
    "ist1997": "International Stroke Trial Collaborative Group",
}

_YEAR_RE = re.compile(r"(?<!\d)(19|20)\d{2}(?=[;\s.]|$)")


def _initials_str(token: str) -> str:
    return " ".join(c + "." for c in token)


def _parse_authors(authors_str: str, key: str) -> tuple[list[tuple[str, str]], bool]:
    parts = [p.strip() for p in authors_str.split(",")]
    et_al = False
    if parts and parts[-1].lower().startswith("et al"):
        et_al = True
        parts = parts[:-1]
    authors: list[tuple[str, str]] = []
    for part in parts:
        tokens = part.split()
        initials: list[str] = []
        surname_tokens: list[str] = []
        for tok in tokens:
            if re.fullmatch(r"[A-Z]+", tok):
                initials.append(tok)
            else:
                surname_tokens.append(tok)
        surname = " ".join(surname_tokens)
        init_str = " ".join(_initials_str(tok) for tok in initials) if initials else ""
        authors.append((surname, init_str))
    if key in AUTHOR_OVERRIDES:
        authors = [(AUTHOR_OVERRIDES[key], "")] + authors[1:]
    return authors, et_al


def _parse_reference(text: str, key: str) -> dict:
    m = re.match(r"([^\.]+)\.\s+(.*)$", text)
    if not m:
        return {
            "raw": text,
            "key": key,
            "authors": [],
            "et_al": False,
            "year": "",
            "title": "",
            "journal": "",
            "volume": "",
            "pages": "",
            "publisher": "",
            "location": "",
            "version": "",
        }
    authors_str, rest = m.group(1), m.group(2)
    authors, et_al = _parse_authors(authors_str, key)
    italic_parts = re.findall(r"\*([^*]+)\*", rest)
    if rest.strip().startswith("*"):
        title = italic_parts[0] if italic_parts else ""
        extra = re.sub(r"\*[^*]+\*\s*\.?\s*", "", rest, count=1).strip()
        journal = ""
    else:
        parts = rest.split("*", 2)
        title = parts[0].strip(" .") if parts else ""
        journal = italic_parts[0] if italic_parts else ""
        extra = parts[2].strip(" .*") if len(parts) > 2 else ""
    volume = ""
    pages = ""
    publisher = ""
    location = ""
    version = ""
    ym = _YEAR_RE.search(extra)
    year = ym.group(0) if ym else ""
    if ym:
        before = extra[: ym.start()].strip()
        after = extra[ym.end() :].lstrip(" .")
        mvp = re.match(r";\s*([^:\n]+):\s*([^\s.]+)", after)
        if mvp:
            volume = mvp.group(1).strip()
            pages = mvp.group(2).rstrip(".").strip().replace("-", "\u2013")
        else:
            colon = before.rfind(":")
            if colon > 0:
                publisher = before[colon + 1 :].strip().rstrip(";")
                prefix = before[:colon].strip()
                if ". " in prefix:
                    version, location = prefix.rsplit(". ", 1)
                    version = version + "." if version else ""
                else:
                    location = prefix
                    version = ""
            else:
                version = before
    return {
        "raw": text,
        "key": key,
        "authors": authors,
        "et_al": et_al,
        "year": year,
        "title": title,
        "journal": journal,
        "volume": volume,
        "pages": pages,
        "publisher": publisher,
        "location": location,
        "version": version,
    }


def _format_authors(authors: list[tuple[str, str]]) -> str:
    parts = []
    for surname, initials in authors:
        if initials:
            parts.append(f"{surname}, {initials}")
        else:
            parts.append(surname)
    return ", ".join(parts)


def _format_reference(ref: dict) -> str:
    authors = _format_authors(ref["authors"])
    title = ref["title"]
    if title and not title.endswith((".", "?", "!")):
        title += "."
    if ref["journal"]:
        if ref["volume"] and ref["pages"]:
            return f"{authors}: {title} {ref['journal']} {ref['volume']}, {ref['pages']} ({ref['year']})."
        elif ref["volume"]:
            return f"{authors}: {title} {ref['journal']} {ref['volume']} ({ref['year']})."
        return f"{authors}: {title} {ref['journal']} ({ref['year']})."
    extra = ref["version"].rstrip(".")
    if ref["publisher"]:
        if extra:
            extra = f"{extra}. {ref['publisher']}, {ref['location']}"
        else:
            extra = f"{ref['publisher']}, {ref['location']}"
    return f"{authors}: {title} {extra} ({ref['year']})."


def _cite_label(ref: dict) -> str:
    if not ref["authors"]:
        return ""
    label = ref["authors"][0][0]
    n = len(ref["authors"])
    if n == 1:
        return label
    if n == 2 and not ref["et_al"]:
        return f"{label} and {ref['authors'][1][0]}"
    return f"{label} et al."


def _cite_author_year(*keys: str) -> str:
    entries = []
    for key in keys:
        idx = R[key] - 1
        text = REFERENCES[idx]
        ref = _parse_reference(text, key)
        label = _cite_label(ref)
        year = ref["year"]
        entries.append((label.lower(), label, year))
    entries.sort(key=lambda x: (x[0], x[2]))
    groups: list[tuple[str, list[str]]] = []
    for _, label, year in entries:
        if groups and groups[-1][0] == label:
            groups[-1][1].append(year)
        else:
            groups.append((label, [year]))
    parts = [f"{label} {', '.join(years)}" for label, years in groups]
    return "(" + "; ".join(parts) + ")"


def format_references() -> list[str]:
    """Return the reference list formatted and sorted alphabetically."""
    formatted = []
    for key, idx in R.items():
        ref = _parse_reference(REFERENCES[idx - 1], key)
        sort_key = (ref["authors"][0][0].lower(), ref["year"], key)
        formatted.append((sort_key, _format_reference(ref)))
    formatted.sort(key=lambda x: x[0])
    return [ref for _, ref in formatted]


def _cite(*keys: str) -> str:
    return _cite_author_year(*keys)


def _fig(label: str, filename: str, caption: str) -> tuple:
    return ("figure", {"label": label, "path": str(FIGURE_DIR / filename), "caption": caption})


def _table(label: str, caption: str, headers: list, rows: list) -> tuple:
    return ("table", {"label": label, "caption": caption, "headers": headers, "rows": rows})


# ----------------------------------------------------------------------
# Derived table rows (all values read from results/)
# ----------------------------------------------------------------------
def simulation_table_rows(res: dict) -> list:
    sim = res["simulation"]
    nc = res["negative_control"]
    a, b = sim["scenario_a"], sim["scenario_b"]
    diff = sim["difference_b_minus_a"]["i_squared"]
    rows = [
        ["Mean ICRD", mean_mcse(a["icrd"], 4), mean_mcse(b["icrd"], 4), mean_mcse(nc["icrd"], 4)],
        ["Mean I-squared (%)", mean_mcse(a["i_squared"], 2), mean_mcse(b["i_squared"], 2), mean_mcse(nc["i_squared"], 2)],
        ["Mean tau-squared", mean_mcse(a["tau_squared"], 4), mean_mcse(b["tau_squared"], 4), mean_mcse(nc["tau_squared"], 4)],
        ["Mean pooled effect", mean_mcse(a["pooled_effect"], 4), mean_mcse(b["pooled_effect"], 4), "-"],
        ["Bias", mean_mcse(a["bias"], 4), mean_mcse(b["bias"], 4), "-"],
    ]
    rows.append(
        [
            "Difference in I-squared (B - A), 95% Monte Carlo CI",
            f"{num(diff['mean_difference'], 2)} {ci(diff['ci_lower'], diff['ci_upper'], 2)}",
            "",
            "",
        ]
    )
    return rows


def redundancy_table_rows(res: dict) -> list:
    return [
        [
            str(int(row["n_redundant"])),
            str(int(round(row["n_variables"]))),
            num(row["icr_std"], 4),
            num(row["icr_raw"], 4),
            num(row["effective_dimension"], 2),
            num(row["icr_effective"], 4),
        ]
        for row in res["redundancy"]["summary"]
    ]


def realworld_table_rows(res: dict, tag: str) -> list:
    return [
        [
            s["study"],
            thousands(s["n_total"]),
            str(int(s["n_variables"])),
            str(int(s["n_endpoints"])),
            num(s["icr_std"], 3),
            f"{s['icr_raw']:.2e}",
            signed(s["effect_size"], 3),
        ]
        for s in res["realworld"][tag]["studies"]
    ]


def meta_sensitivity_rows(res: dict, tag: str) -> list:
    rows = []
    for r in res["realworld"][tag]["meta_sensitivity"]:
        pi = (
            ci(r["pi_lower"], r["pi_upper"])
            if r["pi_lower"] == r["pi_lower"]
            else "not estimable"
        )
        rows.append(
            [
                r["tau2_estimator"],
                r["interval"],
                num(r["tau_squared"], 4),
                num(r["pooled_effect"], 3),
                ci(r["ci_lower"], r["ci_upper"]),
                pi,
            ]
        )
    return rows


def ist_table_rows(res: dict) -> list:
    return [
        [
            c["country"],
            thousands(c["n"]),
            rate_pct(c["mortality_rate"]),
            num(c["icr_std"], 3),
            num(c["icr_pca_loading"], 3),
            f"{c['icr_pca_reg']:.5f}",
            str(int(c["n_endpoint_pcs"])),
        ]
        for c in res["ist"]["countries"]
    ]


def loo_table_rows(res: dict) -> list:
    return [
        [
            r["excluded_country"],
            str(int(r["n_countries"])),
            num(r["r_loading"], 3),
            pval_plain(r["p_loading"]),
            num(r["r_regression"], 3),
            pval_plain(r["p_regression"]),
        ]
        for r in res["ist"]["leave_one_out"]
    ]


def convergence_table_rows(res: dict) -> list:
    labels = {
        "random": "Random order",
        "matched": "ICR-matched first",
        "linko": "ICR-median-ordered (LINKO)",
    }
    return [
        [
            labels[key],
            num(s["mean_conclusive"], 2),
            num(s["median_conclusive"], 1),
            pct(s["pct_conclusive_by_5"]),
            pct(s["pct_conclusive_by_10"]),
            num(s["mean_stable"], 2),
        ]
        for key, s in res["early_convergence"]["strategies"].items()
    ]


# ----------------------------------------------------------------------
# English manuscript
# ----------------------------------------------------------------------
TITLE = (
    "LINKO (Latent Information Normalization for Key Outcomes): A Framework for "
    "Evaluating the Validity of Meta-Analytic Pooling Across Heterogeneous RCT Data Structures"
)
SHORT_TITLE = "LINKO"
AUTHORS = "Tatsuki Onishi"
AFFILIATION = (
    "Data Science and AI Innovation Research Promotion Center, Shiga University"
)
CORRESPONDING = "Tatsuki Onishi, [Address], [Email]"
KEYWORDS = [
    "meta-analysis",
    "heterogeneity",
    "evidence synthesis",
    "principal component analysis",
    "diagnostic plot",
    "reproducibility",
]


def build_english(res: dict) -> list:
    sim = res["simulation"]
    a, b = sim["scenario_a"], sim["scenario_b"]
    diff = sim["difference_b_minus_a"]["i_squared"]
    nc = res["negative_control"]
    red = res["redundancy"]
    statin = res["realworld"]["statin"]
    glucose = res["realworld"]["glucose_control"]
    ist = res["ist"]
    ist_sum = ist["summary"]
    conv = res["early_convergence"]["strategies"]
    meta = res["metadata"]
    settings = sim["settings"]

    blocks: list = []
    add = blocks.append

    # ---------------- Title page
    add(("title", TITLE))
    add(("p", f"Short title: {SHORT_TITLE}"))
    add(("p", f"Author: {AUTHORS}"))
    add(("p", f"Affiliation: {AFFILIATION}"))
    add(("p", f"Corresponding author: {CORRESPONDING}"))
    add(("p", "Word count of abstract: computed at build time (limit 250 words)."))
    add(("pagebreak", None))

    # ---------------- Abstract
    add(("h1", "Abstract"))
    add(
        (
            "p",
            "Meta-analysis pools one effect estimate per study, yet studies differ in how "
            "many variables they measure and in how the endpoint sits within that variable "
            "space. We formalise this structural feature within the Latent Information "
            "Normalization for Key Outcomes (LINKO) framework, whose core descriptor is the Information "
            "Contribution Ratio (ICR); we define its estimand, give estimators computable from published "
            "baseline tables and from individual participant data, and evaluate what the "
            "measure can and cannot support. In a Monte Carlo study with Monte Carlo standard "
            "errors, scenarios with heterogeneous ICR did not show a clearly higher I-squared "
            "than scenarios with uniform ICR (difference "
            f"{num(diff['mean_difference'], 2)} percentage points, 95% Monte Carlo confidence "
            f"interval {ci(diff['ci_lower'], diff['ci_upper'], 2)}), and a negative-control "
            "scenario in which ICR varied without any structural mechanism produced comparable "
            "heterogeneity. Adding near-duplicate covariates changed the dimension-counting "
            f"estimator to {num(red['icr_std_ratio_max_to_base'], 2)} times its original value "
            "while an eigenvalue-based effective-dimension version was essentially unchanged, showing "
            "that ICR is sensitive to variable counting conventions. In two published trial "
            "collections and in an exploratory analysis of eight country groups of the "
            "International Stroke Trial, ICR varied substantially across studies; the "
            "regression-based principal component estimator was associated with 14-day "
            f"mortality ({pval(ist['correlation_full']['p_regression'])}), but the groups are "
            "not independent trials and the analysis is hypothesis-generating. We conclude "
            "that ICR is best used as a reproducible descriptor of data structure and as a "
            "reporting adjunct, not as a validity criterion for pooling. All results are "
            "regenerated from public data by the accompanying code.",
        )
    )
    add(("p", "Keywords: " + "; ".join(KEYWORDS)))
    add(("pagebreak", None))

    # ---------------- 1 Introduction
    add(("h1", "1 Introduction"))
    add(
        (
            "p",
            "Randomised controlled trials (RCTs) record many variables per participant, but "
            "meta-analysis reduces each trial to a single effect estimate for one endpoint. "
            "Between-study heterogeneity is routinely quantified with Cochran's Q, the "
            f"I-squared index and the between-study variance tau-squared {_cite('higgins2003', 'cochrane', 'dl1986')}. "
            "These quantities describe dispersion of effect estimates; they say nothing about "
            "the data structure from which each estimate was extracted.",
        )
    )
    add(
        (
            "p",
            "A trial measuring ten baseline variables and a trial measuring eighty differ in an "
            "obvious way that is invisible to standard heterogeneity statistics. Whether this "
            "difference matters for pooling is an empirical question that, to our knowledge, has "
            "not been formalised. This paper does three things. First, it introduces the Latent Information "
            "Normalization for Key Outcomes (LINKO) framework, in which the "
            "Information Contribution Ratio (ICR) is the descriptor of the share of a study's "
            "measured information carried by its endpoint, together with an explicit estimand "
            "and estimators for both published summary statistics and individual participant data "
            "(IPD). Second, it tests, rather than assumes, the hypothesis that dispersion in ICR "
            "across studies is associated with statistical heterogeneity, using a simulation "
            "study with negative controls and Monte Carlo standard errors "
            f"{_cite('morris')}. Third, it examines the sensitivity of the measure to variable "
            "counting, coding and redundancy, which determines how it may legitimately be used.",
        )
    )
    add(
        (
            "p",
            "We state the conclusion of these analyses in advance because it is negative in an "
            "important respect: in our simulations ICR dispersion by itself did not generate or "
            "predict heterogeneity, and the simplest ICR estimator is strongly dependent on how "
            "variables are counted. We therefore present LINKO as a framework and ICR as its "
            "reproducible structural descriptor and reporting adjunct, and we present the "
            "accompanying visualisation, the prism forest plot, as a display device rather than "
            "as a test.",
        )
    )
    add(
        (
            "p",
            "Figure 1 shows the deterministic relationship between the number of measured "
            "variables and the simplest ICR estimator, which motivates both the appeal and the "
            "fragility of the measure.",
        )
    )
    add(_fig(
        "Figure 1",
        "fig0_icr_dimension_relationship.png",
        "Relationship between the number of measured variables and the dimension-counting "
        "Information Contribution Ratio (ICR_std = d/D) for a single endpoint. The curve is "
        "deterministic and illustrates why the measure is dominated by variable counting.",
    ))

    # ---------------- 2 Methods
    add(("h1", "2 Methods"))

    add(("h2", "2.1 Estimand"))
    add(
        (
            "p",
            "Let a study measure D variables X_1,...,X_D on its participants, of which a subset E "
            "of size d constitutes the endpoint(s) used in the meta-analysis. Define the target "
            "quantity",
        )
    )
    add(("eq", "ICR = f(E; X_1,...,X_D),"))
    add(
        (
            "p",
            "the share of the study's measured information attributable to E under a specified "
            "information functional f and a specified variable set. The estimand is therefore "
            "conditional on (i) the variable set the investigators chose to measure and report, "
            "(ii) the coding of those variables, and (iii) the functional f. It is a property of "
            "the study's data structure, not of the underlying disease process or of the "
            "treatment effect. In the potential-outcomes sense it is not a causal estimand "
            f"{_cite('rubin')}; no counterfactual is involved. This restriction is deliberate "
            "and is the reason we do not interpret ICR as a validity criterion for pooling.",
        )
    )

    add(("h2", "2.2 Estimators computable from published summary statistics"))
    add(("p", "Two functionals are used. The dimension-counting estimator is"))
    add(("eq", "ICR_std = d / D,"))
    add(
        (
            "p",
            "which is the share of the standardised variable space occupied by the endpoint when "
            "every variable is scaled to unit variance. The variance-ratio estimator is",
        )
    )
    add(("eq", "ICR_raw = sum_{j in E} Var(X_j) / sum_{j=1}^{D} Var(X_j),"))
    add(
        (
            "p",
            "computed on the reported measurement scales. For a continuous variable reported as "
            "mean and standard deviation by arm, the pooled within-study variance is reconstructed "
            "from the two arm variances and arm sizes; for a binary variable reported as a "
            "proportion p, the variance is p(1-p). ICR_raw is scale dependent by construction: "
            "a variable recorded in mg/dL contributes a far larger variance than the same variable "
            "in mmol/L, and a binary endpoint contributes a variance bounded by 0.25 while a "
            "laboratory variable may contribute several hundred. We report ICR_raw only to make "
            "this dependence explicit and we do not use it for comparison across studies.",
        )
    )
    add(
        (
            "p",
            "Both estimators depend on the counting rules. We prespecified the following: each "
            "variable reported as a separate row of the baseline table counts once; a multi-level "
            "categorical variable with L levels counts as L-1 indicator variables; composite "
            "scores are counted once and their components are not counted separately if the "
            "components are not reported; variables reported only for a subgroup are excluded. "
            "The complete variable lists, their codings and their sources are given in the "
            "repository so that the counts can be audited and changed. Section 3.2 quantifies how "
            "much the estimator moves when redundant variables are added.",
        )
    )

    add(("h2", "2.3 Estimators from individual participant data"))
    add(
        (
            "p",
            "When IPD are available, principal component analysis (PCA) on the correlation matrix "
            f"of the standardised variables {_cite('jolliffe')} gives two further estimators. The "
            "loading-based estimator sums the explained-variance ratios of components on which the "
            f"endpoint has absolute loading at least {num(res['ist']['summary']['loading_threshold'], 1)}:",
        )
    )
    add(("eq", "ICR_pca_loading = sum_{k in S_E} lambda_k / sum_k lambda_k."))
    add(
        (
            "p",
            "The regression-based estimator performs PCA on the predictors only, regresses the "
            "endpoint on all component scores, and expresses the endpoint variance explained "
            "relative to the total information in the system:",
        )
    )
    add(("eq", "ICR_pca_reg = sum_k beta_k^2 lambda_k / (sum_k lambda_k + Var(Y))."))
    add(
        (
            "p",
            f"The loading threshold of {num(res['ist']['summary']['loading_threshold'], 1)} "
            f"corresponds roughly to a squared loading of "
            f"{num(res['ist']['summary']['loading_threshold'] ** 2, 1)}, i.e. a variable "
            "contributing at least about 10% of a component's variance; we report it "
            "explicitly and treat the loading-based estimator as the more fragile of the two.",
        )
    )

    add(("h2", "2.4 Dispersion measures"))
    add(
        (
            "p",
            "Across the k studies of a meta-analysis we summarise dispersion of ICR by its range, "
            "ICRD = max_i ICR_i - min_i ICR_i, and by its coefficient of variation. Neither is a "
            "test statistic and neither has a reference distribution; they are descriptive.",
        )
    )

    add(("h2", "2.5 Meta-analysis and sensitivity analyses"))
    add(
        (
            "p",
            "Effect estimates were pooled with random-effects models using three estimators of "
            f"tau-squared: DerSimonian-Laird {_cite('dl1986')}, restricted maximum likelihood and "
            f"Paule-Mandel {_cite('veroniki', 'paule')}. Confidence intervals were computed both "
            f"with the Wald approach and with the Hartung-Knapp adjustment {_cite('hk')}, and "
            f"95% prediction intervals were computed where k > 2 {_cite('inthout', 'riley')}. "
            "All estimators are implemented in the accompanying code and are reported side by "
            "side rather than selected post hoc.",
        )
    )

    add(("h2", "2.6 Simulation study"))
    add(
        (
            "p",
            f"The simulation follows the ADEMP structure {_cite('morris')}. "
            "Aims: to determine whether dispersion in ICR across studies is associated with, or "
            "causes, statistical heterogeneity, and to determine how sensitive the estimators are "
            "to variable counting. "
            "Data-generating mechanism: for each study, D correlated standard normal variables "
            "were generated per arm with an exchangeable-like correlation structure, "
            f"n = {settings['n_subjects_per_study']} participants per study split equally between "
            "the two arms, a treatment effect of "
            f"{settings['true_effect']} standard deviations on the endpoint and a spillover "
            f"fraction of {settings['spillover_fraction']} applied to non-endpoint variables. "
            f"Estimands: the pooled endpoint effect and the heterogeneity statistics. "
            "Methods: DerSimonian-Laird random-effects meta-analysis of "
            f"{settings['n_studies_scenario_ab']} studies. "
            "Performance measures: mean I-squared, mean tau-squared, bias of the pooled effect, "
            "and the paired difference in I-squared between scenarios, each with its Monte Carlo "
            f"standard error over {sim['n_iterations']} repetitions.",
        )
    )
    add(
        (
            "p",
            f"Scenario A held the number of variables fixed at D = {settings['dimensions_scenario_a']} "
            "so that ICR was uniform. Scenario B drew D from "
            f"{{{', '.join(str(x) for x in settings['dimensions_scenario_b'])}}} so that ICR varied. "
            "Scenario C added heterogeneous-ICR studies sequentially to a uniform-ICR base. The "
            "negative control repeated Scenario B with the spillover fraction set to zero, so that "
            "ICR varied while nothing in the data-generating mechanism could induce heterogeneity "
            "in the endpoint effect; under the hypothesis that ICR dispersion per se increases "
            "heterogeneity this scenario should behave like Scenario A.",
        )
    )
    add(
        (
            "p",
            "The redundancy analysis added near-duplicate copies of existing covariates (a copy "
            "plus Gaussian noise) to a single simulated study, increasing D without adding "
            "information, and recorded ICR_std, ICR_raw and an eigenvalue-based alternative in "
            "which D is replaced by the participation ratio "
            "(sum of eigenvalues)^2 / sum of squared eigenvalues.",
        )
    )

    add(("h2", "2.7 Published trial collections"))
    add(
        (
            "p",
            f"Two collections were assembled from published reports: {statin['n_studies']} statin "
            f"trials {_cite('s4', 'woscops', 'care', 'lipid', 'afcaps')} and "
            f"{glucose['n_studies']} intensive glucose-control trials "
            f"{_cite('ukpds', 'accord', 'advance', 'vadt')}, with all-cause mortality as the "
            "endpoint. Baseline variables, effect estimates and their variances were entered into "
            "comma-separated files with a per-study citation and provenance note; the analysis "
            "reads those files. These collections illustrate the computation on real published "
            "structures. They are not systematic reviews, the trials were selected for "
            "illustration, and no inference about statin or glucose-control efficacy is intended.",
        )
    )

    add(("h2", "2.8 Individual participant data example"))
    add(
        (
            "p",
            f"The International Stroke Trial {_cite('ist1997', 'ist2011')} provides open "
            f"individual participant data for {thousands(ist_sum['n_patients_raw'])} patients. "
            f"After restriction to complete cases on the {int(ist_sum['n_variables'])} analysis "
            f"variables, {thousands(ist_sum['n_patients_complete'])} patients remained; the "
            f"{ist_sum['n_countries']} largest country groups "
            f"({thousands(ist_sum['total_patients'])} patients) were analysed as pseudo-studies. "
            "These groups are recruitment strata of a single trial with a common protocol and a "
            "common case-report form, not independent RCTs, so all IST results are exploratory "
            "and are reported without inferential claims. Because the case-report form is common, "
            "ICR_std is identical across groups by construction; only the PCA-based estimators "
            "vary. Sensitivity to individual groups was assessed by leave-one-out recomputation "
            "of the association between each estimator and 14-day mortality. Because larger "
            "groups give more stable covariance estimates, group size is a candidate common "
            "cause of both the estimators and the observed mortality; we therefore also report "
            "the partial correlation of each estimator with mortality given the logarithm of "
            "group size.",
        )
    )

    add(("h2", "2.9 Prism forest plot"))
    add(
        (
            "p",
            "The prism forest plot is a standard forest plot in which marker colour encodes ICR "
            "and marker size encodes a second ICR variant when available, with a side panel "
            "listing the values. Its purpose is to make structural differences visible next to "
            f"the effect estimates {_cite('schild')}; it performs no inference.",
        )
    )

    add(("h2", "2.10 Software and reproducibility"))
    add(
        (
            "p",
            f"Analyses were run in Python {meta['python_version']} with NumPy {meta['numpy_version']} "
            f"and pandas {meta['pandas_version']}. The IST data are downloaded by a script from the "
            "University of Edinburgh DataShare repository; the published-trial inputs are stored as "
            "comma-separated files with their sources. A single command regenerates every number, "
            "table and figure in this article into a results directory, and the manuscript is built "
            "by reading those files, so no value reported here is transcribed by hand.",
        )
    )

    # ---------------- 3 Results
    add(("h1", "3 Results"))

    add(("h2", "3.1 Simulation"))
    add(
        (
            "p",
            f"Over {sim['n_iterations']} repetitions, mean I-squared was "
            f"{pct(a['i_squared']['mean'], 1)} (Monte Carlo standard error "
            f"{num(a['i_squared']['mcse'], 2)}) in the uniform-ICR scenario and "
            f"{pct(b['i_squared']['mean'], 1)} (Monte Carlo standard error "
            f"{num(b['i_squared']['mcse'], 2)}) in the heterogeneous-ICR scenario. The paired "
            f"difference was {num(diff['mean_difference'], 2)} percentage points with 95% Monte "
            f"Carlo confidence interval {ci(diff['ci_lower'], diff['ci_upper'], 2)}. The pooled "
            f"effect was unbiased in both scenarios (bias "
            f"{signed(a['bias']['mean'], 4)} and {signed(b['bias']['mean'], 4)}). Across all "
            "repetitions of both scenarios the correlation between ICRD and I-squared was "
            f"r = {num(sim['correlation_icrd_i_squared']['r'], 3)} "
            f"({pval(sim['correlation_icrd_i_squared']['p'])}). In the negative control, where ICR "
            f"varied but no structural mechanism operated, mean I-squared was "
            f"{pct(nc['i_squared']['mean'], 1)} (Monte Carlo standard error "
            f"{num(nc['i_squared']['mcse'], 2)}), that is, of the same order as the two main "
            "scenarios. In the sequential scenario, adding heterogeneous-ICR studies changed "
            f"I-squared by {num(sim['scenario_c']['i_squared_change']['mean'], 2)} percentage "
            f"points on average (Monte Carlo standard error "
            f"{num(sim['scenario_c']['i_squared_change']['mcse'], 2)}), with an increase in "
            f"{rate_pct(sim['scenario_c']['proportion_increased'])} of repetitions. Taken "
            "together, these results do not support the hypothesis that dispersion in ICR by "
            "itself produces detectable statistical heterogeneity in this data-generating "
            "mechanism (Table 1, Figure 2).",
        )
    )
    add(_fig(
        "Figure 2",
        "fig1_scenario_comparison.png",
        "Simulation results for the uniform-ICR (Scenario A) and heterogeneous-ICR (Scenario B) "
        "designs: distributions of I-squared, tau-squared, ICR discrepancy and the pooled effect.",
    ))

    add(("h2", "3.2 Sensitivity of the estimator to variable counting"))
    base = red["summary"][0]
    top = red["summary"][-1]
    add(
        (
            "p",
            "Adding near-duplicate covariates to a single simulated study increased the counted "
            f"dimension from {int(round(base['n_variables']))} to {int(round(top['n_variables']))} "
            f"and reduced ICR_std from {num(base['icr_std'], 4)} to {num(top['icr_std'], 4)}, "
            f"that is to {num(red['icr_std_ratio_max_to_base'], 2)} times its original value, "
            "although the duplicated "
            "variables carried essentially no new information. ICR_raw behaved similarly. The "
            "eigenvalue-based alternative, which replaces the count D by the participation ratio, "
            f"changed only from {num(base['icr_effective'], 4)} to {num(top['icr_effective'], 4)} "
            f"(a ratio of {num(red['icr_effective_ratio_max_to_base'], 2)}; Table 2). The "
            "dimension-counting estimator is therefore an artefact of reporting practice as much "
            "as of study design, and comparisons of ICR_std across studies with different "
            "reporting conventions are not interpretable without an explicit counting protocol.",
        )
    )

    add(("h2", "3.3 Published trial collections"))
    st_meta = statin["meta_analysis"]
    gl_meta = glucose["meta_analysis"]
    all_studies = [
        s
        for tag in ("statin", "glucose_control")
        for s in res["realworld"][tag]["studies"]
    ]
    raw_values = [s["icr_raw"] for s in all_studies]
    std_values = [s["icr_std"] for s in all_studies]
    raw_lo, raw_hi = num(min(raw_values), 6), num(max(raw_values), 6)
    std_lo, std_hi = num(min(std_values), 3), num(max(std_values), 3)
    add(
        (
            "p",
            f"In the statin collection, the number of reported baseline variables ranged from "
            f"{statin['n_variables_range'][0]} to {statin['n_variables_range'][1]}, giving ICR_std "
            f"between {num(statin['icr_std_range'][0])} and {num(statin['icr_std_range'][1])} "
            f"(ICRD {num(statin['icr_statistics']['icrd'], 3)}, coefficient of variation "
            f"{num(statin['icr_statistics']['icr_cv'], 3)}). The pooled log risk ratio was "
            f"{num(st_meta['pooled_effect'])} {ci(st_meta['ci_lower'], st_meta['ci_upper'])} with "
            f"I-squared {pct(st_meta['i_squared'], 1)} (Table 3). In the glucose-control "
            f"collection, ICR_std ranged from {num(glucose['icr_std_range'][0])} to "
            f"{num(glucose['icr_std_range'][1])} (ICRD "
            f"{num(glucose['icr_statistics']['icrd'], 3)}, coefficient of variation "
            f"{num(glucose['icr_statistics']['icr_cv'], 3)}), the pooled log risk ratio was "
            f"{num(gl_meta['pooled_effect'])} {ci(gl_meta['ci_lower'], gl_meta['ci_upper'])} and "
            f"I-squared was {pct(gl_meta['i_squared'], 1)} (Table 4). The ordering of these two "
            "collections is consistent with the hypothesis, but with "
            f"{statin['n_studies']} and {glucose['n_studies']} studies respectively, two "
            "collections cannot distinguish a structural explanation from clinical and "
            "methodological differences; we report the comparison as an illustration and not as "
            "evidence. Within each collection, the association between ICR_std and effect size was "
            f"r = {num(statin['correlation_icr_effect']['icr_vs_effect_r'], 3)} "
            f"({pval(statin['correlation_icr_effect']['icr_vs_effect_p'])}) and "
            f"r = {num(glucose['correlation_icr_effect']['icr_vs_effect_r'], 3)} "
            f"({pval(glucose['correlation_icr_effect']['icr_vs_effect_p'])}).",
        )
    )
    add(
        (
            "p",
            f"ICR_raw ranged from {raw_lo} to {raw_hi} across the studies of the two "
            f"collections, against ICR_std between {std_lo} and {std_hi} in the same studies, "
            "because the endpoints are binary while several baseline variables are "
            "laboratory measurements on wide scales (Table 3, Table 4). This confirms that "
            "ICR_raw is not comparable across studies that report different variable types or "
            "units, and it should not be used for pooling diagnostics.",
        )
    )
    add(
        (
            "p",
            "Conclusions were unchanged under alternative between-study variance estimators, "
            "Hartung-Knapp intervals and prediction intervals (Table 5); the prediction intervals "
            "are, as expected, considerably wider than the confidence intervals.",
        )
    )
    add(
        (
            "p",
            "Figure 3 shows the statin collection as a prism forest plot, in which ICR_std is "
            "visible alongside the effect estimates. The same display for the intensive "
            "glucose-control collection is given in Supplementary Figure S1.",
        )
    )
    add(_fig(
        "Figure 3",
        "fig_linko_prism_statin.png",
        "Prism forest plot for the statin collection. Marker colour encodes ICR_std; the side "
        "panel lists the values. The display is descriptive.",
    ))
    add(_fig(
        "Supplementary Figure S1",
        "fig_linko_prism_glucose_control.png",
        "Prism forest plot for the intensive glucose-control collection.",
    ))

    add(("h2", "3.4 Exploratory individual participant data analysis"))
    corr = ist["correlation_full"]
    loo = ist["loo_ranges"]
    size = ist["size_adjusted"]
    add(
        (
            "p",
            f"Across the {ist_sum['n_countries']} IST country groups, the loading-based estimator "
            f"ranged from {num(ist_sum['icr_pca_loading_range'][0])} to "
            f"{num(ist_sum['icr_pca_loading_range'][1])} (coefficient of variation "
            f"{num(ist_sum['icr_pca_loading_cv'], 2)}) and the regression-based estimator from "
            f"{ist_sum['icr_pca_reg_range'][0]:.5f} to {ist_sum['icr_pca_reg_range'][1]:.5f} "
            f"(coefficient of variation {num(ist_sum['icr_pca_reg_cv'], 2)}), while ICR_std was "
            f"identical at {num(ist_sum['icr_std'])} by construction (Table 6, Figure 4). The "
            "regression-based estimator was associated with 14-day mortality "
            f"(r = {num(corr['r_regression'])}, {pval(corr['p_regression'])}); the loading-based "
            f"estimator was not (r = {num(corr['r_loading'])}, {pval(corr['p_loading'])}). In "
            "leave-one-out recomputation the regression-based association ranged from "
            f"r = {num(loo['r_regression'][0])} to {num(loo['r_regression'][1])} "
            f"(P from {pval_plain(loo['p_regression'][0])} to {pval_plain(loo['p_regression'][1])}) "
            f"and the loading-based association from r = {num(loo['r_loading'][0])} to "
            f"{num(loo['r_loading'][1])} (Supplementary Table S1, Supplementary Figure S2)."
        )
    )
    add(
        (
            "p",
            "The association is not explained by group size alone: the logarithm of the number "
            f"of patients was correlated with mortality at r = {num(size['r_log_n_vs_mortality'])} "
            f"({pval(size['p_log_n_vs_mortality'])}) and with the regression-based estimator at "
            f"r = {num(size['r_log_n_vs_regression'])} "
            f"({pval(size['p_log_n_vs_regression'])}), and the partial correlation of the "
            "regression-based estimator with mortality given log group size was "
            f"r = {num(size['partial_r_regression'])} "
            f"({pval(size['partial_p_regression'])}, {size['partial_df_regression']} degrees of "
            "freedom). With eight groups this adjustment has very little power and cannot "
            "exclude confounding by case mix or by other group-level features.",
        )
    )
    add(
        (
            "p",
            "These groups share a protocol and a case-report form and differ in case mix, so an "
            "association between a covariance-structure summary and mortality is expected under "
            "several explanations that have nothing to do with meta-analytic pooling; with eight "
            "non-independent groups the association is hypothesis-generating only. We report it "
            "to show that the PCA estimators are computable and do vary meaningfully, not as "
            "validation of the framework.",
        )
    )
    add(_fig(
        "Figure 4",
        "fig_pca_ist_analysis.png",
        "Principal-component-based ICR in eight International Stroke Trial country groups: "
        "estimator values, their dispersion, and their relation to 14-day mortality.",
    ))
    add(_fig(
        "Supplementary Figure S2",
        "fig_loo_sensitivity.png",
        "Leave-one-out recomputation of the association between each PCA-based ICR estimator and "
        "14-day mortality across the eight country groups.",
    ))
    add(
        (
            "p",
            "Figure 5 displays the same groups as a prism forest plot, with both PCA-based "
            "estimators encoded simultaneously.",
        )
    )
    add(_fig(
        "Figure 5",
        "fig_linko_prism_ist.png",
        "Prism forest plot for the International Stroke Trial country groups, with colour encoding "
        "the loading-based estimator and marker size the regression-based estimator. Rates are "
        "shown for display; the groups are not independent trials.",
    ))

    add(("h2", "3.5 Study ordering"))
    add(
        (
            "p",
            "Ordering studies by proximity to the median ICR did not reach a conclusive pooled "
            "estimate with fewer studies than random ordering: the mean number of studies required "
            f"was {num(conv['random']['mean_conclusive'], 2)} for random ordering, "
            f"{num(conv['matched']['mean_conclusive'], 2)} for ICR-matched ordering and "
            f"{num(conv['linko']['mean_conclusive'], 2)} for ICR-median ordering (Table 7). We "
            "report this negative result because ICR-guided prioritisation is an obvious "
            "application of the measure and, on this evidence, it is not supported.",
        )
    )

    # ---------------- 4 Discussion
    add(("h1", "4 Discussion"))
    add(
        (
            "p",
            "We introduced the LINKO framework and defined its Information Contribution "
            "Ratio, gave estimators computable from published tables and from IPD, and tested the "
            "natural hypothesis that dispersion in this quantity is associated with statistical "
            "heterogeneity. The hypothesis was not "
            "supported in simulation, either against a uniform-ICR comparator or against a "
            "negative control, and an obvious application, ICR-guided study ordering, gave no "
            "advantage. At the same time the measure is easy to compute, varies substantially "
            "across real studies, and its PCA form varies across groups of a single trial that "
            "share a case-report form.",
        )
    )
    add(
        (
            "p",
            "The practical implication is that ICR should be read as a structural descriptor, in "
            "the same family as reporting of the number and type of measured covariates, and not "
            "as a diagnostic of whether pooling is valid. Reporting it alongside I-squared and "
            "tau-squared costs nothing and makes explicit a feature of the included studies that "
            "is otherwise invisible; interpreting a large ICR discrepancy as evidence against "
            f"pooling would not be justified by our results. Existing tools such as meta-regression "
            f"{_cite('thompson')} and funnel-plot diagnostics {_cite('sterne')} remain the "
            "appropriate instruments for investigating heterogeneity and small-study effects.",
        )
    )
    add(
        (
            "p",
            "Limitations. First, the dimension-counting estimator depends on how variables are "
            "counted, coded and aggregated, and our redundancy analysis shows the size of the "
            "problem: near-duplicate covariates alone changed it to "
            f"{num(red['icr_std_ratio_max_to_base'], 2)} times its original value. Any "
            "application must fix a counting "
            "protocol in advance; the effective-dimension variant is a partial remedy but "
            "requires IPD. Second, ICR_raw is scale dependent and is close to zero whenever the "
            "endpoint is binary and covariates are measured on wide scales. Third, our "
            "data-generating mechanism induces structural differences through the number of "
            "measured variables and a spillover parameter; other mechanisms, for example endpoints "
            "that are composites of differing breadth, might behave differently, and our negative "
            "findings do not exclude them. Fourth, the published collections are illustrative and "
            "small, and the IST analysis uses country groups of one trial, which are not "
            "independent studies; these groups also differ in size, and although adjustment for "
            "log group size left the regression-based association essentially unchanged, eight "
            "groups cannot rule out group-level confounding by case mix. Fifth, we did not "
            "evaluate binary or time-to-event endpoints on "
            "IPD, where the notion of endpoint variance requires a different definition.",
        )
    )

    # ---------------- 5 Conclusions
    add(("h1", "5 Conclusions"))
    add(
        (
            "p",
            "The LINKO framework proposes the Information Contribution Ratio as a reproducible "
            "descriptor of how much of a study's measured data is carried by its endpoint. It is "
            "computable from published baseline tables, it varies across real studies, and it can "
            "be displayed alongside effect estimates. On present evidence it is not a diagnostic "
            "of heterogeneity and not a criterion for deciding whether studies may be pooled, and "
            "its simplest form is sensitive to variable counting. We recommend that it be used, if "
            "at all, as a transparently defined reporting adjunct with a prespecified counting "
            "protocol.",
        )
    )

    # ---------------- Statements and Declarations
    add(("h1", "Statements and Declarations"))
    add(("h2", "Acknowledgements"))
    add(("p", "[To be completed]"))
    add(("h2", "Competing interests"))
    add(("p", "The author declares no competing interests."))
    add(("h2", "Funding"))
    add(("p", "No funding was received for this study."))
    add(("h2", "Data availability"))
    add(
        (
            "p",
            "The International Stroke Trial data are openly available from the University of "
            "Edinburgh DataShare repository at https://datashare.ed.ac.uk/handle/10283/124 and are "
            "downloaded by the script provided with the analysis code. The baseline and effect "
            "data extracted from the published statin and glucose-control trials, with their "
            "per-study citations, are included in the code repository. All analysis code, the "
            "generated results files and the manuscript build script are available at "
            "https://github.com/bougtoir/linko-icr-paper. Every number in this article is regenerated "
            "from those sources by a single command; the results files record the software "
            f"versions and the commit used (commit {meta['git_commit'][:12]}).",
        )
    )
    add(("h2", "Ethics approval and consent to participate"))
    add(
        (
            "p",
            "This study analysed simulated data and a publicly available, de-identified dataset; "
            "no ethical approval was required.",
        )
    )

    add(("pagebreak", None))
    add(("h1", "References"))
    add(("references", REFERENCES))

    # ---------------- Tables (Statistics in Medicine: after the reference list)
    add(("pagebreak", None))
    add(_table(
        "Table 1",
        f"Simulation results over {sim['n_iterations']} repetitions, with Monte Carlo standard "
        "errors (MCSE). Scenario A: uniform ICR; Scenario B: heterogeneous ICR; negative control: "
        f"heterogeneous ICR with no structural mechanism ({nc['n_iterations']} repetitions).",
        ["Performance measure", "Scenario A", "Scenario B", "Negative control"],
        simulation_table_rows(res),
    ))
    add(("pagebreak", None))
    add(_table(
        "Table 2",
        "Effect of adding near-duplicate covariates on the ICR estimators "
        f"({red['n_iterations']} repetitions; means across repetitions). The effective dimension "
        "is the participation ratio of the correlation-matrix eigenvalues.",
        [
            "Redundant copies added",
            "Counted variables D",
            "ICR_std",
            "ICR_raw",
            "Effective dimension",
            "ICR (effective dimension)",
        ],
        redundancy_table_rows(res),
    ))
    add(("pagebreak", None))
    add(_table(
        "Table 3",
        "Statin trials: reported baseline variables, ICR estimators and all-cause mortality log "
        "risk ratios. Sources and provenance for every value are listed in the repository.",
        ["Trial", "Participants", "D", "d", "ICR_std", "ICR_raw", "Log risk ratio"],
        realworld_table_rows(res, "statin"),
    ))
    add(("pagebreak", None))
    add(_table(
        "Table 4",
        "Intensive glucose-control trials: reported baseline variables, ICR estimators and "
        "all-cause mortality log risk ratios.",
        ["Trial", "Participants", "D", "d", "ICR_std", "ICR_raw", "Log risk ratio"],
        realworld_table_rows(res, "glucose_control"),
    ))
    add(("pagebreak", None))
    add(_table(
        "Table 5",
        "Sensitivity of the pooled estimate to the between-study variance estimator and to the "
        "interval method, statin collection (upper block) and glucose-control collection (lower "
        "block). PI: 95% prediction interval.",
        ["tau-squared estimator", "Interval", "tau-squared", "Pooled effect", "95% CI", "95% PI"],
        meta_sensitivity_rows(res, "statin")
        + [["Glucose control", "", "", "", "", ""]]
        + meta_sensitivity_rows(res, "glucose_control"),
    ))
    add(("pagebreak", None))
    add(_table(
        "Table 6",
        "International Stroke Trial country groups: sample size, 14-day mortality and ICR "
        "estimators. ICR_std is identical across groups because the case-report form is common.",
        [
            "Country group",
            "Patients",
            "14-day mortality",
            "ICR_std",
            "ICR_pca (loading)",
            "ICR_pca (regression)",
            "Endpoint components",
        ],
        ist_table_rows(res),
    ))
    add(("pagebreak", None))
    add(_table(
        "Supplementary Table S1",
        "Leave-one-out recomputation of the association between the PCA-based ICR estimators and "
        "14-day mortality across the International Stroke Trial country groups.",
        [
            "Excluded group",
            "Groups analysed",
            "r (loading)",
            "P (loading)",
            "r (regression)",
            "P (regression)",
        ],
        loo_table_rows(res),
    ))
    add(("pagebreak", None))
    add(_table(
        "Table 7",
        "Number of studies required before the pooled estimate excluded the null, by ordering "
        f"strategy ({res['early_convergence']['n_iterations']} repetitions of "
        f"{res['early_convergence']['settings']['n_studies_total']} simulated studies).",
        [
            "Ordering strategy",
            "Mean studies to conclusive",
            "Median",
            "Conclusive by 5 studies",
            "Conclusive by 10 studies",
            "Mean studies to I-squared < 25%",
        ],
        convergence_table_rows(res),
    ))

    return blocks


# ----------------------------------------------------------------------
# Japanese manuscript (mirrors the English structure and numbers)
# ----------------------------------------------------------------------
def build_japanese(res: dict) -> list:
    sim = res["simulation"]
    a, b = sim["scenario_a"], sim["scenario_b"]
    diff = sim["difference_b_minus_a"]["i_squared"]
    nc = res["negative_control"]
    red = res["redundancy"]
    statin = res["realworld"]["statin"]
    glucose = res["realworld"]["glucose_control"]
    ist = res["ist"]
    ist_sum = ist["summary"]
    corr = ist["correlation_full"]
    conv = res["early_convergence"]["strategies"]

    blocks: list = []
    add = blocks.append

    add(("title", "LINKO (Latent Information Normalization for Key Outcomes): 不均一な"
                  "RCTデータ構造を横断したメタ解析的プーリングの妥当性を評価する枠組み"))
    add(("p", "著者: 大西達輝"))
    add(("p", "所属: [所属]"))
    add(("pagebreak", None))

    add(("h1", "抄録"))
    add(("p",
         "メタ解析は各研究から単一の効果量を統合するが、研究間で測定変数の数やエンドポイントの位置づけは大きく異なる。"
         "本研究はこの構造的特徴を情報寄与比 (ICR) として定式化し、推定対象 (estimand) を定義したうえで、"
         "公表ベースライン表および個票データから計算可能な推定量を与え、この指標で何が言えて何が言えないかを検証した。"
         f"モンテカルロ標準誤差を伴うシミュレーションでは、ICRが不均一なシナリオのI²は均一シナリオより明確に高くはなく"
         f"(差 {num(diff['mean_difference'], 2)}ポイント, 95%モンテカルロ信頼区間 "
         f"{ci(diff['ci_lower'], diff['ci_upper'], 2)})、構造的機序を持たない陰性対照でも同程度の異質性が観察された。"
         f"近似重複変数を追加するとICR_stdは{num(red['icr_std_ratio_max_to_base'], 2)}倍に変化した一方、"
         "固有値に基づく実効次元版はほぼ不変であり、ICRが変数の数え方に強く依存することが示された。"
         "公表2領域および国際脳卒中試験 (IST) の8か国群の探索的解析ではICRは研究間で大きく変動し、"
         f"回帰法のPCA推定量は14日死亡率と関連したが ({pval(corr['p_regression'])})、"
         "これらの群は独立したRCTではなく仮説生成的である。"
         "以上より、ICRはプーリングの妥当性判定基準ではなく、データ構造の再現可能な記述指標および報告の補助として"
         "用いるべきである。全結果は公開データから付属コードで再生成される。"))
    add(("pagebreak", None))

    add(("h1", "1 緒言"))
    add(("p",
         "RCTは参加者ごとに多数の変数を測定するが、メタ解析は各試験を単一エンドポイントの効果量に縮約する。"
         "I²やτ²は効果量のばらつきを記述するが、その効果量が抽出された元のデータ構造については何も述べない。"
         "本研究はICRを定義し、その分散が統計的異質性と関連するという仮説を、陰性対照とモンテカルロ標準誤差を"
         "用いて検証した。結論を先に述べると、この仮説は支持されなかった。"))

    add(("h1", "2 方法"))
    add(("h2", "2.1 推定対象"))
    add(("p",
         "研究がD個の変数を測定し、そのうちd個がメタ解析に用いるエンドポイントであるとき、ICRは"
         "指定した情報汎関数fと変数集合のもとでエンドポイントに帰属する情報の割合として定義される。"
         "この推定対象は、研究者が測定・報告した変数集合、その符号化、およびfに条件付けられており、"
         "疾患過程や治療効果の性質ではなくデータ構造の性質である。因果的推定対象ではない。"))
    add(("h2", "2.2 公表要約統計量からの推定量"))
    add(("eq", "ICR_std = d / D"))
    add(("eq", "ICR_raw = Σ_{j∈E} Var(X_j) / Σ_{j=1..D} Var(X_j)"))
    add(("p",
         "連続変数は群別の平均・標準偏差・例数からプール分散を再構成し、2値変数はp(1-p)を用いる。"
         "ICR_rawは測定尺度に依存するため、研究間比較には用いない。変数の計数規則は事前規定し、"
         "変数リストと出典はリポジトリで公開している。"))
    add(("h2", "2.3 個票データからの推定量"))
    add(("p",
         f"標準化変数の相関行列に対する主成分分析により、負荷量が{num(res['ist']['summary']['loading_threshold'], 1)}以上の"
         "主成分の寄与率和 (loading法) と、予測変数のみのPCA得点にエンドポイントを回帰して求める指標 (回帰法) を用いた。"
         f"このしきい値は2乗負荷量約{num(res['ist']['summary']['loading_threshold'] ** 2, 1)}（変数が主成分の約10%の分散を説明）"
         "に概ね対応し、恣意的であることを明示する。"))
    add(("h2", "2.4 メタ解析と感度分析"))
    add(("p",
         "DerSimonian-Laird、REML、Paule-Mandelの3つのτ²推定量、Wald法とHartung-Knapp法の信頼区間、"
         "および95%予測区間を併記した。"))
    add(("h2", "2.5 シミュレーション"))
    add(("p",
         "ADEMP構造に従い、均一ICR (シナリオA)、不均一ICR (シナリオB)、逐次追加 (シナリオC)、"
         "および構造的機序を除いた陰性対照を実施した。性能指標はモンテカルロ標準誤差とともに報告する。"
         "さらに近似重複変数を追加してICR推定量の頑健性を評価した。"))
    add(("h2", "2.6 実データ"))
    add(("p",
         f"公表されたスタチン試験{statin['n_studies']}件と強化血糖コントロール試験{glucose['n_studies']}件を"
         "CSVに出典付きで格納して解析した。ISTについては公開個票データ"
         f"({thousands(ist_sum['n_patients_raw'])}名) を用い、完全症例"
         f"{thousands(ist_sum['n_patients_complete'])}名のうち上位{ist_sum['n_countries']}か国群を"
         "疑似研究として探索的に解析した。これらは単一試験の登録層であり独立RCTではない。"))

    add(("h1", "3 結果"))
    add(("h2", "3.1 シミュレーション"))
    add(("p",
         f"平均I²はシナリオAで{pct(a['i_squared']['mean'], 1)} (MCSE {num(a['i_squared']['mcse'], 2)})、"
         f"シナリオBで{pct(b['i_squared']['mean'], 1)} (MCSE {num(b['i_squared']['mcse'], 2)})、"
         f"対応する差は{num(diff['mean_difference'], 2)}ポイント "
         f"(95%モンテカルロ信頼区間 {ci(diff['ci_lower'], diff['ci_upper'], 2)}) であった。"
         f"陰性対照の平均I²は{pct(nc['i_squared']['mean'], 1)}であり、両シナリオと同程度であった。"
         f"ICRDとI²の相関はr = {num(sim['correlation_icrd_i_squared']['r'], 3)} "
         f"({pval(sim['correlation_icrd_i_squared']['p'])}) であった (表1、図2)。"))
    add(("h2", "3.2 変数の数え方に対する感度"))
    add(("p",
         f"近似重複変数の追加によりICR_stdは{num(red['icr_std_ratio_max_to_base'], 2)}倍変化した一方、"
         f"実効次元版は{num(red['icr_effective_ratio_max_to_base'], 2)}倍にとどまった (表2)。"))
    add(("h2", "3.3 公表試験"))
    add(("p",
         f"スタチン領域ではICR_stdは{num(statin['icr_std_range'][0])}〜{num(statin['icr_std_range'][1])} "
         f"(ICRD {num(statin['icr_statistics']['icrd'], 3)})、統合効果は"
         f"{num(statin['meta_analysis']['pooled_effect'])} "
         f"{ci(statin['meta_analysis']['ci_lower'], statin['meta_analysis']['ci_upper'])}、"
         f"I² = {pct(statin['meta_analysis']['i_squared'], 1)}であった (表3)。"
         f"血糖コントロール領域ではICR_stdは{num(glucose['icr_std_range'][0])}〜"
         f"{num(glucose['icr_std_range'][1])} (ICRD {num(glucose['icr_statistics']['icrd'], 3)})、"
         f"統合効果は{num(glucose['meta_analysis']['pooled_effect'])} "
         f"{ci(glucose['meta_analysis']['ci_lower'], glucose['meta_analysis']['ci_upper'])}、"
         f"I² = {pct(glucose['meta_analysis']['i_squared'], 1)}であった (表4)。"
         "2領域の比較のみでは構造的説明と臨床的差異を区別できず、例示にとどまる (表5)。"))
    add(("h2", "3.4 IST探索的解析"))
    add(("p",
         f"loading法は{num(ist_sum['icr_pca_loading_range'][0])}〜{num(ist_sum['icr_pca_loading_range'][1])}、"
         f"回帰法は{ist_sum['icr_pca_reg_range'][0]:.5f}〜{ist_sum['icr_pca_reg_range'][1]:.5f}で変動した (表6)。"
         f"回帰法は14日死亡率と関連し (r = {num(corr['r_regression'])}, {pval(corr['p_regression'])})、"
         f"loading法では関連は認めなかった (r = {num(corr['r_loading'])}, {pval(corr['p_loading'])})。"
         "Leave-one-out解析の結果を補足表S1に示す。8群は独立でなく、この結果は仮説生成的である。"))
    add(("h2", "3.5 研究の並べ替え"))
    add(("p",
         f"ICR中央値に近い順に研究を追加しても結論到達に要する研究数は減少しなかった "
         f"(ランダム {num(conv['random']['mean_conclusive'], 2)}件、"
         f"ICR一致 {num(conv['matched']['mean_conclusive'], 2)}件、"
         f"LINKO {num(conv['linko']['mean_conclusive'], 2)}件、表7)。"))

    add(("h1", "4 考察"))
    add(("p",
         "ICRの分散が異質性を生むという仮説はシミュレーションで支持されず、ICRに基づく研究順序付けにも利点はなかった。"
         "一方でICRは計算が容易で実データ間で大きく変動する。したがってICRはプーリング妥当性の判定基準ではなく、"
         "測定変数の数と種類の報告と同列の構造的記述指標として、I²・τ²と併記するのが妥当である。"))
    add(("p",
         "限界: (1) ICR_stdは変数の計数・符号化・集約に依存する; (2) ICR_rawは尺度依存である; "
         "(3) データ生成機構は限定的である; (4) 公表2領域は例示であり小規模である; "
         "(5) ISTは単一試験の国別層であり独立研究ではない; (6) 個票データでの2値・生存時間エンドポイントは未評価である。"))

    add(("h1", "5 結論"))
    add(("p",
         "ICRは、エンドポイントが研究の測定データに占める割合を再現可能に記述する指標である。"
         "現時点の証拠では異質性の診断指標でもプーリング妥当性の基準でもなく、"
         "事前規定した計数規則のもとで報告の補助として用いるべきである。"))

    add(("h1", "データ利用可能性"))
    add(("p",
         "ISTデータはエディンバラ大学DataShare (https://datashare.ed.ac.uk/handle/10283/124) から公開されており、"
         "付属スクリプトで取得する。公表試験の抽出データと全解析コードは "
         "https://github.com/bougtoir/linko-icr-paper で公開している。本稿の全数値は単一コマンドで再生成される。"))

    add(("pagebreak", None))
    add(("h1", "参考文献"))
    add(("references", REFERENCES))

    add(("pagebreak", None))
    add(_table("表1", "シミュレーション結果 (モンテカルロ標準誤差付き)",
               ["性能指標", "シナリオA", "シナリオB", "陰性対照"], simulation_table_rows(res)))
    add(_table("表2", "近似重複変数の追加がICR推定量に与える影響",
               ["追加した重複変数", "計数変数数D", "ICR_std", "ICR_raw", "実効次元", "ICR (実効次元)"],
               redundancy_table_rows(res)))
    add(_table("表3", "スタチン試験", ["試験", "参加者数", "D", "d", "ICR_std", "ICR_raw", "対数リスク比"],
               realworld_table_rows(res, "statin")))
    add(_table("表4", "強化血糖コントロール試験",
               ["試験", "参加者数", "D", "d", "ICR_std", "ICR_raw", "対数リスク比"],
               realworld_table_rows(res, "glucose_control")))
    add(_table("表5", "τ²推定量と区間法に対する感度 (上段: スタチン、下段: 血糖コントロール)",
               ["τ²推定量", "区間法", "τ²", "統合効果", "95%CI", "95%予測区間"],
               meta_sensitivity_rows(res, "statin")
               + [["血糖コントロール", "", "", "", "", ""]]
               + meta_sensitivity_rows(res, "glucose_control")))
    add(_table("表6", "IST国別群のICR推定量",
               ["国群", "患者数", "14日死亡率", "ICR_std", "ICR_pca (loading)", "ICR_pca (回帰)", "該当主成分数"],
               ist_table_rows(res)))
    add(_table("補足表S1", "Leave-one-out感度分析",
               ["除外群", "解析群数", "r (loading)", "P (loading)", "r (回帰)", "P (回帰)"],
               loo_table_rows(res)))
    add(_table("表7", "研究順序付け戦略の比較",
               ["戦略", "結論到達までの平均研究数", "中央値", "5件以内", "10件以内", "I²<25%までの平均"],
               convergence_table_rows(res)))
    return blocks


def _extract_tables(blocks: list) -> tuple[list, dict]:
    """Remove table blocks (and their immediately preceding pagebreaks) from
    ``blocks`` and return the cleaned blocks together with the tables.
    """
    cleaned: list = []
    tables: dict[str, tuple] = {}
    pending_pagebreak = None
    for block in blocks:
        kind, payload = block
        if kind == "pagebreak":
            pending_pagebreak = block
            continue
        if kind == "table":
            tables[payload["label"]] = block
            pending_pagebreak = None
            continue
        if pending_pagebreak is not None:
            cleaned.append(pending_pagebreak)
            pending_pagebreak = None
        cleaned.append(block)
    if pending_pagebreak is not None:
        cleaned.append(pending_pagebreak)
    return cleaned, tables


def _insert_tables_inline(blocks: list) -> None:
    """Move each table block to immediately after the paragraph that first
    cites it, preserving the original table order when multiple tables share
    the same first-citation paragraph.
    """
    cleaned, tables = _extract_tables(blocks)
    first_mention: dict[str, int] = {}
    for i, (kind, payload) in enumerate(cleaned):
        if kind != "p":
            continue
        for label in tables:
            if label in first_mention:
                continue
            if label in payload:
                first_mention[label] = i
    missing = [label for label in tables if label not in first_mention]
    if missing:
        raise SystemExit(f"Tables not cited in text: {missing}")
    new_blocks: list = []
    for i, block in enumerate(cleaned):
        new_blocks.append(block)
        if block[0] == "p":
            for label, tbl in tables.items():
                if first_mention.get(label) == i:
                    new_blocks.append(tbl)
    blocks[:] = new_blocks


def prepare_manuscript(blocks: list) -> list:
    """Prepare the manuscript for rendering.

    * Replaces the raw reference list with an author-year formatted,
      alphabetically sorted list.
    * Moves each table block to immediately after the paragraph that first
      cites it.
    * Checks that no bracket-style (Vancouver) citation markers remain.
    """
    formatted = format_references()
    for index, (kind, payload) in enumerate(blocks):
        if kind == "references":
            blocks[index] = ("references", formatted)

    _insert_tables_inline(blocks)

    bracket_pattern = re.compile(r"\[(\d+(?:,\d+)*)\]")
    for kind, payload in blocks:
        if kind in ("p", "eq") and bracket_pattern.search(payload):
            raise SystemExit(
                "Vancouver-style citation marker left in the manuscript: " + payload[:80]
            )
    return blocks


def figure_blocks(blocks: list) -> list:
    return [b[1] for b in blocks if b[0] == "figure"]


def load_and_build(language: str = "en") -> list:
    res = load_results()
    return build_english(res) if language == "en" else build_japanese(res)

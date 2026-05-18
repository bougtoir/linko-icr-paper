# Information Contribution Ratio (ICR): A Novel Framework for Evaluating Meta-Analysis Validity

## 研究仕様書 (Research Specification)

---

## 1. 背景と動機 (Background and Motivation)

ランダム化比較試験（RCT）では、被験者から多数の変数（ベースライン特性、検査値、併存疾患など）が収集されるが、最終的にメタ解析で統合されるのは1つないし少数のエンドポイント（主要アウトカム）のみである。

**根本的な問い**: エンドポイントは元のRCTデータ全体のうちどれだけの「情報的重み」を持つのか？ もしその重みが研究間で大きく異なるなら、単純にエンドポイントを結合するメタ解析は妥当なのか？

### 具体例
- 10次元のデータから抽出された2次元のアウトカム（寄与度20%）
- 50次元のデータから抽出された同じ2次元のアウトカム（寄与度4%）
- これらを同等に扱って良いのか？

---

## 2. 用語定義 (Definitions)

### 2.1 Information Contribution Ratio (ICR)
RCTの全変数集合における、エンドポイント変数群が占める情報量の割合。

**分散ベースICR（Variance-based ICR; ICR_v）**:

```
ICR_v(E) = Σ_{j∈E} Var(X_j) / Σ_{j=1}^{D} Var(X_j)
```

ここで:
- D: 全変数の次元数
- E: エンドポイント変数の集合（|E| = d）
- Var(X_j): 変数jの分散（標準化後）

**主成分ベースICR（PCA-based ICR; ICR_pca）**:

```
ICR_pca(E) = Σ_{k: PC_k ∈ S_E} λ_k / Σ_{k=1}^{D} λ_k
```

ここで:
- λ_k: 第k主成分の固有値
- S_E: エンドポイント変数が支配的な主成分の集合

### 2.2 ICR Discrepancy (ICRD)
複数のRCT間でのICRの差異を測る指標。

```
ICRD = max(ICR_i) - min(ICR_i)  (i = 1, ..., K studies)
```

または変動係数:
```
ICRD_cv = SD(ICR_1, ..., ICR_K) / mean(ICR_1, ..., ICR_K)
```

---

## 3. 研究デザイン (Study Design)

### Phase 1: 理論的枠組みの構築
1. ICR_vの数学的定義と性質の証明
2. ICR_pcaの定義（個票データが利用可能な場合）
3. ICRDとメタ解析の異質性（I²統計量）の理論的関係の導出

### Phase 2: シミュレーション研究（仮想データ検証）

#### シナリオA: ICRが均一な場合
- K個のRCTを生成（各RCTで同一の次元数D、同一の共分散構造）
- エンドポイントのICRが全研究でほぼ等しい
- **期待**: メタ解析は一貫した結果を示す（低I²）

#### シナリオB: ICRが不均一な場合
- K個のRCTを生成（各RCTで異なる次元数Dまたは異なる共分散構造）
- エンドポイントのICRが研究間で大きく異なる
- **期待**: メタ解析で異質性が増大する（高I²）

#### シナリオC: 段階的メタ解析
- まず5個のRCT（均一ICR）でメタ解析 → 一貫した結果
- 追加10個のRCT（不均一ICR）を加える → 異質性増大
- 実社会で観察されるパターンの再現

#### パラメータ設定
- RCT数: K = 5, 10, 15, 20
- 変数次元数: D = 10, 20, 50, 100
- エンドポイント次元数: d = 1, 2
- サンプルサイズ: N = 100, 200, 500
- 真の効果量: δ = 0.2 (small), 0.5 (medium), 0.8 (large)
- ICR範囲: 0.02 ~ 0.50
- 繰り返し: 1000回

### Phase 3: 実社会データでの検証

#### 3a. Table1ベースのアプローチ（ICR_v）
公開論文のTable1からICR_vを算出し、メタ解析の異質性との相関を検証。

**対象候補**:
- 初期の少数RCTでは一貫した結果が得られたが、追加RCTにより異質性が増大した事例
- またはその逆

#### 3b. 個票データベースのアプローチ（ICR_pca）
個票（Individual Patient Data; IPD）が公開されているメタ解析を対象に、PCAベースのICRを算出。

**データソース候補**:
- YODA Project (Yale Open Data Access)
- ClinicalStudyDataRequest.com
- Vivli
- Cochrane IPD meta-analyses with open data
- PhysioNet (臨床試験データ)

---

## 4. 手法詳細 (Methods)

### 4.1 ICR_v の算出手順（報告データのみ）

**入力**: RCT論文のTable1（群別要約統計量）、エンドポイント結果

1. **連続変数の分散再構成**:
   ```
   μ_all = (N_I × μ_I + N_C × μ_C) / N
   Var(X_j) = [(N_I-1)σ²_{I,j} + (N_C-1)σ²_{C,j} + N_I(μ_{I,j} - μ_j)² + N_C(μ_{C,j} - μ_j)²] / (N-1)
   ```

2. **二値変数の分散**:
   ```
   p_all = (N_I × p_I + N_C × p_C) / N
   Var(X_j) = p_all(1 - p_all)
   ```

3. **標準化**: 全変数をZスコア化（分散=1に正規化）

4. **ICR_v算出**:
   ```
   ICR_v = d / D  （標準化後は各変数の分散が1なので、次元数比に近似）
   ```

   非標準化の場合:
   ```
   ICR_v = Σ_{j∈E} Var(X_j) / Σ_{j=1}^{D} Var(X_j)
   ```

### 4.2 ICR_pca の算出手順（個票データ）

**入力**: RCTの個票データ（全変数）

1. 全変数を標準化（平均0、分散1）
2. 共分散行列を計算
3. PCA実行、固有値・固有ベクトル取得
4. 各主成分に対するエンドポイント変数のローディングを計算
5. エンドポイント変数が支配的な主成分を特定
6. 当該主成分の寄与率合計 = ICR_pca

**回帰寄与度アプローチ**:
```
Y_endpoint = β_1 PC_1 + β_2 PC_2 + ... + β_D PC_D + ε
ICR_pca_reg = Σ_k (β_k² × λ_k) / Var(Y_endpoint)
```

### 4.3 メタ解析との統合

1. 各RCTのICRを算出
2. 標準的メタ解析（ランダム効果モデル）を実施
3. I²統計量、τ²を算出
4. ICRDとI²の相関を検定
5. ICR加重メタ解析の提案: ICRを重みに組み込んだ修正モデル

---

## 5. 仮説 (Hypotheses)

### 主仮説（H1）
ICRDが大きい（研究間でICRが不均一な）メタ解析は、ICRDが小さいメタ解析よりも高い異質性（I²）を示す。

### 副仮説
- **H2**: ICR_v と ICR_pca は正の相関を示す（報告データからの近似が妥当）
- **H3**: ICR加重メタ解析は、標準メタ解析よりも推定精度が高い
- **H4**: 段階的メタ解析において、ICRが均一なRCTのみの解析は安定し、ICRが不均一なRCTの追加により不安定化する

---

## 6. 出力 (Outputs)

### コード成果物
- `icr_paper/src/icr_calculator.py`: ICR_v算出コア関数
- `icr_paper/src/pca_icr_calculator.py`: ICR_pca算出（個票データ用）
- `icr_paper/src/simulation.py`: シミュレーション研究コード
- `icr_paper/src/meta_analysis.py`: メタ解析ユーティリティ
- `icr_paper/src/real_world_analysis.py`: 実社会データ分析

### 論文成果物
- `icr_paper/manuscript.md`: 論文原稿
- `icr_paper/figures/`: 図表

---

## 7. タイムライン

| Phase | 内容 | 状態 |
|-------|------|------|
| 1 | 仕様書策定 | 進行中 |
| 2 | シミュレーションコード実装・実行 | 次 |
| 3 | 実社会データ調査・分析 | 予定 |
| 4 | 論文原稿作成 | 予定 |

---

## 8. 参考文献候補

- Higgins JPT, Thompson SG. Quantifying heterogeneity in a meta-analysis. Stat Med. 2002.
- DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986.
- Riley RD, et al. Individual participant data meta-analysis. BMJ. 2010.
- Jolliffe IT. Principal Component Analysis. Springer. 2002.

---

# English Translation

---

# Information Contribution Ratio (ICR): A Novel Framework for Evaluating Meta-Analysis Validity

## Research Specification

---

## 1. Background and Motivation

Randomized controlled trials (RCTs) collect many variables from subjects (baseline characteristics, laboratory values, comorbidities, etc.), but ultimately only one or a few endpoints (primary outcomes) are combined in a meta-analysis.

**Fundamental Question**: How much “informational weight” does the endpoint have in the total original RCT data? If the weights vary widely between studies, is a meta-analysis that simply combines endpoints appropriate?

### Specific example
- 2-dimensional outcomes extracted from 10-dimensional data (20% contribution)
- Same 2-dimensional outcome extracted from 50-dimensional data (4% contribution)
- Can these be treated equally?

---

## 2. Definitions

### 2.1 Information Contribution Ratio (ICR)
The percentage of information that the endpoint variables account for in the entire variable set of an RCT.
**Variance-based ICR (ICR_v)**:

````
ICR_v(E) = Σ_{j∈E} Var(X_j) / Σ_{j=1}^{D} Var(X_j)
````

where:
- D: Number of dimensions of all variables
- E: Set of endpoint variables (|E| = d)
- Var(X_j): Variance of variable j (after standardization)

**Principal component-based ICR (PCA-based ICR; ICR_pca)**:

````
ICR_pca(E) = Σ_{k: PC_k ∈ S_E} λ_k / Σ_{k=1}^{D} λ_k
````

where:
- λ_k: Eigenvalue of the kth principal component
- S_E: Set of principal components dominated by endpoint variables

### 2.2 ICR Discrepancy (ICRD)
An index that measures the difference in ICR between multiple RCTs.

````
ICRD = max(ICR_i) - min(ICR_i) (i = 1, ..., K studies)
````

or coefficient of variation:
````
ICRD_cv = SD(ICR_1, ..., ICR_K) / mean(ICR_1, ..., ICR_K)
````

---

## 3. Study Design

### Phase 1: Building a theoretical framework
1. Mathematical definition and proof of properties of ICR_v
2. Definition of ICR_pca (if individual data is available)
3. Derivation of the theoretical relationship between ICRD and meta-analysis heterogeneity (I² statistic)

### Phase 2: Simulation research (virtual data verification)

#### Scenario A: Uniform ICR
- Generate K RCTs (same number of dimensions D, same covariance structure in each RCT)
- Endpoint ICRs are approximately equal across studies
- **Expectations**: Meta-analysis shows consistent results (low I²)

#### Scenario B: Non-uniform ICR
- Generate K RCTs (different dimensionality D or different covariance structure in each RCT)
- Endpoint ICRs vary widely between studies
- **Expectation**: Increased heterogeneity in meta-analysis (high I²)

#### Scenario C: Stepwise meta-analysis
- First, meta-analysis on 5 RCTs (uniform ICR) → Consistent results
- Add 10 additional RCTs (heterogeneity ICR) → increase heterogeneity
- Reproduction of patterns observed in the real world

#### Parameter settings
- Number of RCTs: K = 5, 10, 15, 20
- Number of variable dimensions: D = 10, 20, 50, 100
- Number of endpoint dimensions: d = 1, 2
- Sample size: N = 100, 200, 500
- True effect size: δ = 0.2 (small), 0.5 (medium), 0.8 (large)
- ICR range: 0.02 ~ 0.50
- Repeat: 1000 times

### Phase 3: Verification with real-world data

#### 3a. Table1-based approach (ICR_v)
ICR_v was calculated from Table 1 of published papers and its correlation with meta-analysis heterogeneity was verified.

**Target candidates**:
- Cases where a small number of initial RCTs yielded consistent results, but additional RCTs increased heterogeneity
- or vice versa

#### 3b. Individual data database approach (ICR_pca)
Calculate PCA-based ICR for meta-analyses for which Individual Patient Data (IPD) is publicly available.

**Data source candidates**:
- YODA Project (Yale Open Data Access)
- ClinicalStudyDataRequest.com
-Vivli
- Cochrane IPD meta-analyses with open data
- PhysioNet (clinical trial data)

---

## 4. Method details (Methods)

### 4.1 ICR_v calculation procedure (reported data only)

**Input**: Table 1 (summary statistics by group) of RCT paper, endpoint results

1. **Distributed reconstruction of continuous variables**:
   ````
μ_all = (N_I × μ_I + N_C × μ_C) / N
   Var(X_j) = [(N_I-1)σ²_{I,j} + (N_C-1)σ²_{C,j} + N_I(μ_{I,j} - μ_j)² + N_C(μ_{C,j} - μ_j)²] / (N-1)
   ````

2. **Distribution of binary variables**:
   ````
   p_all = (N_I × p_I + N_C × p_C) / N
   Var(X_j) = p_all(1 - p_all)
   ````

3. **Standardization**: Z-score all variables (normalized to variance = 1)

4. **ICR_v calculation**:
   ````
   ICR_v = d / D (approximate to the dimensionality ratio since the variance of each variable is 1 after standardization)
   ````

   For non-standardization:
   ````
   ICR_v = Σ_{j∈E} Var(X_j) / Σ_{j=1}^{D} Var(X_j)
   ````

### 4.2 ICR_pca calculation procedure (individual data)

**Input**: RCT individual data (all variables)

1. Standardize all variables (mean 0, variance 1)
2. Calculate the covariance matrix
3. PCA execution, eigenvalue/eigenvector acquisition
4. Calculate loadings of endpoint variables for each principal component
5. Identify principal components dominated by endpoint variables
6. Total contribution rate of the relevant principal component = ICR_pca

**Regression contribution approach**:
````
Y_endpoint = β_1 PC_1 + β_2 PC_2 + ... + β_D PC_D + ε
ICR_pca_reg = Σ_k (β_k² × λ_k) / Var(Y_endpoint)
````

### 4.3 Integration with meta-analysis

1. Calculate ICR for each RCT
2. Conduct standard meta-analysis (random effects model)
3. Calculate I² statistic, τ²
4. Test the correlation between ICRD and I²
5. Proposal for ICR-weighted meta-analysis: Modified model that incorporates ICR into the weights

---

## 5. Hypotheses

### Main hypothesis (H1)
Meta-analyses with large ICRDs (with heterogeneous ICRs across studies) exhibit higher heterogeneity (I²) than meta-analyses with small ICRDs.

### Subhypothesis
- **H2**: ICR_v and ICR_pca show a positive correlation (approximation from reported data is appropriate)
- **H3**: ICR weighted meta-analysis has higher estimation accuracy than standard meta-analysis
- **H4**: In stepwise meta-analysis, analysis of only RCTs with uniform ICR is stable, and addition of RCTs with heterogeneous ICR makes it unstable.

---

## 6. Outputs

### Code artifacts
- `icr_paper/src/icr_calculator.py`: ICR_v calculation core function
- `icr_paper/src/pca_icr_calculator.py`: ICR_pca calculation (for individual data)
- `icr_paper/src/simulation.py`: Simulation research code
- `icr_paper/src/meta_analysis.py`: Meta analysis utility
- `icr_paper/src/real_world_analysis.py`: Real-world data analysis

### Thesis work product
- `icr_paper/manuscript.md`: Paper manuscript
- `icr_paper/figures/`: Figures and tables

---

## 7. Timeline

| Phase | Content | Status |
|-------|------|------|
| 1 | Specification formulation | In progress |
| 2 | Simulation code implementation and execution | Next |
| 3 | Real-world data research and analysis | Schedule |
| 4 | Paper manuscript preparation | Schedule |

---

## 8. Possible references

- Higgins JPT, Thompson SG. Quantifying heterogeneity in a meta-analysis. Stat Med. 2002.
- DerSimonian R, Laird N. Meta-analysis in clinical trials. Control Clin Trials. 1986.
- Riley RD, et al. Individual participant data meta-analysis. BMJ. 2010.
- Jolliffe IT. Principal Component Analysis. Springer. 2002.


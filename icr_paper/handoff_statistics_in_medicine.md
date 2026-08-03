# LINKO → Statistics in Medicine 引き継ぎ資料

## 決定事項
- **投稿先**: Statistics in Medicine（Wiley）
- **IF (2024)**: 1.99
- **出版形態**: Hybrid
- **APC**: $5,190（Open Access選択時）/ $0（Subscription）
- **選定理由**:
  - RSMからは「方法論革新性不足」、BMC MRMからは編集基準未達の拒否を受けている
  - Statistics in Medicineは「実例を伴う新しい医学統計手法」と「明快な記述」を評価する
  - Reviewer指摘の統計的磨き上げ（estimand明確化、感度分析、現代的メタ解析手法）に対応しやすい

## 投稿履歴
- 3/31 Research Synthesis Methods → 4/3 reject（「interesting application, but does not have methodological innovation」）
- 4/7 BMC Medical Research Methodology → 8/3 editorial reject（substantial concerns, not addressable through revision）

## BMC MRM Reviewer指摘の要約

### Reviewer 1（Major）
1. **ICRの統計的意味が曖昧**: estimandを定義せず、「information」「endpoint weight」「structural comparability」「validity of pooling」が混在
2. **ICR_std = d/D の脆弱性**: 変数の数え方・コーディング・分割・集約に依存；冗長・高相関変数への感度が不明
3. **ICR_rawの尺度依存性**: 連続変数の単位、標準化ルール、2値変数 p(1-p) の問題
4. **ICRDとheterogeneityの関連が弱い**: シミュレーション I² 11.0% vs 11.7%、SD 16-17%で差が小さい
5. **実例の限界**: statinと血糖コントロールは臨床・デザイン面でも異なる；ICRDはmarkerかexplanationか不明
6. **シミュレーション設計の不足**: negative control、冗長変数、相関構造、2値/time-to-event、ICRD無関係のheterogeneityを追加
7. **メタ解析手法の陳旧化**: DerSimonian-LairdとI²のみ；REML、Paule-Mandel、Hartung-Knapp、prediction interval、Monte Carlo SEを追加
8. **IST PCAを探索的と位置づける**: 8カ国は独立RCTでなく、交絡調整・bootstrap/permuation・外部IPDが必要

### Reviewer 2（Minor/根本）
- 論文が短すぎ、詳細不足
- abstractのdiagnostic measureの目的が不明
- Table 1 statisticsとは何か不明（本文にTable 1がない）
- 「structural comparability」が誤解を招く
- I²に対する追加情報は何か
- RCTで多数のエンドポイントがあるのか（プロトコルで通常1つ定義）
- シミュレーション・実例の結果記述がない

## 修正後に必要な対応（最低限）
1. **ICRの統計的意味を明確化**: estimandを定義し、descriptorかdiagnosticか峻別
2. **変数カウント・重み付けのルールを詳述**: D/dの決め方、連続変数の標準化、2値変数の扱い、重複/高相関変数への感度分析
3. **ICRDの代替指標を検討**: weighted SD/CV/IQR/ロバストrange
4. **シミュレーションを大幅に強化**: negative control、冗長変数、2値/time-to-event、複数相関構造、REML/Paule-Mandel/HK感度分析、Monte Carlo SE
5. **実例を再解釈**: hypothesis-generating/探索的と位置づけ、臨床・デザイン要因との分離
6. **IST PCAを探索的とし、不確実性を追加**: LOO感度、bootstrapping、閾値感度、外部IPDの検討
7. **早期収束の主張を抑制**: 4.00 vs 3.94など実用的差が小さいことを正直に述べる
8. **Notation/Table/Figure整備**: notation table、D/d一覧、表番号、Prism Forest Plotの再現性（色スケール、サイズ、凡例、色覚特性）
9. **記述を軟化**: 「validity of pooling」「robust validation」「conclusive faster」→「supplementary diagnostic for structural comparability」
10. **Statistics in Medicine形式への変換**: Abstract 250語以内、新しいハイライトセクション（必要に応じ）、Wiley Vancouverスタイル

## 現在の成果物
- ブランチ: `bougtoir/wip` の `devin/1774353301-icr-paper`
- 原稿: `icr_paper/manuscript.md`
- 論文DOCX: `icr_paper/ICR_paper_english.docx`, `ICR_paper_japanese.docx`（BMC MRM形式）
- 図版PPTX: `icr_paper/ICR_figures_english.pptx`, `ICR_figures_japanese.pptx`
- 既存カバーレター: `icr_paper/cover_letter_RSM.md`, `cover_letter_BMC_MRM.md`（要SIM向け書き直し）
- 生成スクリプト: `icr_paper/generate_docx.py`, `generate_pptx.py`
- 解析コード: `icr_paper/run_analysis.py`, `icr_paper/src/`
- 仕様書: `icr_paper/specification.md`
- 他関連: `icr_paper/figures/`

## 新規セッションでの次のタスク
1. `manuscript.md` / DOCXをStatistics in Medicine形式に改変
2. Reviewer指摘に対する修正計画を具体化（上記10項目）
3. 必要な追加解析・感度分析を実装
4. 新しいカバーレター（Statistics in Medicine向け）を作成
5. 図表・表番号・引用の最終チェック
6. Research Square v2更新の検討
7. 公開リポ（bougtoir/???）への同期確認

## 他論文との配置（重複避け）
- LINKO → Statistics in Medicine（本セッション）
- IONE → Statistical Methods in Medical Research
- KOTHA → Journal of Clinical Epidemiology（臨床/GRADE強調）
- ONISHI → Research Synthesis Methods（現在審査中）

## 参考資料
- BMC MRM拒否メール内 Reviewer 1/2 attachments:
  - `ICR_review_report.docx`
  - `report-linko.docx`
- これまでのセッション履歴は Devin プラットフォーム上に保存済み

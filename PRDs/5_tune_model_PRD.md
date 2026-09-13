# PRD: 1-Month Direction Model Tuning Notebook

## 1. Product overview

### 1.1 Document title and version

- PRD: 1-Month Direction Model Tuning Notebook
- Version: 1.0

### 1.2 Product summary

This project defines a Jupyter notebook that performs systematic hyperparameter tuning for the one-month stock-direction classifier after baseline model selection is completed. The notebook consumes prepared data from step 2, baseline evaluation artifacts from step 3, and candidate recommendations from step 4, then produces tuned model artifacts and governance-ready evidence.

The tuning notebook is notebook-first and reproducible by design: all runtime settings (paths, candidate scope, search method, CV strategy, and random seeds) are configured in a dedicated section at the top. The workflow enforces time-aware validation and a one-time final test-set evaluation policy to avoid leakage and overfitting-by-iteration.

Scope is tiered: Tier-1 tuning of `MLPClassifier` is mandatory, while Tier-2 exploratory tuning of `HistGradientBoostingClassifier` is optional to test whether instability can be reduced sufficiently to become viable.

## 2. Goals

### 2.1 Business goals

- Improve out-of-sample classification quality over baseline using documented, systematic tuning.
- Create auditable artifacts that support governance decisions and future production handoff.
- Standardize the tuning process so it can be repeated for additional candidates with minimal notebook changes.

### 2.2 User goals

- Run one notebook end-to-end and obtain tuned model outputs with consistent naming.
- Compare baseline versus tuned performance with explicit lift metrics.
- Determine whether tuned models pass strict governance rules or if baseline remains provisional.

### 2.3 Non-goals

- Building ensembles or model stacking.
- Changing feature engineering, labels, or prepared-dataset schema from step 2.
- Implementing production scheduling, orchestration, or daily inference runtime.
- Downloading or refreshing market data.

## 3. User personas

### 3.1 Key user types

- Quant researcher
- ML engineer
- Retail systematic trader

### 3.2 Basic persona details

- **Quant researcher**: Wants robust model improvement while protecting time-order integrity.
- **ML engineer**: Needs machine-readable artifacts and reproducible search settings for auditability.
- **Retail systematic trader**: Needs clear pass/fail signals to avoid deploying unstable models.

### 3.3 Role-based access

- **Notebook operator**: Executes the tuning notebook and writes outputs under `5_tune_model`.
- **Project maintainer**: Updates search spaces, budget presets, and governance thresholds.

## 4. Functional requirements

- **Notebook setup and configuration block** (Priority: High)
  - Provide a top-level configuration section for:
  - Input paths to prepared data and baseline artifacts.
  - Candidate scope toggles (`run_mlp_tuning`, `run_hgb_tuning_optional`).
  - Search method (`randomized` or `grid`) and budget preset (`small`, `medium`, `large`).
  - CV settings (`n_splits`, scoring metric, random seed).
  - Output directory and filename stem policy.
  - Default to deterministic random seeds for reproducibility.

- **Input ingestion and validation** (Priority: High)
  - Load `2_prepare_data/prepared_dataset.parquet`.
  - Load baseline metrics JSON for active candidates from `3_evaluate_model`.
  - Load `4_select_model/model_comparison_baselines.json` and validate candidate recommendations.
  - Validate required columns and label set (`buy`, `hold`, `sell`).

- **Tiered candidate scope handling** (Priority: High)
  - Always include Tier-1 `mlp_classifier_baseline` as mandatory tuning candidate.
  - Allow Tier-2 optional `hist_gradient_boosting_baseline` exploratory run.
  - Persist candidate tier and rationale in output metadata.

- **Search strategy engine** (Priority: High)
  - Support `RandomizedSearchCV` and `GridSearchCV`.
  - Default policy:
  - `RandomizedSearchCV` for medium-to-large spaces.
  - `GridSearchCV` only for intentionally small, bounded spaces.
  - Enforce scoring metric `f1_macro`.
  - Enforce `refit=True` on best CV score.

- **Budget presets** (Priority: High)
  - Define preset behavior:
  - `small`: 20 sampled trials.
  - `medium`: 50 sampled trials.
  - `large`: 100 sampled trials.
  - Allow model-specific overrides when total grid cardinality is smaller than preset budget.

- **Model-specific parameter spaces** (Priority: High)
  - For `MLPClassifier` include:
  - `hidden_layer_sizes`: `(64,)`, `(128,)`, `(64, 32)`, `(128, 64)`.
  - `alpha`: `0.0001`, `0.001`, `0.01`.
  - `learning_rate_init`: `0.0005`, `0.001`, `0.003`.
  - `batch_size`: `32`, `64`, `128`.
  - `early_stopping`: `True`.
  - For optional `HistGradientBoostingClassifier`, define constrained exploratory space (for example `max_depth`, `learning_rate`, `max_leaf_nodes`, `min_samples_leaf`) with explicit warning that this path is secondary to Tier-1.

- **Time-aware cross-validation strategy** (Priority: High)
  - Use `TimeSeriesSplit` on the combined train+validation subset only.
  - Default `n_splits=4`; allow `n_splits=5` for larger budget runs.
  - No shuffling anywhere in split or CV routines.
  - Log fold date boundaries for auditability.

- **Leakage prevention controls** (Priority: High)
  - Keep the test set completely untouched during search and model selection.
  - Fit preprocessing components only on each training fold within pipeline context.
  - Permit exactly one final test evaluation per tuned candidate after final hyperparameter selection.

- **Final model refit and evaluation** (Priority: High)
  - After selecting best hyperparameters, refit model on full train+validation data.
  - Evaluate exactly once on immutable hold-out test set.
  - Compute and save the same metric schema used in baseline evaluation.

- **Baseline versus tuned comparison** (Priority: High)
  - Produce a comparison table with baseline and tuned metrics side by side.
  - Compute metric lifts at minimum for:
  - `test_macro_f1`.
  - `test_f1_buy`.
  - `test_f1_sell`.
  - Include stability delta (`val_macro_f1 - test_macro_f1`).

- **Governance and pass/fail decisioning** (Priority: High)
  - A tuned candidate passes only if all conditions are met:
  - `test_macro_f1_tuned > test_macro_f1_baseline`.
  - `test_f1_buy_tuned >= 0.20`.
  - `test_f1_sell_tuned >= 0.15`.
  - `flag_instability == False`, where instability means validation-to-test macro F1 drop greater than `0.05`.
  - If failed, baseline remains provisional candidate and failure reason is documented in JSON outputs.
  - Mark `already_tuned=true` only when systematic search is documented, final refit is executed, final test evaluation is executed once, and all required artifacts are saved.

- **Output artifact generation** (Priority: High)
  - Save tuned model pickle:
  - `5_tune_model/{MODEL_NAME}_tuned_model.pkl`.
  - Save tuned metrics JSON:
  - `5_tune_model/{MODEL_NAME}_tuned_metrics.json`.
  - Save tuned test predictions CSV:
  - `5_tune_model/{MODEL_NAME}_tuned_test_predictions.csv`.
  - Save full search-trials results CSV:
  - `5_tune_model/{MODEL_NAME}_tuning_search_results.csv`.
  - Save consolidated baseline-vs-tuned comparison table (CSV and/or JSON) in `5_tune_model`.

- **Step-6 production handoff manifest** (Priority: High)
  - Generate `5_tune_model/production_model_manifest.json` with fixed schema:
  - `model_name`, `model_type`, `model_path`, `feature_columns`, `label_mapping`, `label_thresholds`, `prediction_horizon_days`, `scaler_required`, `scaler_path`, `training_data_end`, `test_metrics`, `governance_status`, `created_at`.
  - Ensure paths in manifest are valid and project-relative.

- **Security and path-safety requirements** (Priority: Medium)
  - Restrict read/write operations to project-relative approved directories.
  - Avoid logging sensitive environment values or credentials.
  - Avoid untrusted object deserialization beyond controlled local model artifacts.

## 5. User experience

### 5.1 Entry points and first-time user flow

- Open tuning notebook in `1-month-direction-classifier/5_tune_model`.
- Review and set configuration values at the top.
- Run notebook cells top-to-bottom.
- Inspect candidate-level search results, final evaluation metrics, and governance outcome.
- Confirm artifact paths and manifest generation.

### 5.2 Core experience

- **Configure run policy**: user selects candidates, budget preset, and search method.
  - Keeps all decision levers explicit and reproducible.
- **Load data and baseline references**: notebook validates all required inputs.
  - Prevents tuning on stale or malformed sources.
- **Run CV search on train+val only**: notebook executes time-aware search and ranks trials.
  - Enforces no leakage and realistic temporal validation.
- **Refit best model and evaluate once on test**: notebook performs final hold-out check.
  - Preserves strict governance around test usage.
- **Generate outputs and governance summary**: notebook writes artifacts and pass/fail rationale.
  - Makes downstream model promotion decisions auditable.

### 5.3 Advanced features and edge cases

- Optional Tier-2 fallback candidate execution when Tier-1 fails governance.
- Automatic fallback from randomized to full grid when grid cardinality is smaller than budget.
- Graceful handling when model lacks probability outputs.
- Explicit warning if class distribution drift makes guardrails harder to satisfy.

### 5.4 UI/UX highlights

- One concise configuration block at the top of notebook.
- Fold-level and trial-level progress summaries.
- Clear baseline-vs-tuned comparison table with lift columns.
- Final governance verdict block with machine-readable status fields.

## 6. Narrative

The user opens the tuning notebook, confirms Tier-1 MLP tuning is enabled, optionally enables Tier-2 HistGradientBoosting exploration, and runs the workflow. The notebook loads prepared data and baseline artifacts, builds train/validation/test partitions chronologically, and runs `TimeSeriesSplit`-based search only on train+validation. Once best hyperparameters are selected, it refits on train+validation, touches the test set exactly once, and computes final metrics. The notebook then compares baseline versus tuned performance, applies strict governance criteria, and either promotes the tuned model as governance-pass or keeps baseline as provisional. Finally, it writes all tuned artifacts plus `production_model_manifest.json` so step 6 can load the selected production model deterministically.

## 7. Success metrics

### 7.1 User-centric metrics

- User can execute one notebook run and receive complete tuned artifacts without manual file post-processing.
- Governance decision for each tuned candidate is clear, reproducible, and documented.
- Manifest is generated and usable by step 6 without schema translation.

### 7.2 Business metrics

- At least one tuned candidate improves test macro F1 over baseline while meeting buy/sell guardrails.
- Reduced ambiguity in model promotion decisions through deterministic pass/fail policy.
- Faster handoff from experimentation to daily prediction workflow.

### 7.3 Technical metrics

- 100% of tuning runs include saved search-results CSV and tuned metrics JSON.
- 0 data leakage violations: no test-set usage during search.
- `production_model_manifest.json` validates against fixed schema on every successful run.

## 8. Technical considerations

### 8.1 Integration points

- Notebook directory: `1-month-direction-classifier/5_tune_model`.
- Input dataset: `1-month-direction-classifier/2_prepare_data/prepared_dataset.parquet`.
- Input baselines: `1-month-direction-classifier/3_evaluate_model/{MODEL_NAME}_metrics.json`.
- Input selection guidance: `1-month-direction-classifier/4_select_model/model_comparison_baselines.json`.
- Output artifacts: `1-month-direction-classifier/5_tune_model/*`.
- Downstream consumer: step-6 daily prediction notebook reads tuned model and manifest.

### 8.2 Data storage and privacy

- Local-file workflow only.
- No PII expected.
- Do not print API keys, tokens, or environment secrets in notebook logs.

### 8.3 Scalability and performance

- Use `n_jobs=-1` where estimator/search supports parallel CPU execution.
- Budget presets allow tuning depth control based on runtime budget.
- Keep optional Tier-2 tuning disabled by default to control compute cost.

### 8.4 Potential challenges

- Hold-class dominance can mask weak buy/sell behavior if relying only on aggregate metrics.
- MLP convergence sensitivity across seeds and learning-rate settings.
- HistGradientBoosting instability may persist despite tuning.
- Risk of accidental repeated test-set probing unless guardrails are enforced programmatically.

## 9. Milestones and sequencing

### 9.1 Project estimate

- Medium: 3-5 working days

### 9.2 Team size and composition

- 1-2 people: notebook developer and reviewer

### 9.3 Suggested phases

- **Phase 1**: Notebook scaffold and config contract (0.5-1 day)
  - Key deliverables: config section, path validation, candidate-tier toggles.
- **Phase 2**: Search engine and CV integration (1-2 days)
  - Key deliverables: Randomized/Grid strategy logic, TimeSeriesSplit, model spaces, budget presets.
- **Phase 3**: Final refit, test evaluation, and governance (1 day)
  - Key deliverables: one-time test evaluation controls, pass/fail implementation, comparison table.
- **Phase 4**: Artifact packaging and manifest handoff (0.5-1 day)
  - Key deliverables: tuned outputs, search-results export, production manifest, run summary.

## 10. User stories

### 10.1 Configure a reproducible tuning run

- **ID**: GH-501
- **Description**: As a notebook operator, I want one configuration section for candidates, search method, CV, budget, and random seed so I can run reproducible experiments with minimal code edits.
- **Acceptance criteria**:
  - Notebook exposes path, candidate, search, CV, and budget settings in one top configuration cell.
  - Random seed settings are explicit and used by all stochastic components.
  - Configuration values are echoed in run metadata.

### 10.2 Load and validate required inputs

- **ID**: GH-502
- **Description**: As a user, I want strict input validation so tuning only starts when prepared data and baseline/selection artifacts are present and schema-valid.
- **Acceptance criteria**:
  - Parquet dataset file exists and loads successfully.
  - Required baseline JSON files for active candidates load and pass key checks.
  - Selection JSON file loads and exposes candidate recommendations.
  - Missing files or schema errors stop execution with actionable messages.

### 10.3 Enforce tiered candidate scope

- **ID**: GH-503
- **Description**: As a maintainer, I want mandatory Tier-1 MLP tuning and optional Tier-2 HGB exploration so tuning effort is focused while preserving fallback learning.
- **Acceptance criteria**:
  - `mlp_classifier_baseline` is always included unless run is explicitly aborted.
  - `hist_gradient_boosting_baseline` runs only when optional toggle is enabled.
  - Candidate tier labels are written into outputs.

### 10.4 Execute time-aware CV search without leakage

- **ID**: GH-504
- **Description**: As a user, I want hyperparameter search to run on train+validation only with `TimeSeriesSplit` so no future information leaks into tuning decisions.
- **Acceptance criteria**:
  - Search uses `TimeSeriesSplit` with 4 folds by default and optional 5 folds.
  - No shuffling is enabled in any split operation.
  - Test data is excluded from search inputs.
  - Fold boundaries are logged for transparency.

### 10.5 Support search-method and budget presets

- **ID**: GH-505
- **Description**: As a user, I want configurable RandomizedSearchCV/GridSearchCV plus small/medium/large budgets so I can trade off runtime and exploration depth.
- **Acceptance criteria**:
  - Notebook supports both search methods.
  - Budget presets map to deterministic trial counts (`20`, `50`, `100`) unless constrained by finite grid size.
  - Effective trial count and method are saved in run metadata.

### 10.6 Refit best hyperparameters and evaluate once on test

- **ID**: GH-506
- **Description**: As a user, I want the selected best model refit on train+validation and then evaluated once on the immutable test set so final metrics remain unbiased.
- **Acceptance criteria**:
  - Best params from CV are extracted and logged.
  - Final fit uses full train+validation subset.
  - Test-set evaluation occurs exactly once per candidate after selection.
  - Test predictions and metrics are saved.

### 10.7 Compare baseline versus tuned performance

- **ID**: GH-507
- **Description**: As a user, I want side-by-side comparison outputs so I can quantify tuning lift and stability impact.
- **Acceptance criteria**:
  - Comparison includes baseline and tuned values for test macro F1, buy F1, and sell F1.
  - Lift columns are computed and saved.
  - Stability delta and instability flag are included.

### 10.8 Apply strict governance pass/fail policy

- **ID**: GH-508
- **Description**: As a decision maker, I want a deterministic governance gate so only genuinely improved and stable tuned models are considered promotable.
- **Acceptance criteria**:
  - Pass requires all four conditions:
  - tuned test macro F1 strictly greater than baseline test macro F1.
  - tuned test buy F1 at least `0.20`.
  - tuned test sell F1 at least `0.15`.
  - no instability flag (`val-test drop <= 0.05`).
  - Fail result preserves baseline as provisional candidate.
  - Failure reasons are serialized in tuned metrics JSON.

### 10.9 Mark tuned governance status correctly

- **ID**: GH-509
- **Description**: As a maintainer, I want the `already_tuned` status to reflect completed process evidence, not just changed parameters.
- **Acceptance criteria**:
  - `already_tuned` becomes true only when systematic search metadata exists.
  - Final refit and one-time test evaluation evidence is present.
  - Required artifacts are all present on disk.

### 10.10 Export standardized tuning artifacts

- **ID**: GH-510
- **Description**: As a user, I want all tuned outputs in standardized files so downstream notebooks can consume them automatically.
- **Acceptance criteria**:
  - Model pickle, metrics JSON, test predictions CSV, and search-results CSV are saved with required naming convention.
  - Paths are under `5_tune_model`.
  - Artifacts are parseable and schema-consistent.

### 10.11 Generate production manifest for step 6

- **ID**: GH-511
- **Description**: As a step-6 consumer, I want a fixed-schema manifest so I can load the production model and required metadata deterministically.
- **Acceptance criteria**:
  - `production_model_manifest.json` is generated with all required fields.
  - `model_path` and optional `scaler_path` point to valid project-relative files.
  - `governance_status` clearly indicates pass/fail and active production choice.

### 10.12 Ensure secure local execution and artifact handling

- **ID**: GH-512
- **Description**: As a maintainer, I want path-safe, controlled local execution so the notebook does not leak secrets or operate outside approved project directories.
- **Acceptance criteria**:
  - Notebook constrains I/O to project-relative allowlisted paths.
  - Sensitive runtime values are not printed.
  - Notebook avoids unsafe loading patterns for untrusted external artifacts.

## 11. Glossary and artifact schemas

### 11.1 Core glossary

- **Baseline model**: A model evaluated without systematic hyperparameter search in step 3.
- **Tuned model**: A model produced by documented CV-based hyperparameter search plus final refit and hold-out test evaluation.
- **Tier-1 candidate**: Mandatory primary tuning target (`MLPClassifier`).
- **Tier-2 candidate**: Optional exploratory fallback target (`HistGradientBoostingClassifier`).
- **Instability flag**: Boolean computed from validation-to-test macro F1 drop; true if drop is greater than `0.05`.
- **Governance pass**: Status where all four pass criteria are satisfied.
- **Provisional baseline**: Baseline model retained as temporary default when tuned candidate fails governance.

### 11.2 Tuned metrics JSON schema

Required top-level keys in `{MODEL_NAME}_tuned_metrics.json`:

- **model_name**: String, candidate identifier.
- **model_type**: String, estimator class path.
- **search_method**: String, `randomized` or `grid`.
- **search_budget**: String, `small`, `medium`, or `large`.
- **search_space**: Object, parameter distributions/grid used.
- **best_params**: Object, selected hyperparameters.
- **cv_results_summary**: Object with best CV score, rank, and trial count.
- **data**: Object with split dates and row counts.
- **baseline_test_metrics**: Object containing baseline test metric subset.
- **tuned_val_metrics**: Object containing validation metrics for tuned model.
- **tuned_test_metrics**: Object containing test metrics for tuned model.
- **comparison**: Object with baseline-vs-tuned lifts and deltas.
- **governance**: Object with pass/fail status and reasons.
- **already_tuned**: Boolean.
- **created_at**: ISO 8601 timestamp.

### 11.3 Production manifest schema

Required keys in `production_model_manifest.json`:

- **model_name**: String; production-selected model identifier.
- **model_type**: String; estimator class path.
- **model_path**: String; relative path to model pickle artifact.
- **feature_columns**: Array of strings; exact ordered feature list required at inference.
- **label_mapping**: Object; mapping between labels and encoded values if encoding is used.
- **label_thresholds**: Object; buy/sell thresholds used for label definition.
- **prediction_horizon_days**: Integer; forward horizon (20).
- **scaler_required**: Boolean; whether separate scaler artifact is required.
- **scaler_path**: String or null; relative path if scaler is persisted separately.
- **training_data_end**: Date string; last date included in final training subset.
- **test_metrics**: Object; final test metric summary for production-selected model.
- **governance_status**: Object; pass/fail decision and reason codes.
- **created_at**: ISO 8601 timestamp.

### 11.4 File naming convention

- Tuned model: `1-month-direction-classifier/5_tune_model/{MODEL_NAME}_tuned_model.pkl`
- Tuned metrics: `1-month-direction-classifier/5_tune_model/{MODEL_NAME}_tuned_metrics.json`
- Tuned test predictions: `1-month-direction-classifier/5_tune_model/{MODEL_NAME}_tuned_test_predictions.csv`
- Search results: `1-month-direction-classifier/5_tune_model/{MODEL_NAME}_tuning_search_results.csv`
- Manifest: `1-month-direction-classifier/5_tune_model/production_model_manifest.json`
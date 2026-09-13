# PRD: 1-Month Direction Daily Prediction Notebook

## 1. Product overview

### 1.1 Document title and version

- PRD: 1-Month Direction Daily Prediction Notebook
- Version: 1.0

### 1.2 Product summary

This project defines a notebook-based daily inference workflow for the production-ready one-month stock-direction classifier. The notebook reads the model manifest from step 5, loads the selected production model and feature specification, ingests the latest available data for each symbol in the configured universe, computes the same 39 features used in step 2, and generates a decision template for the current market state. The primary output is a prediction CSV that contains the latest buy/hold/sell classification, the class probabilities, and a minimal signal-strength heuristic for human review.

The workflow is intentionally notebook-first and strictly descriptive. It does not execute trades or decide portfolio actions on its own. In optional research mode, a second model is also loaded and evaluated alongside the production model to show a descriptive consensus view without granting either model any decision authority. The final design preserves a clear separation between operational inference and future consensus evaluation, which is intentionally deferred to a follow-up notebook in step 6c.

## 2. Goals

### 2.1 Business goals

- Produce a repeatable daily prediction template for the validated production model.
- Standardize how inference is performed from the trained artifacts and manifest generated in step 5.
- Make model output machine-readable, auditable, and easy to review by a human operator.
- Provide a safe optional dual-model research view without overstating confidence or creating automated decision logic.

### 2.2 User goals

- Open one notebook and run a complete prediction cycle for the current symbol universe.
- Load the production model and the exact feature schema defined in `production_model_manifest.json`.
- Receive a CSV of latest symbol-level predictions and metadata without any uncertain or hidden automation.
- Optionally inspect MLP research-only output alongside HGB production output for descriptive comparison.

### 2.3 Non-goals

- No automatic trading execution or order generation.
- No portfolio optimization or strategy execution.
- No backtesting framework or performance evaluation of consensus logic.
- No feature engineering changes from step 2.
- No model retraining or hyperparameter search in this step.
- No validated confidence layer or ensemble voting before step 6c.
- No production scheduler or orchestration service.

## 3. User personas

### 3.1 Key user types

- Quant researcher
- ML engineer
- Retail systematic trader
- Model reviewer / governance stakeholder

### 3.2 Basic persona details

- **Quant researcher**: Wants a stable daily prediction notebook that uses the approved production model and preserves the original feature contract.
- **ML engineer**: Needs deterministic file paths, manifest validation, and consistent output schema for downstream automation.
- **Retail systematic trader**: Needs a decision template that shows the model output clearly without implying that any trade is automatically approved.
- **Model reviewer / governance stakeholder**: Requires transparent metadata and explicit disclaimers so model consensus is not confused with validated decision quality.

### 3.3 Role-based access

- **Notebook operator**: Can run the notebook locally, select the symbol universe, and save prediction outputs under `1-month-direction-classifier/6_predict_data`.
- **Project maintainer**: Can update configuration values, model paths, and notebook run settings while preserving the manifest contract.
- **Reviewer**: Reads output CSVs and metadata for audit and governance review; no direct write permissions are required.

## 4. Functional requirements

- **Notebook configuration and setup block** (Priority: High)
  - Define a fixed configuration section at the top of the notebook with:
  - project root and notebook output directory,
  - universe CSV path,
  - model manifest path,
  - optional research mode toggle,
  - output filename convention,
  - random seed and deterministic settings,
  - list of required runtime libraries.
  - Keep all paths project-relative to `1-month-direction-classifier/` for reproducibility.

- **Production model manifest validation** (Priority: High)
  - Read `5_tune_model/production_model_manifest.json`.
  - Validate that the file exists and contains the required schema keys:
  - `model_name`, `model_type`, `model_path`, `feature_columns`, `label_mapping`, `label_thresholds`, `prediction_horizon_days`, `scaler_required`, `scaler_path`, `training_data_end`, `governance_status`.
  - Ensure the selected model path points to a file that exists in the project.
  - Confirm the manifest declares `governance_status.passed == true` before the production path is used.
  - Reject or warn clearly if the schema is incomplete or malformed.

- **Model loading for primary mode** (Priority: High)
  - Load the HGB production model from the path declared in the manifest.
  - Use the exact feature columns in their manifest order to preserve compatibility.
  - Use the label mapping from the manifest to convert model class indexes to `buy`, `hold`, and `sell` labels.
  - Validate that the model supports `predict()` and `predict_proba()` for inference.
  - Keep the model version and governance metadata in the output row and JSON metadata.

- **Universe and symbol data loading** (Priority: High)
  - Read the universe CSV from `data/{NAME}.csv`, where the required field is `symbol`.
  - Validate that the selected universe file exists and contains the expected field(s).
  - For each symbol, resolve the per-symbol archive file from `data/{NAME}/{SYMBOL}.csv`.
  - Load only sanitized symbol histories that are relevant to the model and preserve temporal order.
  - Validate that there is enough history to satisfy the longest feature window, especially `sma_200` and other 60-day/20-day lookbacks.

- **Minimum data sufficiency checks** (Priority: High)
  - Require at least 200 trading days of usable history for the final prediction sample.
  - Report symbols with insufficient history and exclude them from prediction output.
  - Keep a diagnostics log for skipped symbols with reason codes such as `insufficient_history`, `missing_file`, or `invalid_schema`.

- **Feature engineering parity with step 2** (Priority: High)
  - Load all required raw market data and compute the same 39 feature set used in the prepared data step.
  - Apply the same temporal ordering and per-symbol window logic to avoid mismatch between training-time and inference-time feature definitions.
  - Ensure feature columns and ordering exactly match the manifest's `feature_columns` sequence.
  - Only use the most recent row for each symbol at inference time; the notebook is not a batch training pipeline.

- **Prediction execution** (Priority: High)
  - For each valid symbol, take the most recent available row after feature engineering.
  - Run `model.predict()` to produce a label and `model.predict_proba()` to produce class probabilities.
  - Map model output indexes using `label_mapping` and output labels as `buy`, `hold`, or `sell`.
  - Save probabilities for `buy`, `hold`, and `sell` separately.
  - Include `date` as the latest trading date for that symbol, not a future-run timestamp.

- **Signal strength heuristic** (Priority: High)
  - Derive a `signal_strength` value from the probability distribution, such as:
  - top probability value,
  - gap between top two probabilities,
  - or another simple descriptive heuristic.
  - Clearly document in the notebook and output metadata that this is a rough heuristic and not a calibrated confidence measure.

- **Output CSV and metadata generation** (Priority: High)
  - Save a primary prediction output at `1-month-direction-classifier/6_predict_data/prediction_yyyy-mm-dd.csv`.
  - Required columns:
  - `date`
  - `symbol`
  - `prediction`
  - `prob_buy`
  - `prob_hold`
  - `prob_sell`
  - `signal_strength`
  - `model_name`
  - `model_version`
  - `prediction_horizon_days`
  - `close`
  - `volume`
  - `fwd_ret_20d` when available; else null/empty value
  - Keep the file human-readable and reproducible.
  - Save a JSON run artifact at `1-month-direction-classifier/6_predict_data/prediction_run_yyyy-mm-dd.json` with:
  - generated_at,
  - model_name,
  - model_version,
  - symbol_count,
  - prediction_distribution,
  - manifest_reference,
  - run_notes.

- **Notebook-first reproducibility** (Priority: High)
  - Keep the logic in a Jupyter notebook with a clear configuration section at the top.
  - Use deterministic random seeds when relevant.
  - Make all file paths, symbol universe, output naming, and model flags explicit and auditable.

- **Optional dual-model research mode** (Priority: Medium)
  - If enabled, load the optional MLP model and StandardScaler from the step 5 artifacts.
  - Label it explicitly as research-only and non-production.
  - Produce predictions for HGB and MLP side by side for the same symbols.
  - Do not assign any confidence tier or trading action to the concordance between models.

- **Consensus bucket generation in research mode** (Priority: Medium)
  - Build a descriptive 3x3 matrix category using the pair of labels:
  - `hgb_buy_mlp_buy`, `hgb_buy_mlp_hold`, `hgb_buy_mlp_sell`,
  - `hgb_hold_mlp_buy`, `hgb_hold_mlp_hold`, `hgb_hold_mlp_sell`,
  - `hgb_sell_mlp_buy`, `hgb_sell_mlp_hold`, `hgb_sell_mlp_sell`.
  - Assign `consensus_status` as one of:
  - `agreement`
  - `partial_disagreement`
  - `model_conflict`
  - Use `model_conflict` only for explicit buy/sell contradictions such as `hgb_buy_mlp_sell` and `hgb_sell_mlp_buy`.
  - Keep all consensus labels descriptive and non-evaluative.

- **Research-mode output schema** (Priority: Medium)
  - Save a secondary CSV at `1-month-direction-classifier/6_predict_data/prediction_dual_yyyy-mm-dd.csv`.
  - Include all fields from the primary mode plus:
  - `mlp_prediction`
  - `mlp_prob_buy`
  - `mlp_prob_hold`
  - `mlp_prob_sell`
  - `consensus_bucket`
  - `consensus_status`
  - Add a notebook callout and file-level disclaimer stating that consensus is a hypothesis and has not been validated out-of-sample.

- **Operational safeguard: no trade action** (Priority: High)
  - Ensure the notebook and CSV outputs clearly state that predictions are a decision template only.
  - Do not generate order tickets, execution instructions, or portfolio actions.
  - Include a plain-language disclaimer in both notebook output and final CSV metadata.

- **Future-step boundary** (Priority: Medium)
  - Define step 6c as a separate, future evaluation notebook that performs walk-forward out-of-sample analysis, bucket-level return analysis, error correlation checks, and calibration review.
  - Explicitly avoid embedding any consensus confidence claims in the current production inference notebook.

## 5. User experience

### 5.1 Entry points and first-time user flow

- Open the notebook in `1-month-direction-classifier/6_predict_data`.
- Review the configuration block at the top.
- Confirm the production manifest path and selected universe file.
- Run the notebook top-to-bottom.
- Inspect saved prediction CSVs and run metadata output.
- For research mode, enable the optional MLP section and review the descriptive dual-model summary.

### 5.2 Core experience

- **Load production model and manifest**: Notebook reads the step 5 production file and validates model and schema integrity.
  - This prevents silent use of stale or incomplete artifacts.
- **Load symbol universe and raw archives**: Notebook resolves each symbol to its local archive file and checks minimum history.
  - This reduces inference errors from missing or weak data.
- **Compute features and the latest symbol rows**: Notebook reuses step-2 feature logic and preserves the correct temporal sequence.
  - This keeps inference mathematically aligned with the trained model contract.
- **Generate live predictions**: Notebook calls the production model and saves outputs with label and probability columns.
  - This creates a decision template ready for human review.
- **Run optional research comparison**: Notebook optionally loads the MLP and produces a descriptive consensus view.
  - This provides secondary diagnostics without claiming a validated confidence layer.
- **Write outputs and disclaimer metadata**: Notebook saves prediction CSVs and research notes with explanatory disclaimers.
  - This limits overinterpretation and preserves governance clarity.

### 5.3 Advanced features and edge cases

- Universe contains symbols with missing or malformed history.
- Symbol has insufficient data for 200-day indicators.
- Model manifest points to a missing or invalid pickled object.
- Some classes have very low probability mass due to class imbalance.
- Research mode shows buy/sell conflict without making a recommendation.
- Latest symbol row is missing because of incomplete data for that day.

### 5.4 UI/UX highlights

- One top-level configuration cell for paths and toggles.
- Clear symbol-level validation summary with skipped-symbol reasons.
- Compact output tables for prediction labels and class probabilities.
- Explicit disclaimer that no trade is executed and consensus is not validated.
- Machine-readable JSON and CSV outputs for downstream review.

## 6. Narrative

The user opens the daily prediction notebook, confirms the production model manifest and symbol universe, and runs the workflow. The notebook validates the manifest, loads the HGB production model, resolves each symbol to the local archive, and computes the same 39 features used during step 2. It keeps the latest row for each symbol, scores the row with the production model, and writes a clean prediction output containing labels, probabilities, and model metadata. If research mode is enabled, the notebook also loads the MLP as a descriptive secondary model and presents a consensus summary without assigning any validated confidence layer. The result is a transparent decision template, not an automated trade, with enough metadata for a human reviewer to interpret the signal responsibly.

## 7. Success metrics

### 7.1 User-centric metrics

- User can run the notebook end-to-end without editing core logic.
- Primary prediction CSV and JSON outputs are generated for every successful run.
- Human reviewer can tell exactly which model generated the prediction, which universe was used, and what the model warning/disclaimer says.
- Research mode is clearly separated from the production path and never presented as a sanctioning authority.

### 7.2 Business metrics

- A consistent daily decision template is available for the active symbol universe.
- Model governance remains clear because HGB is the only production model in the manifest.
- Research comparison adds diagnostic visibility without creating misleading confidence claims.

### 7.3 Technical metrics

- 100% of successful runs produce valid CSV and JSON outputs.
- 0 invalid feature columns are emitted relative to the production manifest.
- 100% of skipped symbols are logged with a reason code.
- Research mode correctly labels `agreement`, `partial_disagreement`, and `model_conflict` categories without adding a validated trust score.

## 8. Technical considerations

### 8.1 Integration points

- Notebook directory: `1-month-direction-classifier/6_predict_data`.
- Input manifest: `1-month-direction-classifier/5_tune_model/production_model_manifest.json`.
- Input model artifact: `1-month-direction-classifier/5_tune_model/{MODEL_NAME}_tuned_model.pkl`.
- Input universe CSV: `1-month-direction-classifier/data/{NAME}.csv`.
- Input per-symbol archives: `1-month-direction-classifier/data/{NAME}/{SYMBOL}.csv`.
- Optional MLP research artifact: `1-month-direction-classifier/5_tune_model/mlp_classifier_baseline_tuned_model.pkl`.
- Output CSV: `1-month-direction-classifier/6_predict_data/prediction_yyyy-mm-dd.csv`.
- Output dual CSV: `1-month-direction-classifier/6_predict_data/prediction_dual_yyyy-mm-dd.csv`.
- Output metadata: `1-month-direction-classifier/6_predict_data/prediction_run_yyyy-mm-dd.json`.

### 8.2 Data storage and privacy

- The project uses local file-based storage only.
- No user identity, PII, or credential material is expected in the data pipeline.
- Model and dataset paths should remain project-relative for reproducibility and safe local execution.
- Avoid logging environment secrets or credentials as notebook output.

### 8.3 Scalability and performance

- The inference step operates on a single latest row per symbol, so runtime is modest even for nontrivial universes.
- Compute cost is dominated by feature engineering across the required history windows.
- Prefer vectorized pandas operations and efficient file handling with small cleanup overhead.
- Research mode should remain optional to keep the default daily workflow focused and fast.

### 8.4 Potential challenges

- Some per-symbol archives may be incomplete or have fewer than 200 valid trading rows.
- Feature windows such as 200-day SMA and rolling volatility measures require a stable history path.
- Label imbalance makes probability outputs noisy and not inherently calibrated.
- Consensus artifacts may be overinterpreted by users if disclaimers are not explicit.
- MLP, while useful in research mode, is not a production model and must remain separated from governance logic.

### 8.5 Future steps

- **Step 6c: Consensus Evaluation Notebook**
  - Perform walk-forward out-of-sample evaluation across consistent market windows.
  - Analyze each of the nine consensus buckets individually for hit rate, future return, drawdown, and transaction cost effects.
  - Examine error correlation and calibration across the two models.
  - Define explicit pre-registered success criteria for any future confidence-layer upgrade.
  - Only after positive evidence should a validated confidence layer be introduced to the inference workflow.

## 9. Milestones and sequencing

### 9.1 Project estimate

- Small to medium: 2-4 working days

### 9.2 Team size and composition

- 1-2 people: notebook developer and reviewer/governance validator

### 9.3 Suggested phases

- **Phase 1**: Manifest and model validation block (0.5-1 day)
  - Key deliverables: manifest parsing, file existence checks, schema validation, model load verification.
- **Phase 2**: Data ingestion and feature alignment (0.5-1 day)
  - Key deliverables: universe validation, per-symbol archive loading, history threshold checks, feature generation and latest-row selection.
- **Phase 3**: Primary prediction pipeline and outputs (0.5-1 day)
  - Key deliverables: HGB prediction, probability extraction, signal strength heuristic, CSV and JSON outputs.
- **Phase 4**: Optional research mode and behavioral guardrails (0.5-1 day)
  - Key deliverables: MLP loading, consensus bucket logic, disclaimers, dual CSV output.
- **Phase 5**: Documentation and review checklist (0.5 day)
  - Key deliverables: markdown notes, final notebook review, governance-ready output verification.

## 10. User stories

### 10.1 Load and validate the production model manifest

- **ID**: GH-006A-001
- **Description**: As a notebook operator, I want the notebook to read `production_model_manifest.json` and validate its schema so I only use a vetted production model.
- **Acceptance criteria**:
  - The notebook loads the manifest from `5_tune_model`.
  - It confirms the file exists and contains required fields.
  - It rejects malformed manifests with a clear error.
  - It confirms `governance_status.passed` is true before switching to production inference.

### 10.2 Load the correct symbol universe

- **ID**: GH-006A-002
- **Description**: As a user, I want the notebook to read a configured universe file and resolve the matching symbol archives so inference uses the correct data scope.
- **Acceptance criteria**:
  - Universe CSV exists and includes a valid symbol column.
  - Notebook resolves `data/{NAME}/{SYMBOL}.csv` for each symbol.
  - Missing symbol files are logged with a readable reason.
  - The output includes only valid symbols that pass the minimum standards.

### 10.3 Validate enough data history for inference

- **ID**: GH-006A-003
- **Description**: As a model reviewer, I want the notebook to enforce minimum-history checks so the feature deck is not computed on incomplete data.
- **Acceptance criteria**:
  - Notebook verifies each symbol has at least 200 valid trading days of required history.
  - Symbols below threshold are excluded and logged.
  - Inference runs only on symbols meeting the minimum data requirement.

### 10.4 Rebuild the production feature set exactly as trained

- **ID**: GH-006A-004
- **Description**: As a quant researcher, I want the notebook to generate the same 39 features and order as step 2 so the model sees compatibility-preserving inputs.
- **Acceptance criteria**:
  - Feature columns match the manifest in exact order.
  - The same temporal feature logic and lookbacks are used as in step 2.
  - Only the newest valid row per symbol is used for inference.

### 10.5 Generate a clean primary prediction output

- **ID**: GH-006A-005
- **Description**: As a trader, I want a prediction CSV with the latest label and probability outputs for each symbol so I can review the daily decision template.
- **Acceptance criteria**:
  - Output includes `date`, `symbol`, `prediction`, and probability columns.
  - `prediction` values are only `buy`, `hold`, or `sell`.
  - Output includes model name, version, horizon, and relevant market context fields.
  - File is saved in `6_predict_data` using a date-based naming convention.

### 10.6 Add a descriptive signal-strength heuristic

- **ID**: GH-006A-006
- **Description**: As a reviewer, I want a simple signal-strength field so the prediction output conveys rough separation without implying calibration or validated confidence.
- **Acceptance criteria**:
  - `signal_strength` is computed from class probabilities.
  - Method is documented as a heuristic only.
  - Notebook/CSV output explains it is not a calibrated confidence estimate.

### 10.7 Save run metadata for auditability

- **ID**: GH-006A-007
- **Description**: As a governance reviewer, I want a JSON run artifact so the exact runtime configuration and prediction summary are documented.
- **Acceptance criteria**:
  - JSON includes execution date, model name, symbol count, and prediction distribution.
  - Manifest reference and run notes are stored.
  - JSON is saved in the same output directory as the primary prediction file.

### 10.8 Run optional research mode without influencing production decisions

- **ID**: GH-006B-001
- **Description**: As a researcher, I want to compare the HGB production model with the MLP diagnostic model in a secondary mode without creating a false production signal.
- **Acceptance criteria**:
  - Research mode loads the MLP and scaler only when enabled.
  - Both models' predictions are shown side by side.
  - The output is labeled as research-only and not as a production signal.

### 10.9 Produce descriptive consensus buckets

- **ID**: GH-006B-002
- **Description**: As a researcher, I want descriptive consensus categories so I can inspect the relationship between HGB and MLP outputs without claiming validated trust.
- **Acceptance criteria**:
  - Notebook calculates all nine bucket combinations from the 3x3 label matrix.
  - `consensus_status` is one of `agreement`, `partial_disagreement`, or `model_conflict`.
  - `model_conflict` is only used for buy/sell contradictions.
  - No bucket is labeled as a validated confidence tier.

### 10.10 Add explicit disclaimers for consensus and automated action

- **ID**: GH-006B-003
- **Description**: As a reviewer, I want the notebook and CSV outputs to make it unambiguous that consensus is a hypothesis and no automatic trade is created.
- **Acceptance criteria**:
  - Notebook output states consensus has not been validated out-of-sample.
  - CSV metadata includes a clear no-trade disclaimer.
  - The project avoids any language implying that the consensus logic is production-grade.

### 10.11 Define a future consensus evaluation workflow

- **ID**: GH-006C-001
- **Description**: As a project maintainer, I want a clear roadmap for step 6c so the project can evaluate whether a validated confidence layer is justified before any trust claim is made.
- **Acceptance criteria**:
  - Step 6c is documented as a future workflow separate from step 6a and 6b.
  - The roadmap includes walk-forward out-of-sample evaluation, bucket analysis, error correlation, and calibration checks.
  - The document explicitly states that a confidence layer requires evidence rather than agreement alone.

## 11. Glossary

### 11.1 Core terms

- **prediction**: The final label assigned by the production model using `buy`, `hold`, or `sell`.
- **class_probabilities**: The probability vector returned by `model.predict_proba()` for the buy/hold/sell classes.
- **signal_strength**: A heuristic measure derived from the probability distribution, used as a descriptive separation metric rather than as calibrated confidence.
- **consensus_bucket**: A descriptive 3x3 label combination from the HGB and MLP outputs in research mode.
- **consensus_status**: One of `agreement`, `partial_disagreement`, or `model_conflict`; this is descriptive only and not a validated trust score.
- **prediction_horizon_days**: Fixed at 20 trading days, based on the production manifest from step 5.
- **model_conflict**: Explicit buy/sell contradiction between the two models; not an execution signal and not an automatic trade trigger.
- **validated confidence layer**: A future feature that may be introduced only after step 6c confirms out-of-sample value; it is not part of step 6a or 6b.

### 11.2 Output schema summary

Primary output columns:

- `date`
- `symbol`
- `prediction`
- `prob_buy`
- `prob_hold`
- `prob_sell`
- `signal_strength`
- `model_name`
- `model_version`
- `prediction_horizon_days`
- `close`
- `volume`
- `fwd_ret_20d` (when available; otherwise null)

Optional research output columns:

- `mlp_prediction`
- `mlp_prob_buy`
- `mlp_prob_hold`
- `mlp_prob_sell`
- `consensus_bucket`
- `consensus_status`

### 11.3 Operational guardrails

- HGB is the only production model defined by the manifest.
- MLP remains a research-only, diagnostic model.
- The notebook is a template for human decision support only.
- No automated execution, confidence stake, or portfolio action should be inferred from model agreement alone.
- A future validated confidence layer requires separate out-of-sample evidence from step 6c before it enters production design.

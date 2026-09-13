# 1-Month Direction Classifier

A machine-learning pipeline that predicts whether a stock's 1-month forward return will be **buy** (>+5%), **hold** (±5%), or **sell** (<-5%), based on 39 engineered features from daily OHLCV data.

## Pipeline Overview

```
data/{NAME}.csv (ticker universe)
    │
    ▼
┌──────────────────────────────────────────────────┐
│ 1_fetch_data     EODHD API → per-symbol CSVs     │
│                  Incremental updates, batching   │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│ 2_prepare_data   39 features + 3-class labels    │
│                  → prepared_dataset.parquet      │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│ 3_evaluate_model 6 baseline models evaluated     │
│                   Time-aware 70/15/15 splits     │
│                   JSON metrics + model pickles   │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│ 4_select_model   Leaderboard, guardrails,        │
│                  tuning recommendations          │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│ 5_tune_model     Hyperparameter tuning           │
│                  Tier-1: MLP (governance FAILED) │
│                  Tier-2: HGB (governance PASSED) │
│                  → production_model_manifest.json│
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│ 6_predict_data   Daily prediction                │
│                  Primary: HGB production model   │
│                  Research: + MLP diagnostic view │
│                  → prediction_yyyy-mm-dd.csv     │
└──────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone
git clone git@github.com:0xC0FFEE71/1-month-direction-classifier.git
cd 1-month-direction-classifier

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
cp config.example.py config.py
# Edit config.py: set EODHD_API_KEY to your key (or use 'demo' for 3 test symbols)

# 5. Run notebooks in order (1 → 6)
jupyter notebook
```

## Project Structure

```
1-month-direction-classifier/
├── 1_fetch_data/          Step 1: Data ingestion from EODHD
├── 2_prepare_data/        Step 2: Feature engineering + labeling
├── 3_evaluate_model/      Step 3: 6 baseline model evaluations
├── 4_select_model/        Step 4: Model comparison + selection
├── 5_tune_model/          Step 5: Hyperparameter tuning + governance
├── 6_predict_data/        Step 6: Daily prediction (primary + research mode)
├── PRDs/                  Product Requirements Documents (steps 1-6)
├── data/                  Universe CSVs + per-symbol OHLCV archives
│   ├── DEMO_003.csv       3-symbol demo universe (AAPL, TSLA, AMZN)
│   ├── DEMO_003/          Per-symbol CSV archives
│   ├── S&P_500.csv        S&P 500 universe (populate with EODHD subscription)
│   └── STOXX_600.csv      STOXX 600 universe (populate with EODHD subscription)
├── config.example.py      API key template (copy to config.py)
├── requirements.txt       Python dependencies
├── .python-version        Python 3.9
└── .gitignore
```

## Features (39 total)

| Category | Features |
|---|---|
| Returns | ret_1d, log_ret_1d, ret_5d, ret_10d, ret_20d, ret_60d, log_ret_5d, log_ret_20d |
| Trend | sma_5, sma_20, sma_50, sma_200, close_over_sma_*, sma_*_slope_5d |
| Volatility | vol_ret_5d/20d/60d, vol_tr_5d/20d, true_range, tr_range |
| Volume | value_traded, vol_ma_20/60, vol_rel_20, value_traded_ma_20, value_traded_rel_20 |
| Technical | rsi_14, macd, macd_signal, macd_hist, atr_14 |
| Price Context | hh_20d, ll_20d, dist_from_20d_high, dist_from_20d_low |

## Label Definition

- **buy**: forward 20-trading-day return > +5%
- **sell**: forward 20-trading-day return < -5%
- **hold**: otherwise

## Models

6 baseline models were evaluated (step 3), tuned (step 5), and governance-checked:

| Model | Test Macro F1 | Governance |
|---|---|---|
| HistGradientBoosting (tuned) | 0.394 | ✅ PASSED — **production model** |
| MLP Classifier (tuned) | 0.307 | ❌ FAILED — diagnostic only |
| HistGradientBoosting (baseline) | 0.384 | — |
| MLP Classifier (baseline) | 0.362 | — |
| Logistic Regression | 0.331 | — |
| Linear SVC | 0.314 | — |
| Extra Trees | 0.308 | — |
| Random Forest | 0.268 | — |

## Governance

A tuned model passes only if ALL conditions are met:
1. test_macro_f1_tuned > test_macro_f1_baseline
2. test_f1_buy >= 0.20
3. test_f1_sell >= 0.15
4. Val→Test macro F1 drop <= 0.05 (stability)

## Current Status

- **Data**: 3 demo symbols (AAPL.US, TSLA.US, AMZN.US) — expand to S&P 500 / STOXX 600 with EODHD subscription
- **Production model**: HistGradientBoostingClassifier (tuned, governance-passed)
- **Daily prediction**: Working in primary (HGB) and research (HGB+MLP) mode
- **Step 6c (Consensus Evaluation)**: Roadmap — not yet implemented

## Disclaimer

This project produces model predictions as a **decision template for human review only**. It does not execute trades, generate orders, or provide automated portfolio actions. Model consensus between HGB and MLP is descriptive and has **not** been validated out-of-sample.
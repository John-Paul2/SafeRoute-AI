# SafeRoute AI — Dataset Directory (CO5 & CO4)

This directory houses the processed accident parquet data and the raw US Accidents CSV dataset.

## Kaggle "US Accidents" Dataset Placement

1. **Source**: Download the dataset from Kaggle:
   - URL: https://www.kaggle.com/datasets/sobhanmohammadpour/us-accidents
   - Primary File: `US_Accidents_March23.csv` (~3.05 GB uncompressed, ~7.7 million records).

2. **Placement**:
   Place the downloaded CSV in either of these locations:
   - `backend/data/US_Accidents_March23.csv` (standard directory)
   - Or directly in the repository root: `US_Accidents_March23.csv`

   The data preparation pipeline (`ml/prepare_data.py`) automatically checks both locations.

3. **Data Security & Git Policy**:
   > **Important (AGENTS.md Rule 7)**: Never commit the raw CSV file to Git repository.
   > The raw CSV files (`*.csv`) are strictly ignored via `.gitignore`.

4. **Pipeline Output**:
   Running the data preparation script:
   ```bash
   python ml/prepare_data.py
   ```
   will filter the accidents to the configured target city/state (default: Austin, TX), sample to $\le 300\text{k}$ records, engineer spatial/temporal/weather features, and output:
   - `backend/data/clean.parquet`

Parquet format provides $\sim 10\times$ faster read speeds and high columnar compression for subsequent model training (XGBoost, Bayesian Network).

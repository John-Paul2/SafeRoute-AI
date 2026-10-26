"""
SafeRoute AI - Tabular Data Preparation & Feature Engineering
Course Outcome: CO5 (Machine Learning Techniques)
Description:
    Streams the raw US Accidents CSV in chunks, filters to a single target city/state,
    samples to <=100k rows, cleans missing values, bins Severity into a binary target
    (high_severity = Severity >= 3), engineers temporal, weather, and spatial grid features,
    and saves the cleaned dataset to clean.parquet for XGBoost and Bayesian Network training.
"""

from pathlib import Path
import os
import sys
import time
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# Configurable Constants
# ---------------------------------------------------------
TARGET_CITY = "Austin"
TARGET_STATE = "TX"
MAX_SAMPLES = 100_000
CHUNK_SIZE = 100_000
RANDOM_STATE = 42
GRID_RESOLUTION = 0.01  # ~1.1 km spatial discretization for grid_cell_id

# Target CSV candidate paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CSV_CANDIDATE_PATHS = [
    DATA_DIR / "US_Accidents_March23.csv",
    BASE_DIR.parent / "US_Accidents_March23.csv",
    Path("US_Accidents_March23.csv"),
    Path("backend/data/US_Accidents_March23.csv"),
]

USE_COLS = [
    "ID", "Severity", "Start_Time", "Start_Lat", "Start_Lng",
    "City", "State", "Temperature(F)", "Humidity(%)", "Visibility(mi)",
    "Wind_Speed(mph)", "Precipitation(in)", "Weather_Condition",
    "Sunrise_Sunset", "Junction", "Traffic_Signal"
]


def find_csv_path() -> Path:
    """Locate raw CSV dataset across standard search paths."""
    for p in CSV_CANDIDATE_PATHS:
        if p.exists():
            return p.resolve()
    raise FileNotFoundError(
        f"US_Accidents_March23.csv not found in search paths:\n"
        + "\n".join(str(p) for p in CSV_CANDIDATE_PATHS)
    )


def map_weather_condition(series: pd.Series) -> pd.Series:
    """
    Groups detailed weather condition strings into 5 broad categories:
    Clear, Rain, Fog, Snow, Other.
    """
    s = series.fillna("Clear").astype(str).str.lower()
    result = pd.Series("Other", index=series.index)

    # Precipitation & snow conditions take precedence
    result[s.str.contains("snow|sleet|ice|hail|blizzard|wintry", regex=True)] = "Snow"
    result[s.str.contains("rain|drizzle|shower|storm|thunderstorm", regex=True)] = "Rain"
    result[s.str.contains("fog|mist|haze|smoke", regex=True)] = "Fog"
    result[s.str.contains("clear|fair|cloud|overcast", regex=True)] = "Clear"

    return result


def prepare_dataset(csv_path: Path, output_path: Path):
    """
    Loads raw CSV in chunks, filters to city/state, samples, cleans,
    engineers features, and saves to parquet.
    """
    print(f"===========================================================")
    print(f"SafeRoute AI — Data Preparation Pipeline (CO5)")
    print(f"Target City / State : {TARGET_CITY}, {TARGET_STATE}")
    print(f"Max Samples Target  : {MAX_SAMPLES:,}")
    print(f"Source CSV Path     : {csv_path}")
    print(f"Output Parquet Path : {output_path}")
    print(f"===========================================================")

    t0 = time.time()
    city_chunks = []
    total_scanned = 0

    print(f"\n[1/4] Scanning CSV in chunks of {CHUNK_SIZE:,} rows...")
    for chunk in pd.read_csv(
        csv_path,
        chunksize=CHUNK_SIZE,
        usecols=USE_COLS,
        low_memory=False
    ):
        total_scanned += len(chunk)
        # Filter to target city and state
        match = chunk[(chunk["City"] == TARGET_CITY) & (chunk["State"] == TARGET_STATE)]
        if not match.empty:
            city_chunks.append(match)

        # Log progress periodically
        if total_scanned % 1_000_000 == 0:
            found_so_far = sum(len(c) for c in city_chunks)
            print(f"   Scanned {total_scanned:,} rows -> Found {found_so_far:,} {TARGET_CITY} accidents...")

    if not city_chunks:
        raise ValueError(f"No records found for {TARGET_CITY}, {TARGET_STATE} in {csv_path}")

    raw_df = pd.concat(city_chunks, ignore_index=True)
    initial_count = len(raw_df)
    print(f"   Finished scan in {time.time() - t0:.1f}s.")
    print(f"   Total {TARGET_CITY} records retrieved: {initial_count:,}")

    # [2/4] Sampling
    print(f"\n[2/4] Sampling up to {MAX_SAMPLES:,} rows...")
    if initial_count > MAX_SAMPLES:
        df = raw_df.sample(n=MAX_SAMPLES, random_state=RANDOM_STATE).reset_index(drop=True)
        print(f"   Downsampled from {initial_count:,} to {len(df):,} rows.")
    else:
        df = raw_df.copy()
        print(f"   Dataset size ({len(df):,}) is within <= {MAX_SAMPLES:,} limit.")

    # [3/4] Cleaning & Feature Engineering
    print(f"\n[3/4] Cleaning nulls and engineering features...")
    
    # 1. Clean primary nulls (drop if missing critical spatial or temporal coordinates)
    df = df.dropna(subset=["Start_Lat", "Start_Lng", "Start_Time", "Severity"]).copy()

    # 2. Binary target: high_severity (Severity >= 3)
    df["high_severity"] = (df["Severity"] >= 3).astype(int)

    # 3. Temporal features
    dt = pd.to_datetime(df["Start_Time"], errors="coerce")
    df["hour"] = dt.dt.hour.fillna(12).astype(int)
    df["day_of_week"] = dt.dt.dayofweek.fillna(0).astype(int)
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # Night flag: dataset Sunrise_Sunset ('Night'/'Day') with fallback to hour
    night_mask = (df["Sunrise_Sunset"] == "Night") | ((df["hour"] < 6) | (df["hour"] >= 20))
    df["is_night"] = night_mask.astype(int)

    # 4. Continuous weather features (median imputation for robustness)
    df["temperature"] = pd.to_numeric(df["Temperature(F)"], errors="coerce")
    df["temperature"] = df["temperature"].fillna(df["temperature"].median()).round(1)

    df["humidity"] = pd.to_numeric(df["Humidity(%)"], errors="coerce")
    df["humidity"] = df["humidity"].fillna(df["humidity"].median()).round(1)

    df["visibility"] = pd.to_numeric(df["Visibility(mi)"], errors="coerce")
    df["visibility"] = df["visibility"].fillna(10.0).round(1)

    df["wind_speed"] = pd.to_numeric(df["Wind_Speed(mph)"], errors="coerce")
    df["wind_speed"] = df["wind_speed"].fillna(df["wind_speed"].median()).round(1)

    df["precipitation"] = pd.to_numeric(df["Precipitation(in)"], errors="coerce").fillna(0.0).round(2)

    # 5. Categorical weather grouping (Clear / Rain / Fog / Snow / Other)
    df["weather_condition"] = map_weather_condition(df["Weather_Condition"])

    # 6. Road feature flags
    df["junction"] = df["Junction"].fillna(False).astype(bool).astype(int)
    df["traffic_signal"] = df["Traffic_Signal"].fillna(False).astype(bool).astype(int)

    # 7. Spatial grid cell ID
    grid_lat = (df["Start_Lat"] / GRID_RESOLUTION).astype(int)
    grid_lng = (df["Start_Lng"] / GRID_RESOLUTION).astype(int)
    df["grid_cell_id"] = "cell_" + grid_lat.astype(str) + "_" + grid_lng.astype(str)

    # Coordinate aliases for spatial graph matching
    df["latitude"] = df["Start_Lat"].round(5)
    df["longitude"] = df["Start_Lng"].round(5)

    # Final feature column selection
    final_cols = [
        "ID", "high_severity", "Severity",
        "hour", "day_of_week", "is_weekend", "is_night",
        "temperature", "humidity", "visibility", "wind_speed", "precipitation",
        "weather_condition", "junction", "traffic_signal",
        "latitude", "longitude", "grid_cell_id", "City", "State"
    ]
    df = df[final_cols]

    # [4/4] Save to Parquet
    print(f"\n[4/4] Saving clean dataset to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False, engine="pyarrow", compression="snappy")
    print(f"   Successfully wrote {len(df):,} rows ({output_path.stat().st_size / (1024 * 1024):.2f} MB).")

    # Class balance and summary
    print(f"\n===========================================================")
    print(f"DATASET SUMMARY & CLASS BALANCE (high_severity = Severity >= 3)")
    print(f"===========================================================")
    balance = df["high_severity"].value_counts(normalize=False)
    balance_pct = df["high_severity"].value_counts(normalize=True) * 100

    print(f"Total Rows: {len(df):,}")
    print(f"  Class 0 (Low Severity  1-2): {balance.get(0, 0):>7,}  ({balance_pct.get(0, 0.0):.2f}%)")
    print(f"  Class 1 (High Severity 3-4): {balance.get(1, 0):>7,}  ({balance_pct.get(1, 0.0):.2f}%)")

    print(f"\nWeather Condition Breakdown:")
    for w_cond, count in df["weather_condition"].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"  - {w_cond:<8}: {count:>7,} ({pct:.2f}%)")

    print(f"\nSpatial Coverage:")
    print(f"  Lat Range: [{df['latitude'].min():.4f}, {df['latitude'].max():.4f}]")
    print(f"  Lng Range: [{df['longitude'].min():.4f}, {df['longitude'].max():.4f}]")
    print(f"  Unique Grid Cells: {df['grid_cell_id'].nunique():,}")

    print(f"\nFeatures Head Preview:")
    print(df[["hour", "is_weekend", "is_night", "temperature", "visibility", "weather_condition", "high_severity"]].head(5).to_string())

    print(f"\nExecution finished in {time.time() - t0:.1f} seconds.")
    return df


if __name__ == "__main__":
    csv_file = find_csv_path()
    out_file = DATA_DIR / "clean.parquet"
    prepare_dataset(csv_file, out_file)

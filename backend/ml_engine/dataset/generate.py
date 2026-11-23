

"""Sarva Mitra: build sarva_mitra_final_dataset.csv for LightGBM / XGBoost regression.

Starts from the existing project dataset (sarva_mitra_regression_2000_2026.csv) and keeps its
historical values. Only the soil and elevation columns, which the existing dataset lacks, are
fetched from APIs. Each API response is cached in ./cache so reruns make no repeat requests.

Usage:
    python build_final_dataset.py [path/to/sarva_mitra_regression_2000_2026.csv]

Outputs (./reports and the final CSV):
    sarva_mitra_final_dataset.csv   15 columns, exactly as specified
    reports/data_dictionary.csv     every column, unit and source
    reports/missing_values.csv      missing counts overall and per location
    reports/correlation.csv         correlation of each feature with risk_pct
    reports/validation.txt          checks run, rows dropped, warnings

Key decisions (see the RISK INDEX section):
    * Weather (air temperature, humidity, rainfall, sunlight, soil moisture) comes from the
      existing dataset, because it is what the model was trained on. Open-Meteo is used only
      for elevation and as a fallback if a column is missing.
    * soil_ec, soil_temperature_c, nitrogen, phosphorus and potassium are not in the final schema.
      They are never generated or filled.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

INPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("D:\\SARVA-MITRA\\extra\\sarva_mitra_regression_2000_2026.csv")
OUTPUT = Path("sarva_mitra_final_dataset.csv")
CACHE = Path("cache")
REPORTS = Path("reports")
CACHE.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

FINAL_COLUMNS = ["date", "lat", "lon", "soil_moisture_pct", "air_temperature_c", "humidity_pct",
                 "sunlight_wm2", "rainfall_mm", "soil_ph", "organic_carbon", "clay_pct",
                 "sand_pct", "silt_pct", "elevation_m", "risk_pct"]
FEATURES = [c for c in FINAL_COLUMNS if c not in ("date", "risk_pct")]
TARGET = "risk_pct"

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
SOIL_PROPS = {"phh2o": "soil_ph", "soc": "organic_carbon", "clay": "clay_pct",
              "sand": "sand_pct", "silt": "silt_pct"}

# Plausible bounds. Rows that break a hard bound are dropped; soft bounds are only reported.
HARD = {"soil_moisture_pct": (0, 100), "humidity_pct": (0, 100), "rainfall_mm": (0, 1000),
        "sunlight_wm2": (0, 400), "lat": (6, 38), "lon": (68, 98)}
SOFT = {"air_temperature_c": (5, 48), "soil_ph": (3.5, 9.5), "elevation_m": (0, 6000)}

log_lines = []


def log(msg):
    print(msg, flush=True)
    log_lines.append(msg)


# ---------- risk index (documented in reports/data_dictionary.csv) ----------

def risk_components(df: pd.DataFrame) -> pd.DataFrame:
    """Seven stress components, each 0 (no stress) to 1 (maximum stress).

    Thresholds are generic, not crop-specific, because no crop was specified. They are
    prototype values to be confirmed by an agronomist or KVK officer.
    """
    c = pd.DataFrame(index=df.index)
    # Soil moisture (0-100 %): stress at drought (<20) or waterlogging (>80), full at 0 or 100.
    drought = (20 - df["soil_moisture_pct"]) / 20
    waterlog = (df["soil_moisture_pct"] - 80) / 20
    c["stress_soil_moisture"] = np.clip(np.maximum(drought, waterlog), 0, 1)
    # Air temperature: no stress in 20-30 C, full stress 10 C outside that band.
    outside = np.maximum(np.maximum(20 - df["air_temperature_c"], df["air_temperature_c"] - 30), 0)
    c["stress_air_temperature"] = np.clip(outside / 10, 0, 1)
    # Humidity: fungal infection needs prolonged high humidity. Stress from 70 %, full at 100 %.
    c["stress_humidity"] = np.clip((df["humidity_pct"] - 70) / 30, 0, 1)
    # Rainfall: heavy daily rain causes waterlogging and spreads pathogens. Full stress at 50 mm.
    c["stress_rainfall"] = np.clip(df["rainfall_mm"] / 50, 0, 1)
    # Solar radiation: low daily mean (overcast) limits growth. Full stress at 0, none above 150 W/m2.
    c["stress_solar_radiation"] = np.clip((150 - df["sunlight_wm2"]) / 150, 0, 1)
    # Soil pH: optimum 6.0-7.5 for most crops. Full stress 1.5 units outside.
    ph_dev = np.maximum(np.maximum(6.0 - df["soil_ph"], df["soil_ph"] - 7.5), 0)
    c["stress_soil_ph"] = np.clip(ph_dev / 1.5, 0, 1)
    # Organic carbon (g/kg): deficiency below 10 g/kg, full stress at 0.
    c["stress_organic_carbon"] = np.clip((10 - df["organic_carbon"]) / 10, 0, 1)
    return c


def risk_index(df: pd.DataFrame) -> pd.Series:
    """Equal-weight mean of the seven stresses, scaled to 0-100.

    Equal weights are the neutral default: there is no calibration data to rank the factors.
    Any row missing a component gets NaN, rather than a score from partial inputs.
    """
    comps = risk_components(df)
    return (100 * comps.mean(axis=1, skipna=False)).round(2)


def legacy_risk_index(df: pd.DataFrame) -> pd.Series:
    """The formula used before this build, kept only to compare with the new index."""
    wet = ((df["humidity_pct"] >= 90) | (df["rainfall_mm"] > 0)).astype(float)
    temp = np.exp(-(((df["air_temperature_c"] - 25) / 5) ** 2))
    humid = ((df["humidity_pct"] - 60) / 30).clip(0, 1)
    return 100 * wet * (0.5 * temp + 0.5 * humid)


# ---------- API calls with cache ----------

def fetch_json(url, params, tries=5):
    last = None
    for attempt in range(tries):
        try:
            print(f"    request {attempt + 1}/{tries}: {url}", flush=True)
            r = requests.get(url, params=params, timeout=120)
            if r.status_code == 200:
                print("    ok", flush=True)
                return r.json()
            if r.status_code == 429 or r.status_code >= 500:
                wait = 30 * (attempt + 1)
                print(f"    HTTP {r.status_code}, retrying in {wait}s", flush=True)
                time.sleep(wait)
                last = f"HTTP {r.status_code}"
                continue
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
        except requests.RequestException as e:
            wait = 10 * (attempt + 1)
            print(f"    network error: {e}; retrying in {wait}s", flush=True)
            last = e
            time.sleep(wait)
    raise RuntimeError(f"failed after {tries} tries: {last}")


def cached(key, fetch):
    path = CACHE / f"{key}.json"
    if path.exists():
        print(f"  cache hit: {key}", flush=True)
        return json.loads(path.read_text(encoding="utf-8"))
    print(f"  fetching: {key}", flush=True)
    data = fetch()
    print(f"  saved: {key}", flush=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def slug(name):
    return name.lower().replace(" ", "_")


def parse_soilgrids(j):
    out = {}
    for layer in j["properties"]["layers"]:
        col = SOIL_PROPS.get(layer["name"])
        if col is None:
            continue
        mean = layer["depths"][0]["values"]["mean"]
        d_factor = layer["unit_measure"]["d_factor"]
        out[col] = None if mean is None else mean / d_factor
    return out


def fetch_soil(lat, lon):
    # One property per request: lighter for the SoilGrids server, which times out on big requests.
    out = {}
    for prop in SOIL_PROPS:
        print(f"    soil property: {prop}", flush=True)
        params = [("lon", lon), ("lat", lat), ("depth", "0-5cm"), ("value", "mean"), ("property", prop)]
        out.update(parse_soilgrids(fetch_json(SOILGRIDS_URL, params)))
        time.sleep(1)
    return out


def fetch_elevation(lat, lon):
    j = fetch_json(ELEVATION_URL, {"latitude": lat, "longitude": lon})
    return j["elevation"][0]


def static_table(points: pd.DataFrame) -> pd.DataFrame:
    """One row per location: soil properties and elevation, joined on location."""
    rows, failed = [], []
    total = len(points)
    for i, (_, p) in enumerate(points.iterrows(), start=1):
        print(f"[{i}/{total}] {p.location}", flush=True)
        try:
            soil = cached(f"soil_{slug(p.location)}", lambda: fetch_soil(p.lat, p.lon))
            elev = cached(f"elev_{slug(p.location)}", lambda: fetch_elevation(p.lat, p.lon))
        except RuntimeError as e:
            # Skip this state; finished states are cached, so a rerun only fetches what is missing.
            print(f"  FAILED, skipping {p.location}: {e}", flush=True)
            failed.append(p.location)
            continue
        rows.append({"location": p.location, **{c: soil.get(c) for c in SOIL_PROPS.values()},
                     "elevation_m": elev})
        time.sleep(1)
    if failed:
        log(f"WARNING: {len(failed)} state(s) failed and were left out: {', '.join(failed)}")
        log("Rerun the script; cached states are skipped and only these are retried.")
    return pd.DataFrame(rows)


# ---------- cleaning and validation ----------

def load_base(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, parse_dates=["date"])
    log(f"loaded {len(raw):,} rows from {path}")
    df = raw[["date", "location", "lat", "lon", "soil_moisture_pct", "temperature_c",
              "humidity_pct", "sunlight_wm2", "rainfall_mm"]].rename(
        columns={"temperature_c": "air_temperature_c"})

    before = len(df)
    df = df.drop_duplicates(["location", "date"])
    log(f"duplicate (location, date) rows removed: {before - len(df)}")

    bad = pd.Series(False, index=df.index)
    for col, (lo, hi) in HARD.items():
        broken = df[col].notna() & ((df[col] < lo) | (df[col] > hi))
        if broken.any():
            log(f"hard-bound failures in {col}: {int(broken.sum())} rows (dropped)")
        bad |= broken
    df = df[~bad].copy()
    log(f"rows after hard-bound checks: {len(df):,}")

    # Sunlight gaps: interpolate up to 3 days within a location, same as training.
    df = df.sort_values(["location", "date"])
    missing_before = df["sunlight_wm2"].isna().sum()
    df["sunlight_wm2"] = df.groupby("location")["sunlight_wm2"].transform(
        lambda s: s.interpolate(limit=3, limit_direction="both"))
    log(f"sunlight_wm2 gaps: {missing_before} before, {df['sunlight_wm2'].isna().sum()} after interpolation")

    for col, (lo, hi) in SOFT.items():
        if col in df.columns:
            n = int(((df[col] < lo) | (df[col] > hi)).sum())
            if n:
                log(f"soft-bound warning: {col} outside {lo}-{hi} in {n} rows (kept, check)")
    return df


def check_coordinates(df: pd.DataFrame) -> None:
    per_loc = df.groupby("location")[["lat", "lon"]].nunique()
    if (per_loc > 1).any().any():
        log("WARNING: some locations have more than one lat/lon pair")


def validate_final(df: pd.DataFrame) -> None:
    dup = df.duplicated(["date", "lat", "lon"]).sum()
    log(f"final duplicate (date, lat, lon): {dup}")
    if list(df.columns) != FINAL_COLUMNS:
        raise AssertionError("final columns do not match the specification")
    s = df[["soil_ph", "organic_carbon"]].notna().all(axis=1).mean()
    log(f"rows with soil pH and organic carbon present: {s:.1%}")
    tex = df[["clay_pct", "sand_pct", "silt_pct"]].dropna()
    if len(tex):
        total = tex.sum(axis=1)
        off = int(((total < 95) | (total > 105)).sum())
        log(f"texture sums outside 95-105 %: {off} of {len(tex)} rows")


# ---------- reports ----------

def write_reports(df: pd.DataFrame, raw_base: pd.DataFrame) -> None:
    miss = pd.DataFrame({"missing": df[FINAL_COLUMNS].isna().sum(),
                         "missing_pct": (100 * df[FINAL_COLUMNS].isna().mean()).round(2)})
    miss.to_csv(REPORTS / "missing_values.csv")

    feats = [c for c in FEATURES if df[c].notna().any()]
    corr = df[feats + [TARGET]].corr(numeric_only=True)[TARGET].drop(TARGET).sort_values(
        key=np.abs, ascending=False)
    corr.rename("pearson_with_risk_pct").to_csv(REPORTS / "correlation.csv")

    fc = df[feats].corr().abs()
    arr = fc.to_numpy(copy=True)
    np.fill_diagonal(arr, 0)
    fc = pd.DataFrame(arr, index=fc.index, columns=fc.columns)
    pairs = fc.stack().sort_values(ascending=False).head(6)
    with open(REPORTS / "validation.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n\n")
        f.write("Top feature-feature correlations (multicollinearity check):\n")
        f.write(pairs.round(3).to_string() + "\n\n")
        f.write("Leakage: risk_pct is a function of same-day air temperature, humidity, rainfall,\n")
        f.write("sunlight and soil moisture. A model given those same-day columns learns the formula,\n")
        f.write("not disease. Train on previous-day values (lags) and a time-based split.\n")
        if TARGET in df and "legacy" in df.attrs:
            f.write(f"\nCorrelation new vs legacy index: {df.attrs['legacy']:.3f}\n")

    if df[TARGET].isna().all():
        log("WARNING: risk_pct is empty. Soil data is missing for every location.")


DICTIONARY = [
    ("date", "Existing", "date", "YYYY-MM-DD, local date (Asia/Kolkata)"),
    ("lat", "Existing", "degrees", "Representative point latitude"),
    ("lon", "Existing", "degrees", "Representative point longitude"),
    ("soil_moisture_pct", "Existing (NASA POWER GWETTOP)", "%", "Surface soil wetness; proxy, replace with sensor data going forward"),
    ("air_temperature_c", "Existing (NASA POWER T2M)", "degC", "Daily mean air temperature"),
    ("humidity_pct", "Existing (NASA POWER RH2M)", "%", "Daily mean relative humidity"),
    ("sunlight_wm2", "Existing (NASA POWER ALLSKY_SFC_SW_DWN)", "W/m2", "Daily mean shortwave radiation; 29 gaps interpolated where possible"),
    ("rainfall_mm", "Existing (NASA POWER PRECTOTCORR)", "mm/day", "Daily precipitation"),
    ("soil_ph", "SoilGrids v2.0 phh2o", "pH", "0-5 cm mean, static per location"),
    ("organic_carbon", "SoilGrids v2.0 soc", "g/kg", "0-5 cm mean, static per location"),
    ("clay_pct", "SoilGrids v2.0 clay", "%", "0-5 cm mean, static per location"),
    ("sand_pct", "SoilGrids v2.0 sand", "%", "0-5 cm mean, static per location"),
    ("silt_pct", "SoilGrids v2.0 silt", "%", "0-5 cm mean, static per location"),
    ("elevation_m", "Open-Meteo elevation API", "m", "Static per location"),
    ("risk_pct", "Derived target", "0-100", "Equal-weight mean of 7 stress components x 100. Prototype index, not validated against disease"),
]


def main():
    base = load_base(INPUT)
    check_coordinates(base)
    points = base[["location", "lat", "lon"]].drop_duplicates("location")
    log(f"locations: {len(points)}")

    static = static_table(points)
    df = base.merge(static, on="location", how="left")
    missing_soil = static[list(SOIL_PROPS.values())].isna().all(axis=1).sum()
    if missing_soil:
        log(f"WARNING: no soil data for {missing_soil} location(s)")

    df[TARGET] = risk_index(df)
    df.attrs["legacy"] = float(pd.concat([df[TARGET], legacy_risk_index(df)], axis=1).dropna().corr().iloc[0, 1]) \
        if df[TARGET].notna().any() else np.nan

    final = df[FINAL_COLUMNS].sort_values(["date", "lat", "lon"])
    final["date"] = pd.to_datetime(final["date"]).dt.strftime("%Y-%m-%d")
    final.to_csv(OUTPUT, index=False)
    log(f"wrote {OUTPUT} with {len(final):,} rows and {len(FINAL_COLUMNS)} columns")

    validate_final(final)
    pd.DataFrame(DICTIONARY, columns=["column", "source", "unit", "notes"]).to_csv(
        REPORTS / "data_dictionary.csv", index=False)
    write_reports(final, base)
    log("reports written to ./reports")


if __name__ == "__main__":
    main()
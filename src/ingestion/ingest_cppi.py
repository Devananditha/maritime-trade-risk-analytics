"""World Bank Container Port Performance Index (CPPI) Ingestion.

Parses the official World Bank CPPI Excel file 'Annex' sheet, normalizes schema,
cleans column headers, handles null values, casts types, and stages to
data/raw/dim_ports_clean.csv.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ingest_cppi")

CPPI_COLUMN_MAPPING = {
    "Port": "port_name",
    "UN/LOCODE": "un_locode",
    "Territory": "country",
    "Maritime services region": "region",
    "Rank 2025": "cppi_rank",
    "CPPI 2025": "cppi_score",
    "Berth hours in % of port hours": "berth_efficiency_ratio",
    "Number of calls in sample": "annual_call_sample",
}


def clean_cppi_dataset(
    excel_path: Path,
    sheet_name: str = "Annex",
    output_csv: Path | None = None,
) -> pd.DataFrame:
    """Read the CPPI Excel file, map columns, clean data, and save to CSV."""
    if output_csv is None:
        output_csv = Path(__file__).resolve().parents[2] / "data" / "raw" / "dim_ports_clean.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Reading CPPI sheet '{sheet_name}' from: {excel_path}")
    raw_df = pd.read_excel(excel_path, sheet_name=sheet_name)
    logger.info(f"Loaded {len(raw_df)} rows and {len(raw_df.columns)} columns from Excel.")

    # Strip column whitespaces
    raw_df.columns = [str(c).strip() for c in raw_df.columns]

    # Verify required columns exist
    missing_cols = [c for c in CPPI_COLUMN_MAPPING.keys() if c not in raw_df.columns]
    if missing_cols:
        raise KeyError(f"Missing required columns in CPPI sheet: {missing_cols}. Found: {list(raw_df.columns)}")

    # Select and rename
    df = raw_df[list(CPPI_COLUMN_MAPPING.keys())].copy()
    df.rename(columns=CPPI_COLUMN_MAPPING, inplace=True)

    # Filter invalid/null ports
    initial_count = len(df)
    df = df.dropna(subset=["port_name"]).copy()
    df["port_name"] = df["port_name"].astype(str).str.strip()
    df = df[df["port_name"] != ""].copy()

    # Clean un_locode
    if "un_locode" in df.columns:
        df["un_locode"] = df["un_locode"].astype(str).str.strip()
        df["un_locode"] = df["un_locode"].replace({"nan": None, "None": None, "": None})

    # Numeric formatting and conversions
    df["cppi_rank"] = pd.to_numeric(df["cppi_rank"], errors="coerce").astype("Int64")
    df["cppi_score"] = pd.to_numeric(df["cppi_score"], errors="coerce")
    df["berth_efficiency_ratio"] = pd.to_numeric(df["berth_efficiency_ratio"], errors="coerce")
    df["annual_call_sample"] = pd.to_numeric(df["annual_call_sample"], errors="coerce")

    # Clean country and region
    df["country"] = df["country"].astype(str).str.strip().replace({"nan": None, "None": None})
    df["region"] = df["region"].astype(str).str.strip().replace({"nan": None, "None": None})

    # Reset index and generate surrogate primary key port_id
    df.reset_index(drop=True, inplace=True)
    df.insert(0, "port_id", range(1, len(df) + 1))

    logger.info(f"Cleaned CPPI dataset: {len(df)} ports retained (from {initial_count} raw rows).")
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved clean ports dimension to: {output_csv}")

    return df


if __name__ == "__main__":
    from src.ingestion.stage_downloads import find_latest_cppi_source
    cppi_file = find_latest_cppi_source()
    clean_cppi_dataset(cppi_file)

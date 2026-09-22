"""AIS Vessel Telemetry Ingestion and Streaming Coordinate Validator.

Processes large-scale AIS telemetry files in high-performance chunks, normalizes
headers, validates spatial coordinates and kinematics, assigns geofenced chokepoints,
extracts unique vessels, and writes clean partitioned/streamed datasets.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Iterator
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ingest_ais")

AIS_FIELD_VARIANTS: dict[str, list[str]] = {
    "mmsi": ["mmsi", "mmsi_id"],
    "timestamp": ["base_date_time", "basedatetime", "# timestamp", "timestamp", "datetime", "date_time_utc"],
    "latitude": ["latitude", "lat", "y"],
    "longitude": ["longitude", "lon", "long", "x"],
    "sog_knots": ["sog", "speedoverground", "speed_over_ground", "speed", "sog_knots"],
    "cog_degrees": ["cog", "courseoverground", "course_over_ground", "course", "cog_degrees"],
    "vessel_type": ["vessel_type", "vesseltype", "ship_type", "shiptype"],
    "vessel_name": ["vessel_name", "vesselname", "ship_name", "shipname"],
}


def resolve_ais_columns(raw_columns: list[str]) -> dict[str, str]:
    """Map raw column headers to standardized names regardless of case/format."""
    col_lookup = {c.strip().lower(): c for c in raw_columns}
    rename_map = {}

    for target_name, variants in AIS_FIELD_VARIANTS.items():
        matched = False
        for v in variants:
            if v in col_lookup:
                rename_map[col_lookup[v]] = target_name
                matched = True
                break
        if not matched and target_name in ["mmsi", "timestamp", "latitude", "longitude"]:
            raise KeyError(f"Required AIS field '{target_name}' not found in columns: {raw_columns}")

    return rename_map


def validate_coordinates(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    sog_col: str = "sog_knots",
    cog_col: str = "cog_degrees",
) -> pd.DataFrame:
    """Validate spatial coordinates and kinematic attributes.
    
    Filters out:
    - Latitude outside [-90.0, 90.0]
    - Longitude outside [-180.0, 180.0]
    - SOG < 0.0 or SOG > 102.2 (AIS standard max speed indicator)
    - COG < 0.0 or COG > 360.0
    - Null / NaN coordinates or MMSI
    """
    valid_mask = (
        df["mmsi"].notna()
        & (df["mmsi"] > 10000000)  # Valid MMSI has 9 digits
        & df[lat_col].notna()
        & df[lon_col].notna()
        & (df[lat_col] >= -90.0)
        & (df[lat_col] <= 90.0)
        & (df[lon_col] >= -180.0)
        & (df[lon_col] <= 180.0)
    )

    if sog_col in df.columns:
        valid_sog = df[sog_col].isna() | ((df[sog_col] >= 0.0) & (df[sog_col] <= 102.2))
        valid_mask = valid_mask & valid_sog

    if cog_col in df.columns:
        valid_cog = df[cog_col].isna() | ((df[cog_col] >= 0.0) & (df[cog_col] <= 360.0))
        valid_mask = valid_mask & valid_cog

    return df[valid_mask].copy()


def tag_chokepoints(df: pd.DataFrame, chokepoints: list[dict] | None = None) -> pd.DataFrame:
    """Tag AIS pings that fall inside predefined chokepoint bounding boxes."""
    if chokepoints is None:
        from src.ingestion.seed_reference_data import CHOKEPOINTS_DATA
        chokepoints = CHOKEPOINTS_DATA

    df["chokepoint_id"] = None
    for cp in chokepoints:
        cid = cp["chokepoint_id"]
        lat_min, lat_max = cp["lat_min"], cp["lat_max"]
        lon_min, lon_max = cp["lon_min"], cp["lon_max"]

        mask = (
            (df["latitude"] >= lat_min)
            & (df["latitude"] <= lat_max)
            & (df["longitude"] >= lon_min)
            & (df["longitude"] <= lon_max)
        )
        df.loc[mask, "chokepoint_id"] = cid

    return df


def stream_process_ais(
    raw_csv_path: Path,
    output_pings_csv: Path | None = None,
    output_vessels_csv: Path | None = None,
    chunk_size: int = 100_000,
    max_total_rows: int | None = None,
    tag_geofences: bool = True,
) -> tuple[int, int]:
    """Stream process raw AIS telemetry in memory-safe chunks.
    
    Returns (total_pings_processed, total_unique_vessels).
    """
    if output_pings_csv is None:
        output_pings_csv = Path(__file__).resolve().parents[2] / "data" / "processed" / "fact_ais_pings_clean.csv"
    if output_vessels_csv is None:
        output_vessels_csv = Path(__file__).resolve().parents[2] / "data" / "processed" / "dim_vessels_clean.csv"

    output_pings_csv.parent.mkdir(parents=True, exist_ok=True)
    output_vessels_csv.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting chunked stream processing of AIS data from: {raw_csv_path}")

    # Read initial chunk to detect columns
    sample = pd.read_csv(raw_csv_path, nrows=5)
    rename_map = resolve_ais_columns(sample.columns.tolist())
    logger.info(f"Resolved AIS column mapping: {rename_map}")

    total_valid_pings = 0
    unique_vessels: dict[int, dict] = {}
    is_first_chunk = True
    ping_id_counter = 1

    reader: Iterator[pd.DataFrame] = pd.read_csv(
        raw_csv_path,
        chunksize=chunk_size,
        low_memory=False,
    )

    for chunk_idx, chunk in enumerate(reader):
        chunk.rename(columns=rename_map, inplace=True)

        # Retain only recognized columns
        keep_cols = [c for c in AIS_FIELD_VARIANTS.keys() if c in chunk.columns]
        chunk = chunk[keep_cols].copy()

        # Coerce types
        chunk["mmsi"] = pd.to_numeric(chunk["mmsi"], errors="coerce")
        chunk["latitude"] = pd.to_numeric(chunk["latitude"], errors="coerce")
        chunk["longitude"] = pd.to_numeric(chunk["longitude"], errors="coerce")
        if "sog_knots" in chunk.columns:
            chunk["sog_knots"] = pd.to_numeric(chunk["sog_knots"], errors="coerce")
        if "cog_degrees" in chunk.columns:
            chunk["cog_degrees"] = pd.to_numeric(chunk["cog_degrees"], errors="coerce")

        chunk = validate_coordinates(chunk)
        if chunk.empty:
            continue

        # Extract vessel info
        if "vessel_name" in chunk.columns or "vessel_type" in chunk.columns:
            for _, row in chunk.drop_duplicates(subset=["mmsi"]).iterrows():
                mmsi_val = int(row["mmsi"])
                if mmsi_val not in unique_vessels:
                    unique_vessels[mmsi_val] = {
                        "mmsi": mmsi_val,
                        "vessel_name": str(row.get("vessel_name", "")).strip() or None,
                        "vessel_type": str(row.get("vessel_type", "")).strip() or None,
                        "scnt": None,
                        "dwt": None,
                        "daily_charter_usd": None,
                        "fuel_burn_tons_day": None,
                    }

        # Tag chokepoints
        if tag_geofences:
            chunk = tag_chokepoints(chunk)
        else:
            chunk["chokepoint_id"] = None

        # Format pings for fact_ais_pings
        chunk.insert(0, "ping_id", range(ping_id_counter, ping_id_counter + len(chunk)))
        ping_id_counter += len(chunk)

        ping_cols = ["ping_id", "mmsi", "timestamp", "latitude", "longitude", "sog_knots", "cog_degrees", "chokepoint_id"]
        # Ensure all columns exist
        for col in ping_cols:
            if col not in chunk.columns:
                chunk[col] = None
        pings_df = chunk[ping_cols]

        # Append to CSV
        pings_df.to_csv(
            output_pings_csv,
            mode="w" if is_first_chunk else "a",
            header=is_first_chunk,
            index=False,
        )
        is_first_chunk = False
        total_valid_pings += len(pings_df)

        if (chunk_idx + 1) % 5 == 0 or max_total_rows is not None:
            logger.info(f"Streamed chunk {chunk_idx + 1}: {total_valid_pings:,} cumulative valid pings...")

        if max_total_rows is not None and total_valid_pings >= max_total_rows:
            logger.info(f"Reached row threshold {max_total_rows:,}. Halting stream.")
            break

    # Save unique vessels
    vessels_df = pd.DataFrame(list(unique_vessels.values()))
    vessels_df.to_csv(output_vessels_csv, index=False)
    logger.info(f"Completed AIS ingestion: {total_valid_pings:,} valid pings -> {output_pings_csv}")
    logger.info(f"Extracted {len(vessels_df):,} distinct vessels -> {output_vessels_csv}")

    return total_valid_pings, len(vessels_df)


if __name__ == "__main__":
    raw_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "ais_telemetry_raw.csv"
    if raw_path.exists():
        stream_process_ais(raw_path, max_total_rows=100_000)
    else:
        logger.warning(f"Raw AIS CSV not found at {raw_path}. Run stage_downloads first.")

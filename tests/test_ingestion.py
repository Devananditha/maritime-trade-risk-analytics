"""Unit tests for AIS and CPPI data ingestion and validation."""

from pathlib import Path
import pandas as pd
import pytest

from src.ingestion.ingest_ais import (
    resolve_ais_columns,
    validate_coordinates,
    tag_chokepoints,
)
from src.ingestion.seed_reference_data import (
    seed_suez_toll_tiers,
    seed_chokepoints,
    SUEZ_TOLL_TIERS_DATA,
    CHOKEPOINTS_DATA,
)


def test_resolve_ais_columns():
    """Verify mapping of heterogeneous column headers to normalized names."""
    raw_cols = ["MMSI", "BaseDateTime", "LAT", "LON", "SOG", "COG", "VesselType", "VesselName"]
    resolved = resolve_ais_columns(raw_cols)
    assert resolved["MMSI"] == "mmsi"
    assert resolved["BaseDateTime"] == "timestamp"
    assert resolved["LAT"] == "latitude"
    assert resolved["LON"] == "longitude"
    assert resolved["SOG"] == "sog_knots"
    assert resolved["COG"] == "cog_degrees"


def test_validate_coordinates():
    """Verify coordinate and kinematic validation filters out corrupted pings."""
    df = pd.DataFrame([
        # Valid ping
        {"mmsi": 211234567, "latitude": 30.5, "longitude": 32.5, "sog_knots": 12.0, "cog_degrees": 180.0},
        # Invalid latitude (>90)
        {"mmsi": 211234568, "latitude": 95.0, "longitude": 32.5, "sog_knots": 12.0, "cog_degrees": 180.0},
        # Invalid longitude (<-180)
        {"mmsi": 211234569, "latitude": 30.5, "longitude": -190.0, "sog_knots": 12.0, "cog_degrees": 180.0},
        # Negative SOG
        {"mmsi": 211234570, "latitude": 30.5, "longitude": 32.5, "sog_knots": -2.0, "cog_degrees": 180.0},
        # Out-of-range COG (>360)
        {"mmsi": 211234571, "latitude": 30.5, "longitude": 32.5, "sog_knots": 10.0, "cog_degrees": 400.0},
        # Invalid MMSI (< 10000000)
        {"mmsi": 1234, "latitude": 30.5, "longitude": 32.5, "sog_knots": 10.0, "cog_degrees": 180.0},
    ])

    clean = validate_coordinates(df)
    assert len(clean) == 1
    assert clean.iloc[0]["mmsi"] == 211234567


def test_tag_chokepoints_geofence():
    """Verify spatial bounding box tags pings within chokepoints correctly."""
    df = pd.DataFrame([
        # Inside Suez Canal (lat: 29.8 - 31.35, lon: 32.2 - 32.7)
        {"mmsi": 211234567, "latitude": 30.5, "longitude": 32.5},
        # Open Atlantic Ocean (outside any chokepoint)
        {"mmsi": 211234568, "latitude": 20.0, "longitude": -40.0},
        # Inside Bab-el-Mandeb (lat: 12.2 - 13.5, lon: 43.0 - 44.0)
        {"mmsi": 211234569, "latitude": 12.8, "longitude": 43.5},
    ])

    tagged = tag_chokepoints(df, chokepoints=CHOKEPOINTS_DATA)
    assert tagged.iloc[0]["chokepoint_id"] == 1  # Suez
    assert pd.isna(tagged.iloc[1]["chokepoint_id"])  # Open ocean
    assert tagged.iloc[2]["chokepoint_id"] == 2  # Bab-el-Mandeb


def test_seed_reference_data_integrity(tmp_path: Path):
    """Verify static reference datasets export with schema conformance."""
    suez_csv = tmp_path / "dim_suez_toll_tiers.csv"
    choke_csv = tmp_path / "dim_chokepoints.csv"

    seed_suez_toll_tiers(suez_csv)
    seed_chokepoints(choke_csv)

    suez_df = pd.read_csv(suez_csv)
    choke_df = pd.read_csv(choke_csv)

    assert len(suez_df) == len(SUEZ_TOLL_TIERS_DATA)
    assert len(choke_df) == 5
    assert "tier_1_first_5k" in suez_df.columns
    assert "tier_7_next_60k" in suez_df.columns
    assert "cape_diversion_added_days" in choke_df.columns

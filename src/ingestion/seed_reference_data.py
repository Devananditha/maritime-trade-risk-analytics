"""Seed reference data module.

Generates official Suez Canal Authority (SCA) progressive toll rate cards (dim_suez_toll_tiers.csv)
and strategic maritime chokepoints geofences (dim_chokepoints.csv) in data/raw/.
"""

from __future__ import annotations

import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("seed_reference_data")

# Official Suez Canal Authority 2024 progressive tariff cards (SDR per SCNT)
SUEZ_TOLL_TIERS_DATA = [
    {
        "vessel_type": "Crude Oil Tankers",
        "condition": "Laden",
        "tier_1_first_5k": 11.04,
        "tier_2_next_5k": 7.82,
        "tier_3_next_10k": 5.91,
        "tier_4_next_20k": 2.93,
        "tier_5_next_30k": 2.53,
        "tier_6_next_50k": 2.17,
        "tier_7_next_60k": 2.13,
        "tier_8_the_rest": 2.13,
    },
    {
        "vessel_type": "Crude Oil Tankers",
        "condition": "Ballast",
        "tier_1_first_5k": 9.40,
        "tier_2_next_5k": 6.64,
        "tier_3_next_10k": 5.04,
        "tier_4_next_20k": 2.50,
        "tier_5_next_30k": 2.14,
        "tier_6_next_50k": 1.85,
        "tier_7_next_60k": 1.82,
        "tier_8_the_rest": 1.82,
    },
    {
        "vessel_type": "Petroleum Products Tankers",
        "condition": "Laden",
        "tier_1_first_5k": 11.04,
        "tier_2_next_5k": 7.82,
        "tier_3_next_10k": 5.91,
        "tier_4_next_20k": 3.93,
        "tier_5_next_30k": 3.84,
        "tier_6_next_50k": 3.46,
        "tier_7_next_60k": 3.34,
        "tier_8_the_rest": 3.34,
    },
    {
        "vessel_type": "Petroleum Products Tankers",
        "condition": "Ballast",
        "tier_1_first_5k": 9.40,
        "tier_2_next_5k": 6.64,
        "tier_3_next_10k": 5.04,
        "tier_4_next_20k": 2.50,
        "tier_5_next_30k": 2.14,
        "tier_6_next_50k": 1.85,
        "tier_7_next_60k": 1.82,
        "tier_8_the_rest": 1.82,
    },
    {
        "vessel_type": "Dry Bulk Vessels",
        "condition": "Laden",
        "tier_1_first_5k": 10.13,
        "tier_2_next_5k": 7.74,
        "tier_3_next_10k": 6.12,
        "tier_4_next_20k": 2.24,
        "tier_5_next_30k": 1.97,
        "tier_6_next_50k": 1.85,
        "tier_7_next_60k": 1.77,
        "tier_8_the_rest": 1.77,
    },
    {
        "vessel_type": "Dry Bulk Vessels",
        "condition": "Ballast",
        "tier_1_first_5k": 8.62,
        "tier_2_next_5k": 6.58,
        "tier_3_next_10k": 5.21,
        "tier_4_next_20k": 1.89,
        "tier_5_next_30k": 1.68,
        "tier_6_next_50k": 1.58,
        "tier_7_next_60k": 1.50,
        "tier_8_the_rest": 1.50,
    },
    {
        "vessel_type": "Liquefied Petroleum Gas (LPG) Carriers",
        "condition": "Laden",
        "tier_1_first_5k": 11.60,
        "tier_2_next_5k": 8.40,
        "tier_3_next_10k": 6.22,
        "tier_4_next_20k": 5.05,
        "tier_5_next_30k": 4.42,
        "tier_6_next_50k": 4.13,
        "tier_7_next_60k": 4.13,
        "tier_8_the_rest": 4.13,
    },
    {
        "vessel_type": "Liquefied Petroleum Gas (LPG) Carriers",
        "condition": "Ballast",
        "tier_1_first_5k": 9.87,
        "tier_2_next_5k": 7.14,
        "tier_3_next_10k": 5.29,
        "tier_4_next_20k": 4.30,
        "tier_5_next_30k": 3.76,
        "tier_6_next_50k": 3.51,
        "tier_7_next_60k": 3.51,
        "tier_8_the_rest": 3.51,
    },
    {
        "vessel_type": "Liquefied Natural Gas (LNG) Carriers",
        "condition": "Laden",
        "tier_1_first_5k": 10.42,
        "tier_2_next_5k": 8.11,
        "tier_3_next_10k": 7.02,
        "tier_4_next_20k": 5.43,
        "tier_5_next_30k": 5.03,
        "tier_6_next_50k": 4.80,
        "tier_7_next_60k": 4.67,
        "tier_8_the_rest": 4.67,
    },
    {
        "vessel_type": "Liquefied Natural Gas (LNG) Carriers",
        "condition": "Ballast",
        "tier_1_first_5k": 8.87,
        "tier_2_next_5k": 6.89,
        "tier_3_next_10k": 5.97,
        "tier_4_next_20k": 4.61,
        "tier_5_next_30k": 4.27,
        "tier_6_next_50k": 4.08,
        "tier_7_next_60k": 3.97,
        "tier_8_the_rest": 3.97,
    },
    {
        "vessel_type": "Chemical Tankers & Liquid Bulk",
        "condition": "Laden",
        "tier_1_first_5k": 11.55,
        "tier_2_next_5k": 8.92,
        "tier_3_next_10k": 7.12,
        "tier_4_next_20k": 5.19,
        "tier_5_next_30k": 4.63,
        "tier_6_next_50k": 4.35,
        "tier_7_next_60k": 4.27,
        "tier_8_the_rest": 4.27,
    },
    {
        "vessel_type": "Chemical Tankers & Liquid Bulk",
        "condition": "Ballast",
        "tier_1_first_5k": 9.81,
        "tier_2_next_5k": 7.58,
        "tier_3_next_10k": 6.06,
        "tier_4_next_20k": 4.42,
        "tier_5_next_30k": 3.94,
        "tier_6_next_50k": 3.70,
        "tier_7_next_60k": 3.63,
        "tier_8_the_rest": 3.63,
    },
    {
        "vessel_type": "Container Ships",
        "condition": "Laden",
        "tier_1_first_5k": 11.04,
        "tier_2_next_5k": 7.58,
        "tier_3_next_10k": 5.89,
        "tier_4_next_20k": 4.13,
        "tier_5_next_30k": 3.82,
        "tier_6_next_50k": 3.01,
        "tier_7_next_60k": 2.94,
        "tier_8_the_rest": 2.88,
    },
    {
        "vessel_type": "Container Ships",
        "condition": "Ballast",
        "tier_1_first_5k": 9.40,
        "tier_2_next_5k": 6.45,
        "tier_3_next_10k": 5.00,
        "tier_4_next_20k": 3.51,
        "tier_5_next_30k": 3.25,
        "tier_6_next_50k": 2.56,
        "tier_7_next_60k": 2.52,
        "tier_8_the_rest": 2.44,
    },
    {
        "vessel_type": "General Cargo Vessels",
        "condition": "Laden",
        "tier_1_first_5k": 10.08,
        "tier_2_next_5k": 7.78,
        "tier_3_next_10k": 5.42,
        "tier_4_next_20k": 4.07,
        "tier_5_next_30k": 3.94,
        "tier_6_next_50k": 3.87,
        "tier_7_next_60k": 3.80,
        "tier_8_the_rest": 3.80,
    },
    {
        "vessel_type": "General Cargo Vessels",
        "condition": "Ballast",
        "tier_1_first_5k": 8.58,
        "tier_2_next_5k": 6.62,
        "tier_3_next_10k": 4.61,
        "tier_4_next_20k": 3.45,
        "tier_5_next_30k": 3.36,
        "tier_6_next_50k": 3.30,
        "tier_7_next_60k": 3.22,
        "tier_8_the_rest": 3.22,
    },
    {
        "vessel_type": "Roll-On/Roll-Off (Ro/Ro) Vessels",
        "condition": "Laden",
        "tier_1_first_5k": 10.08,
        "tier_2_next_5k": 7.50,
        "tier_3_next_10k": 5.83,
        "tier_4_next_20k": 4.21,
        "tier_5_next_30k": 3.94,
        "tier_6_next_50k": 3.80,
        "tier_7_next_60k": 3.65,
        "tier_8_the_rest": 3.65,
    },
    {
        "vessel_type": "Roll-On/Roll-Off (Ro/Ro) Vessels",
        "condition": "Ballast",
        "tier_1_first_5k": 8.58,
        "tier_2_next_5k": 6.37,
        "tier_3_next_10k": 4.97,
        "tier_4_next_20k": 3.59,
        "tier_5_next_30k": 3.36,
        "tier_6_next_50k": 3.22,
        "tier_7_next_60k": 3.12,
        "tier_8_the_rest": 3.12,
    },
    {
        "vessel_type": "Vehicles Carriers",
        "condition": "Laden",
        "tier_1_first_5k": 11.04,
        "tier_2_next_5k": 7.58,
        "tier_3_next_10k": 5.67,
        "tier_4_next_20k": 4.05,
        "tier_5_next_30k": 3.82,
        "tier_6_next_50k": 3.01,
        "tier_7_next_60k": 2.88,
        "tier_8_the_rest": 2.88,
    },
    {
        "vessel_type": "Vehicles Carriers",
        "condition": "Ballast",
        "tier_1_first_5k": 9.40,
        "tier_2_next_5k": 6.45,
        "tier_3_next_10k": 4.83,
        "tier_4_next_20k": 3.45,
        "tier_5_next_30k": 3.25,
        "tier_6_next_50k": 2.56,
        "tier_7_next_60k": 2.44,
        "tier_8_the_rest": 2.44,
    },
    {
        "vessel_type": "Cruise Ships",
        "condition": "Laden",
        "tier_1_first_5k": 9.97,
        "tier_2_next_5k": 7.00,
        "tier_3_next_10k": 5.77,
        "tier_4_next_20k": 4.08,
        "tier_5_next_30k": 4.03,
        "tier_6_next_50k": 3.90,
        "tier_7_next_60k": 3.76,
        "tier_8_the_rest": 3.76,
    },
    {
        "vessel_type": "Cruise Ships",
        "condition": "Ballast",
        "tier_1_first_5k": 8.48,
        "tier_2_next_5k": 5.96,
        "tier_3_next_10k": 4.91,
        "tier_4_next_20k": 3.48,
        "tier_5_next_30k": 3.42,
        "tier_6_next_50k": 3.31,
        "tier_7_next_60k": 3.19,
        "tier_8_the_rest": 3.19,
    },
    {
        "vessel_type": "Special Floating Units",
        "condition": "Laden",
        "tier_1_first_5k": 11.98,
        "tier_2_next_5k": 7.94,
        "tier_3_next_10k": 7.14,
        "tier_4_next_20k": 5.06,
        "tier_5_next_30k": 4.76,
        "tier_6_next_50k": 4.31,
        "tier_7_next_60k": 4.16,
        "tier_8_the_rest": 4.16,
    },
    {
        "vessel_type": "Special Floating Units",
        "condition": "Ballast",
        "tier_1_first_5k": 11.98,
        "tier_2_next_5k": 7.94,
        "tier_3_next_10k": 7.14,
        "tier_4_next_20k": 5.06,
        "tier_5_next_30k": 4.76,
        "tier_6_next_50k": 4.31,
        "tier_7_next_60k": 4.16,
        "tier_8_the_rest": 4.16,
    },
    {
        "vessel_type": "Other Vessels",
        "condition": "Laden",
        "tier_1_first_5k": 10.54,
        "tier_2_next_5k": 7.10,
        "tier_3_next_10k": 5.97,
        "tier_4_next_20k": 4.35,
        "tier_5_next_30k": 4.21,
        "tier_6_next_50k": 3.94,
        "tier_7_next_60k": 3.80,
        "tier_8_the_rest": 3.80,
    },
    {
        "vessel_type": "Other Vessels",
        "condition": "Ballast",
        "tier_1_first_5k": 8.96,
        "tier_2_next_5k": 6.04,
        "tier_3_next_10k": 5.08,
        "tier_4_next_20k": 3.70,
        "tier_5_next_30k": 3.59,
        "tier_6_next_50k": 3.36,
        "tier_7_next_60k": 3.22,
        "tier_8_the_rest": 3.22,
    },
]

CHOKEPOINTS_DATA = [
    {
        "chokepoint_id": 1,
        "name": "Suez Canal",
        "corridor": "Mediterranean - Red Sea Connector",
        "lat_min": 29.8000,
        "lat_max": 31.3500,
        "lon_min": 32.2000,
        "lon_max": 32.7000,
        "baseline_transit_hrs": 14.00,
        "baseline_speed_knots": 8.50,
        "base_toll_usd": 500000.00,
        "war_risk_surcharge_pct": 15.00,
        "cape_diversion_added_days": 12.00,
    },
    {
        "chokepoint_id": 2,
        "name": "Bab-el-Mandeb Strait",
        "corridor": "Southern Red Sea - Gulf of Aden",
        "lat_min": 12.2000,
        "lat_max": 13.5000,
        "lon_min": 43.0000,
        "lon_max": 44.0000,
        "baseline_transit_hrs": 6.00,
        "baseline_speed_knots": 14.00,
        "base_toll_usd": 0.00,
        "war_risk_surcharge_pct": 125.00,
        "cape_diversion_added_days": 14.00,
    },
    {
        "chokepoint_id": 3,
        "name": "Strait of Malacca",
        "corridor": "Indian Ocean - South China Sea",
        "lat_min": 1.0000,
        "lat_max": 5.5000,
        "lon_min": 95.0000,
        "lon_max": 104.5000,
        "baseline_transit_hrs": 32.00,
        "baseline_speed_knots": 15.00,
        "base_toll_usd": 0.00,
        "war_risk_surcharge_pct": 2.50,
        "cape_diversion_added_days": 0.00,
    },
    {
        "chokepoint_id": 4,
        "name": "Panama Canal",
        "corridor": "Atlantic - Pacific Gateway",
        "lat_min": 8.8000,
        "lat_max": 9.4000,
        "lon_min": -80.1000,
        "lon_max": -79.5000,
        "baseline_transit_hrs": 11.50,
        "baseline_speed_knots": 6.00,
        "base_toll_usd": 450000.00,
        "war_risk_surcharge_pct": 0.00,
        "cape_diversion_added_days": 22.00,
    },
    {
        "chokepoint_id": 5,
        "name": "Cape of Good Hope",
        "corridor": "South Atlantic - Indian Ocean Bypass",
        "lat_min": -36.5000,
        "lat_max": -33.5000,
        "lon_min": 17.5000,
        "lon_max": 21.0000,
        "baseline_transit_hrs": 24.00,
        "baseline_speed_knots": 13.50,
        "base_toll_usd": 0.00,
        "war_risk_surcharge_pct": 0.00,
        "cape_diversion_added_days": 0.00,
    },
]


def seed_suez_toll_tiers(output_csv: Path | None = None) -> Path:
    """Export the official SCA progressive toll tiers to CSV."""
    if output_csv is None:
        output_csv = Path(__file__).resolve().parents[2] / "data" / "raw" / "dim_suez_toll_tiers.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(SUEZ_TOLL_TIERS_DATA)
    df.to_csv(output_csv, index=False)
    logger.info(f"Generated dim_suez_toll_tiers.csv: {len(df)} rows at {output_csv}")
    return output_csv


def seed_chokepoints(output_csv: Path | None = None) -> Path:
    """Export strategic maritime chokepoints geofences to CSV."""
    if output_csv is None:
        output_csv = Path(__file__).resolve().parents[2] / "data" / "raw" / "dim_chokepoints.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(CHOKEPOINTS_DATA)
    df.to_csv(output_csv, index=False)
    logger.info(f"Generated dim_chokepoints.csv: {len(df)} rows at {output_csv}")
    return output_csv


def seed_all(data_dir: Path | None = None) -> dict[str, Path]:
    """Seed all static dimension tables."""
    raw_dir = (data_dir or (Path(__file__).resolve().parents[2] / "data")) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    suez_path = seed_suez_toll_tiers(raw_dir / "dim_suez_toll_tiers.csv")
    choke_path = seed_chokepoints(raw_dir / "dim_chokepoints.csv")
    return {"suez_tolls": suez_path, "chokepoints": choke_path}


if __name__ == "__main__":
    seed_all()

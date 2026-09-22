"""Master Execution Script: Phase 1 Maritime Route Risk Intelligence.

Orchestrates the entire Phase 1 pipeline:
1. Programmatic discovery of real-world downloads (AIS telemetry & World Bank CPPI).
2. Automated extraction & staging to data/raw/.
3. Ingestion & cleaning of CPPI port performance metrics.
4. Seeding of official Suez Canal Authority (SCA) progressive toll rates & chokepoints.
5. High-throughput chunked stream ingestion & coordinate validation of AIS telemetry.
6. Relational DDL schema creation and batch loading into DuckDB / PostgreSQL.
7. Verification assertions, analytical queries, and executive summary report.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
import pandas as pd

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.stage_downloads import stage_all_downloads
from src.ingestion.ingest_cppi import clean_cppi_dataset
from src.ingestion.seed_reference_data import seed_all
from src.ingestion.ingest_ais import stream_process_ais
from src.db.db_loader import DatabaseManager, load_all_data
from src.models.suez_calculator import calculate_suez_toll_breakdown, calculate_suez_toll_usd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("run_phase1")


def print_banner() -> None:
    banner = """
================================================================================
           MARITIME ROUTE RISK INTELLIGENCE - PHASE 1 PIPELINE
================================================================================
  Data Engineering Platform:
  * Source A: Real-World AIS Vessel Telemetry Stream & Coordinate Validator
  * Source B: World Bank Container Port Performance Index (CPPI 2025)
  * Source C: Official Suez Canal Authority (SCA) Progressive Toll Rate Cards
  * Database: Embedded Columnar DuckDB (OLAP) & PostgreSQL Schema (DDL)
  * Model   : Progressive Multi-Tier Transit Dues Calculator in USD
================================================================================
"""
    print(banner)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 1 Maritime Risk Intelligence Pipeline.")
    parser.add_argument(
        "--max-ais-rows",
        type=int,
        default=250_000,
        help="Maximum AIS rows to stream and validate (default: 250,000 for rapid local processing. Set 0 for unlimited).",
    )
    parser.add_argument(
        "--db-type",
        choices=["duckdb", "postgres"],
        default="duckdb",
        help="Database engine to initialize and load (default: duckdb).",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=str(PROJECT_ROOT / "data" / "maritime_risk.duckdb"),
        help="Path to DuckDB database file.",
    )
    return parser.parse_args()


def execute_pipeline(max_ais_rows: int = 250_000, db_type: str = "duckdb", db_path: str | None = None) -> None:
    start_time = time.time()
    print_banner()

    data_dir = PROJECT_ROOT / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    max_rows = None if max_ais_rows <= 0 else max_ais_rows

    # -------------------------------------------------------------------------
    # STEP 1: Programmatic Downloads Discovery & Staging
    # -------------------------------------------------------------------------
    logger.info(">>> STEP 1: Scanning ~/Downloads for real-world AIS telemetry & CPPI dataset...")
    staged = stage_all_downloads(output_dir=data_dir)
    ais_raw_path = staged["ais_raw_csv"]
    cppi_source_path = staged["cppi_source"]
    logger.info(f"Staged AIS raw CSV: {ais_raw_path} ({ais_raw_path.stat().st_size / (1024*1024):.2f} MB)")
    logger.info(f"Located CPPI source: {cppi_source_path}")

    # -------------------------------------------------------------------------
    # STEP 2: Ingest & Clean CPPI Port Performance Index
    # -------------------------------------------------------------------------
    logger.info(">>> STEP 2: Parsing World Bank CPPI 'Annex' sheet...")
    ports_clean_path = raw_dir / "dim_ports_clean.csv"
    ports_df = clean_cppi_dataset(cppi_source_path, sheet_name="Annex", output_csv=ports_clean_path)
    logger.info(f"Cleaned {len(ports_df):,} global ports into {ports_clean_path}")

    # -------------------------------------------------------------------------
    # STEP 3: Seed Reference Data (Suez Toll Cards & Chokepoints)
    # -------------------------------------------------------------------------
    logger.info(">>> STEP 3: Generating official Suez Canal toll tiers and chokepoint geofences...")
    seeded = seed_all(data_dir=data_dir)
    logger.info(f"Seeded Suez toll rates: {seeded['suez_tolls']}")
    logger.info(f"Seeded Chokepoints: {seeded['chokepoints']}")

    # -------------------------------------------------------------------------
    # STEP 4: Stream Ingest & Validate AIS Telemetry
    # -------------------------------------------------------------------------
    logger.info(f">>> STEP 4: Streaming & validating AIS telemetry (limit: {max_rows or 'ALL'} rows)...")
    pings_clean_path = processed_dir / "fact_ais_pings_clean.csv"
    vessels_clean_path = processed_dir / "dim_vessels_clean.csv"

    valid_pings, unique_vessels = stream_process_ais(
        raw_csv_path=ais_raw_path,
        output_pings_csv=pings_clean_path,
        output_vessels_csv=vessels_clean_path,
        chunk_size=100_000,
        max_total_rows=max_rows,
        tag_geofences=True,
    )
    logger.info(f"Validated {valid_pings:,} pings and extracted {unique_vessels:,} vessels.")

    # -------------------------------------------------------------------------
    # STEP 5: Initialize Database Schema and Batch Load Tables
    # -------------------------------------------------------------------------
    logger.info(f">>> STEP 5: Initializing relational DDL & batch loading {db_type.upper()}...")
    db_file_path = Path(db_path) if db_path else (data_dir / "maritime_risk.duckdb")
    db, counts = load_all_data(data_dir=data_dir, engine_type=db_type, db_path=db_file_path)

    # -------------------------------------------------------------------------
    # STEP 6: Run Analytical Verification Queries & Progressive Toll Verification
    # -------------------------------------------------------------------------
    logger.info(">>> STEP 6: Running validation assertions and analytical sanity checks...")

    # Assertions
    assert counts["dim_ports"] > 0, "dim_ports table must not be empty"
    assert counts["dim_chokepoints"] == 5, "dim_chokepoints must contain 5 corridors"
    assert counts["dim_suez_toll_rates"] >= 20, "dim_suez_toll_rates must contain all tiers"
    assert counts["fact_ais_pings"] > 0, "fact_ais_pings must contain validated observations"
    assert counts["dim_vessels"] > 0, "dim_vessels must contain extracted vessels"

    # Query 1: Top 5 Highest Performing Global Ports (CPPI 2025)
    top_ports = db.run_query("""
        SELECT port_name, country, region, cppi_rank, cppi_score, berth_efficiency_ratio
        FROM dim_ports
        WHERE cppi_rank IS NOT NULL
        ORDER BY cppi_rank ASC
        LIMIT 5;
    """)

    # Query 2: AIS Pings inside Chokepoints
    choke_summary = db.run_query("""
        SELECT c.name AS chokepoint, COUNT(p.ping_id) AS ping_count,
               AVG(p.sog_knots) AS avg_speed_knots
        FROM dim_chokepoints c
        LEFT JOIN fact_ais_pings p ON c.chokepoint_id = p.chokepoint_id
        GROUP BY c.chokepoint_id, c.name
        ORDER BY ping_count DESC;
    """)

    # Progressive Toll Calculation Test for 120,000 SCNT Laden Container Ship
    ship_type = "Container Ships"
    scnt = 120_000.0
    sdr_usd = 1.33
    toll_breakdown = calculate_suez_toll_breakdown(ship_type, scnt, is_laden=True, sdr_to_usd=sdr_usd)
    toll_usd = toll_breakdown["total_usd"]
    expected_toll_usd = 664601.0
    assert toll_usd == expected_toll_usd, f"Expected {expected_toll_usd}, got {toll_usd}"

    elapsed = time.time() - start_time

    # -------------------------------------------------------------------------
    # EXECUTIVE SUMMARY REPORT
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("                    PHASE 1 PIPELINE EXECUTION REPORT")
    print("=" * 80)
    print(f"Elapsed Time: {elapsed:.2f} seconds")
    print(f"Database Target: {db_type.upper()} ({db_file_path if db_type == 'duckdb' else 'PostgreSQL'})")
    print("-" * 80)
    print("TABLE ROW COUNTS:")
    for tbl, count in counts.items():
        print(f"  * {tbl:<25}: {count:>10,d} rows")
    print("-" * 80)
    print("SAMPLE ANALYTICS - TOP 5 GLOBAL PORTS (CPPI 2025):")
    print(top_ports.to_string(index=False))
    print("-" * 80)
    print("STRATEGIC CHOKEPOINT AIS OBSERVATIONS:")
    print(choke_summary.to_string(index=False))
    print("-" * 80)
    print("PROGRESSIVE SUEZ TOLL VERIFICATION (120,000 SCNT Laden Container Ship):")
    for t in toll_breakdown["tier_breakdown"]:
        print(f"  - {t['label']:<28}: {t['tonnage']:>8,.0f} SCNT @ {t['rate_sdr']:>5.2f} SDR = {t['cost_sdr']:>10,.2f} SDR")
    print(f"  Total Transit Dues (SDR): {toll_breakdown['total_sdr']:,.2f} SDR")
    print(f"  Total Transit Dues (USD): ${toll_usd:,.2f} USD (verified against official SCA tariff)")
    print("=" * 80)
    print(">>> PHASE 1 EXECUTION COMPLETE: ALL DELIVERABLES AND ASSERTIONS PASSED <<<\n")

    db.close()


if __name__ == "__main__":
    args = parse_args()
    execute_pipeline(
        max_ais_rows=args.max_ais_rows,
        db_type=args.db_type,
        db_path=args.db_path,
    )

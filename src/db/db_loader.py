"""Database Loader Module.

High-performance batch loader supporting both DuckDB (embedded local OLAP engine)
and PostgreSQL (via SQLAlchemy / psycopg2).
Executes relational DDL, populates dimension tables and fact tables, and creates indexes.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any
import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("db_loader")


class DatabaseManager:
    """Manages database connections, schema execution, and data loading."""

    def __init__(
        self,
        engine_type: str = "duckdb",
        db_path: Path | str | None = None,
        database_url: str | None = None,
    ):
        self.engine_type = engine_type.lower()
        self.db_path = db_path or (Path(__file__).resolve().parents[2] / "data" / "maritime_risk.duckdb")
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self._duck_conn: duckdb.DuckDBPyConnection | None = None
        self._pg_engine = None

        if self.engine_type == "duckdb":
            if isinstance(self.db_path, (str, Path)) and str(self.db_path) != ":memory:":
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._duck_conn = duckdb.connect(str(self.db_path))
            logger.info(f"Initialized DuckDB connection at: {self.db_path}")
        elif self.engine_type == "postgres":
            if not self.database_url:
                raise ValueError("DATABASE_URL must be provided for postgres engine_type.")
            from sqlalchemy import create_engine
            self._pg_engine = create_engine(self.database_url)
            logger.info("Initialized PostgreSQL connection via SQLAlchemy.")
        else:
            raise ValueError(f"Unsupported engine type: {engine_type}")

    def execute_sql(self, sql: str) -> None:
        """Execute raw SQL statements."""
        if self.engine_type == "duckdb" and self._duck_conn:
            self._duck_conn.execute(sql)
        elif self.engine_type == "postgres" and self._pg_engine:
            from sqlalchemy import text
            with self._pg_engine.begin() as conn:
                conn.execute(text(sql))

    def execute_sql_file(self, sql_file_path: Path) -> None:
        """Read and execute a .sql file."""
        if not sql_file_path.exists():
            raise FileNotFoundError(f"SQL file not found at: {sql_file_path}")

        logger.info(f"Executing SQL script: {sql_file_path.name}")
        sql_content = sql_file_path.read_text(encoding="utf-8")

        # DuckDB handles multiple semicolons or statement blocks
        if self.engine_type == "duckdb" and self._duck_conn:
            # DuckDB supports execute for script
            self._duck_conn.execute(sql_content)
        elif self.engine_type == "postgres" and self._pg_engine:
            from sqlalchemy import text
            with self._pg_engine.begin() as conn:
                conn.execute(text(sql_content))

    def init_schema(self, ddl_path: Path | None = None) -> None:
        """Initialize the relational schema from 01_schema.sql."""
        if ddl_path is None:
            ddl_path = Path(__file__).resolve().parents[2] / "sql" / "01_schema.sql"
        self.execute_sql_file(ddl_path)
        logger.info("Schema initialized successfully.")

    def load_dataframe(self, table_name: str, df: pd.DataFrame, if_exists: str = "append") -> int:
        """Load a pandas DataFrame into the designated table."""
        if df.empty:
            logger.warning(f"Skipping load for table '{table_name}': DataFrame is empty.")
            return 0

        logger.info(f"Loading {len(df):,} rows into '{table_name}'...")
        if self.engine_type == "duckdb" and self._duck_conn:
            # Register temp view and insert
            self._duck_conn.register("tmp_stage_view", df)
            if if_exists == "replace":
                self._duck_conn.execute(f"DELETE FROM {table_name}")
            cols = ", ".join(df.columns)
            self._duck_conn.execute(f"INSERT OR REPLACE INTO {table_name} ({cols}) SELECT {cols} FROM tmp_stage_view")
            self._duck_conn.unregister("tmp_stage_view")
        elif self.engine_type == "postgres" and self._pg_engine:
            df.to_sql(table_name, con=self._pg_engine, if_exists=if_exists, index=False, method="multi", chunksize=10000)

        logger.info(f"Successfully loaded {len(df):,} rows into '{table_name}'.")
        return len(df)

    def load_csv(self, table_name: str, csv_path: Path, if_exists: str = "append") -> int:
        """Load a CSV file into the designated table."""
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        if self.engine_type == "duckdb" and self._duck_conn:
            logger.info(f"Fast loading '{csv_path.name}' into DuckDB table '{table_name}'...")
            posix_path = str(csv_path).replace("\\", "/")
            if if_exists == "replace":
                self._duck_conn.execute(f"DELETE FROM {table_name}")
            query = f"""
                INSERT OR REPLACE INTO {table_name}
                SELECT * FROM read_csv('{posix_path}', header=True, auto_detect=True);
            """
            self._duck_conn.execute(query)
            count = self._duck_conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            logger.info(f"Table '{table_name}' now contains {count:,} rows.")
            return count
        else:
            df = pd.read_csv(csv_path)
            return self.load_dataframe(table_name, df, if_exists=if_exists)

    def get_table_counts(self) -> dict[str, int]:
        """Query and return the row counts of all core database tables."""
        tables = ["dim_vessels", "dim_ports", "dim_chokepoints", "dim_suez_toll_rates", "fact_ais_pings"]
        counts: dict[str, int] = {}

        for tbl in tables:
            try:
                if self.engine_type == "duckdb" and self._duck_conn:
                    cnt = self._duck_conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                elif self.engine_type == "postgres" and self._pg_engine:
                    from sqlalchemy import text
                    with self._pg_engine.connect() as conn:
                        cnt = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
                else:
                    cnt = 0
                counts[tbl] = cnt
            except Exception as e:
                logger.debug(f"Error querying table {tbl}: {e}")
                counts[tbl] = 0

        return counts

    def run_query(self, sql: str) -> pd.DataFrame:
        """Run arbitrary SQL and return a pandas DataFrame."""
        if self.engine_type == "duckdb" and self._duck_conn:
            return self._duck_conn.execute(sql).df()
        elif self.engine_type == "postgres" and self._pg_engine:
            return pd.read_sql_query(sql, con=self._pg_engine)
        return pd.DataFrame()

    def close(self) -> None:
        """Close connections."""
        if self._duck_conn:
            self._duck_conn.close()
            self._duck_conn = None


def load_all_data(
    data_dir: Path | None = None,
    engine_type: str = "duckdb",
    db_path: Path | None = None,
) -> tuple[DatabaseManager, dict[str, int]]:
    """Execute complete schema creation and data loading."""
    project_root = Path(__file__).resolve().parents[2]
    data_root = data_dir or (project_root / "data")
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"

    db = DatabaseManager(engine_type=engine_type, db_path=db_path)
    db.init_schema(project_root / "sql" / "01_schema.sql")

    # 1. Load Suez toll rates
    suez_csv = raw_dir / "dim_suez_toll_tiers.csv"
    if suez_csv.exists():
        db.load_csv("dim_suez_toll_rates", suez_csv, if_exists="replace")
    else:
        db.execute_sql_file(project_root / "sql" / "02_seed_suez_tolls.sql")

    # 2. Load Chokepoints
    choke_csv = raw_dir / "dim_chokepoints.csv"
    if choke_csv.exists():
        db.load_csv("dim_chokepoints", choke_csv, if_exists="replace")
    else:
        db.execute_sql_file(project_root / "sql" / "03_seed_chokepoints.sql")

    # 3. Load Ports
    ports_csv = raw_dir / "dim_ports_clean.csv"
    if ports_csv.exists():
        db.load_csv("dim_ports", ports_csv, if_exists="replace")

    # 4. Load Vessels
    vessels_csv = processed_dir / "dim_vessels_clean.csv"
    if vessels_csv.exists():
        db.load_csv("dim_vessels", vessels_csv, if_exists="replace")

    # 5. Load AIS pings
    pings_csv = processed_dir / "fact_ais_pings_clean.csv"
    if pings_csv.exists():
        db.load_csv("fact_ais_pings", pings_csv, if_exists="replace")

    counts = db.get_table_counts()
    logger.info("Pipeline Data Load Summary:")
    for tbl, count in counts.items():
        logger.info(f"  - {tbl}: {count:,} rows")

    return db, counts


if __name__ == "__main__":
    load_all_data()

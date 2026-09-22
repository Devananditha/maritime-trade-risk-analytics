"""Downloads Staging Module.

Programmatically scans the local Downloads directory (Path.home() / "Downloads")
for:
1. AIS Vessel Telemetry archives/files (AIS*.zip, ais*.zip, ais*.tgz, .csv.zst, or directory).
   Extracts and stages into data/raw/ais_telemetry_raw.csv.
2. World Bank Container Port Performance Index (CPPI) Excel files (*CPPI*.xlsx, P509479*.xlsx).
   Stages or locates for ingestion into dim_ports_clean.csv.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
import zipfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("stage_downloads")


def get_downloads_dir() -> Path:
    """Return the user's Downloads directory path."""
    downloads = Path.home() / "Downloads"
    if not downloads.exists():
        raise FileNotFoundError(f"Downloads directory not found at: {downloads}")
    return downloads


def find_latest_ais_source(downloads_dir: Path | None = None) -> Path:
    """Scan Downloads for the newest AIS telemetry file or archive.
    
    Checks for .zip, .tgz, .tar.gz, .csv.zst, .csv, or extracted AIS directories.
    """
    downloads = downloads_dir or get_downloads_dir()
    patterns = [
        "AIS*.zip", "ais*.zip",
        "AIS*.tgz", "ais*.tgz",
        "AIS*.tar.gz", "ais*.tar.gz",
        "AIS*.csv.zst", "ais*.csv.zst",
        "AIS*.csv", "ais*.csv",
        "ais-*-*", "AIS-*-*",
    ]

    candidates: list[Path] = []
    for pattern in patterns:
        for p in downloads.glob(pattern):
            candidates.append(p)

    if not candidates:
        raise FileNotFoundError(f"No AIS telemetry sources matching patterns {patterns} found in {downloads}")

    # Prioritize extracted folder or latest modified file
    # Sort by modification time descending
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest = candidates[0]
    logger.info(f"Discovered newest AIS source: {latest} ({latest.stat().st_size / (1024*1024):.2f} MB)")
    return latest


def find_latest_cppi_source(downloads_dir: Path | None = None) -> Path:
    """Scan Downloads for the World Bank CPPI dataset."""
    downloads = downloads_dir or get_downloads_dir()
    patterns = [
        "P509479*.xlsx",
        "*CPPI*.xlsx",
        "*cppi*.xlsx",
        "*CPPI*.csv",
        "*cppi*.csv",
    ]

    candidates: list[Path] = []
    for pattern in patterns:
        for p in downloads.glob(pattern):
            candidates.append(p)

    if not candidates:
        raise FileNotFoundError(f"No CPPI sources matching patterns {patterns} found in {downloads}")

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest = candidates[0]
    logger.info(f"Discovered CPPI source: {latest} ({latest.stat().st_size / 1024:.2f} KB)")
    return latest


def stage_ais_to_raw(
    ais_source: Path,
    output_raw_csv: Path | None = None,
    max_staging_rows: int | None = None,
) -> Path:
    """Safely extract/copy the AIS dataset into data/raw/ais_telemetry_raw.csv."""
    if output_raw_csv is None:
        output_raw_csv = Path(__file__).resolve().parents[2] / "data" / "raw" / "ais_telemetry_raw.csv"
    output_raw_csv.parent.mkdir(parents=True, exist_ok=True)

    target_csv: Path | None = None
    temp_dir: str | None = None

    try:
        if ais_source.is_dir():
            # Directory: find internal CSV or data file
            files = [f for f in ais_source.iterdir() if f.is_file()]
            # Look for file matching ais or .csv
            csv_candidates = [f for f in files if f.suffix.lower() == ".csv" or "ais" in f.name.lower()]
            if csv_candidates:
                target_csv = csv_candidates[0]
            elif files:
                target_csv = files[0]
            else:
                raise FileNotFoundError(f"Directory {ais_source} contains no files.")

        elif ais_source.suffix.lower() == ".zip":
            temp_dir = tempfile.mkdtemp(prefix="ais_zip_stage_")
            logger.info(f"Extracting ZIP archive {ais_source.name} to {temp_dir}...")
            with zipfile.ZipFile(ais_source, "r") as zf:
                zf.extractall(temp_dir)
            extracted_files = [Path(temp_dir) / f for f in os.listdir(temp_dir)]
            csv_candidates = [f for f in extracted_files if f.suffix.lower() == ".csv" or f.is_file()]
            if not csv_candidates:
                raise FileNotFoundError(f"No files extracted from {ais_source}")
            target_csv = csv_candidates[0]

        elif ais_source.suffix.lower() in [".tgz", ".gz"] or ais_source.name.endswith(".tar.gz"):
            temp_dir = tempfile.mkdtemp(prefix="ais_tar_stage_")
            logger.info(f"Extracting TAR archive {ais_source.name} to {temp_dir}...")
            with tarfile.open(ais_source, "r:*") as tar:
                tar.extractall(temp_dir)
            extracted_files = list(Path(temp_dir).rglob("*"))
            files = [f for f in extracted_files if f.is_file()]
            csv_candidates = [f for f in files if f.suffix.lower() == ".csv" or "ais" in f.name.lower()]
            target_csv = csv_candidates[0] if csv_candidates else (files[0] if files else None)
            if not target_csv:
                raise FileNotFoundError(f"No files extracted from {ais_source}")

        elif ais_source.suffix.lower() == ".csv" or ais_source.is_file():
            target_csv = ais_source

        else:
            raise ValueError(f"Unsupported AIS source format: {ais_source}")

        logger.info(f"Staging AIS source file: {target_csv} -> {output_raw_csv}")

        # Stream copy to avoid duplicating massive memory
        # If max_staging_rows is specified, sample; otherwise stream full file
        if max_staging_rows is not None and max_staging_rows > 0:
            logger.info(f"Downsampling staging to first {max_staging_rows:,} rows...")
            with open(target_csv, "r", encoding="utf-8", errors="ignore") as fin, \
                 open(output_raw_csv, "w", encoding="utf-8", newline="") as fout:
                header = fin.readline()
                fout.write(header)
                count = 0
                for line in fin:
                    fout.write(line)
                    count += 1
                    if count >= max_staging_rows:
                        break
            logger.info(f"Staged {count:,} rows into {output_raw_csv}")
        else:
            shutil.copyfile(target_csv, output_raw_csv)
            file_mb = output_raw_csv.stat().st_size / (1024 * 1024)
            logger.info(f"Successfully staged full AIS raw dataset: {file_mb:.2f} MB at {output_raw_csv}")

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

    return output_raw_csv


def stage_all_downloads(
    downloads_dir: Path | None = None,
    output_dir: Path | None = None,
    max_staging_rows: int | None = None,
) -> dict[str, Path]:
    """Execute end-to-end downloads discovery and staging."""
    downloads = downloads_dir or get_downloads_dir()
    raw_dir = (output_dir or (Path(__file__).resolve().parents[2] / "data")) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Scanning downloads directory: {downloads}")

    ais_source = find_latest_ais_source(downloads)
    ais_raw_csv = stage_ais_to_raw(ais_source, raw_dir / "ais_telemetry_raw.csv", max_staging_rows=max_staging_rows)

    cppi_source = find_latest_cppi_source(downloads)

    return {
        "ais_raw_csv": ais_raw_csv,
        "cppi_source": cppi_source,
    }


if __name__ == "__main__":
    stage_all_downloads()

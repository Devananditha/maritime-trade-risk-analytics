"""Master Pipeline Execution Driver (Alias for run_phase1.py)."""

from run_phase1 import execute_pipeline, parse_args

if __name__ == "__main__":
    args = parse_args()
    execute_pipeline(
        max_ais_rows=args.max_ais_rows,
        db_type=args.db_type,
        db_path=args.db_path,
    )

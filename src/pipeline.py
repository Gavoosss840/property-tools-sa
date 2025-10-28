"""
src/pipeline.py

End-to-end pipeline for the Streamlit app (CSV/Excel only):
1) Load addresses from Excel/CSV (normalized columns)
2) Geocode addresses (OSM first, then Google if available)
3) Split into San Antonio zones and write per-zone CSVs
4) Return summary statistics for display
"""

from pathlib import Path
from typing import Dict

import pandas as pd

from .geocode_hybrid import geocode_hybrid_batch
from .area_filters import (
    filter_by_polygon,
    NORTH_SA_RECT,
    SOUTH_SA_RECT,
    EAST_SA_RECT,
    WEST_SA_RECT,
)
from .io_utils import load_csv as load_csv_normalized
from .io_utils import load_excel as load_excel_normalized


def _run_pipeline(df: pd.DataFrame) -> Dict[str, int]:
    """Shared core: geocode, split into zones, write outputs, return stats."""
    outputs_dir = Path("data/outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)

    if df.empty:
        return {
            "total_addresses": 0,
            "geocoded": 0,
            "unassigned": 0,
            "north": 0,
            "south": 0,
            "east": 0,
            "west": 0,
        }

    # Geocode
    df_geo = geocode_hybrid_batch(df)

    # Save all geocoded addresses
    all_path = outputs_dir / "all_addresses_geocoded.csv"
    df_geo.to_csv(all_path, index=False)

    # Zones (valid lat/lon only)
    df_geo_valid = df_geo.dropna(subset=["lat", "lon"]).copy()

    north_df = filter_by_polygon(df_geo_valid, NORTH_SA_RECT)
    south_df = filter_by_polygon(df_geo_valid, SOUTH_SA_RECT)
    east_df = filter_by_polygon(df_geo_valid, EAST_SA_RECT)
    west_df = filter_by_polygon(df_geo_valid, WEST_SA_RECT)

    # Save per-zone CSVs (create empty files if no rows)
    (outputs_dir / "north_san_antonio.csv").write_text("") if len(north_df) == 0 else north_df.to_csv(outputs_dir / "north_san_antonio.csv", index=False)
    (outputs_dir / "south_san_antonio.csv").write_text("") if len(south_df) == 0 else south_df.to_csv(outputs_dir / "south_san_antonio.csv", index=False)
    (outputs_dir / "east_san_antonio.csv").write_text("") if len(east_df) == 0 else east_df.to_csv(outputs_dir / "east_san_antonio.csv", index=False)
    (outputs_dir / "west_san_antonio.csv").write_text("") if len(west_df) == 0 else west_df.to_csv(outputs_dir / "west_san_antonio.csv", index=False)

    # Stats
    total = len(df_geo)
    geocoded = df_geo_valid.shape[0]
    assigned = sum(len(x) for x in (north_df, south_df, east_df, west_df))
    unassigned = max(0, geocoded - assigned)

    return {
        "total_addresses": int(total),
        "geocoded": int(geocoded),
        "unassigned": int(unassigned),
        "north": int(len(north_df)),
        "south": int(len(south_df)),
        "east": int(len(east_df)),
        "west": int(len(west_df)),
    }


def run_csv_pipeline(csv_path: str) -> Dict[str, int]:
    """Pipeline starting from a user-provided CSV file."""
    df = load_csv_normalized(csv_path)
    return _run_pipeline(df)


def run_excel_pipeline(xlsx_path: str) -> Dict[str, int]:
    """Pipeline starting from a user-provided Excel (.xlsx) file."""
    df = load_excel_normalized(xlsx_path)
    return _run_pipeline(df)

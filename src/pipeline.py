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
from .area_filters import assign_san_antonio_zones, ZONE_KEYS
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
    df_geo_with_zone = df_geo.copy()
    df_geo_with_zone["zone"] = None

    # Zones (valid lat/lon only)
    df_geo_valid = df_geo.dropna(subset=["lat", "lon"]).copy()

    df_zoned = assign_san_antonio_zones(df_geo_valid)
    zone_dfs = {
        zone: df_zoned[df_zoned["zone"] == zone].drop(columns=["zone"])
        for zone in ZONE_KEYS
    }
    unassigned_df = df_zoned[df_zoned["zone"].isna()].drop(columns=["zone"])

    # Update overall export with zone info
    df_geo_with_zone.loc[df_zoned.index, "zone"] = df_zoned["zone"]
    df_geo_with_zone.to_csv(all_path, index=False)

    # Save per-zone CSVs (create empty files if no rows)
    for zone in ZONE_KEYS:
        path = outputs_dir / f"{zone}_san_antonio.csv"
        zone_df = zone_dfs[zone]
        if zone_df.empty:
            path.write_text("")
        else:
            zone_df.to_csv(path, index=False)

    # Stats
    total = len(df_geo)
    geocoded = df_geo_valid.shape[0]
    assigned = sum(len(zone_dfs[zone]) for zone in ZONE_KEYS)
    unassigned = len(unassigned_df)

    return {
        "total_addresses": int(total),
        "geocoded": int(geocoded),
        "unassigned": int(unassigned),
        "north": int(len(zone_dfs["north"])),
        "south": int(len(zone_dfs["south"])),
        "east": int(len(zone_dfs["east"])),
        "west": int(len(zone_dfs["west"])),
    }


def run_csv_pipeline(csv_path: str) -> Dict[str, int]:
    """Pipeline starting from a user-provided CSV file."""
    df = load_csv_normalized(csv_path)
    return _run_pipeline(df)


def run_excel_pipeline(xlsx_path: str) -> Dict[str, int]:
    """Pipeline starting from a user-provided Excel (.xlsx) file."""
    df = load_excel_normalized(xlsx_path)
    return _run_pipeline(df)


__all__ = [
    "run_csv_pipeline",
    "run_excel_pipeline",
]

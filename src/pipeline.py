"""
src/pipeline.py

Assemble the end-to-end pipeline used by the Streamlit app:
1) Extract addresses from a foreclosure-style PDF into CSV
2) Geocode addresses (OSM first, then Google if available)
3) Split into San Antonio zones and write per-zone CSVs
4) Return summary statistics for display
"""

from pathlib import Path
from typing import Dict

import pandas as pd

from .pdf_extractor import process_pdf_to_csv
from .geocode_hybrid import geocode_hybrid_batch
from .area_filters import (
    filter_by_polygon,
    NORTH_SA_RECT,
    SOUTH_SA_RECT,
    EAST_SA_RECT,
    WEST_SA_RECT,
)
from .io_utils import load_csv as load_csv_normalized


def run_full_pipeline(pdf_path: str) -> Dict[str, int]:
    """Run the full pipeline and return stats for the UI.

    Args:
        pdf_path: Path to the input PDF containing addresses.

    Returns:
        Dict with keys: total_addresses, geocoded, unassigned, north, south, east, west
    """
    input_csv = Path("data/input.csv")
    outputs_dir = Path("data/outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # 1) PDF -> CSV of addresses
    extracted_count = process_pdf_to_csv(pdf_path, str(input_csv))
    if extracted_count == 0:
        # Nothing to do
        return {
            "total_addresses": 0,
            "geocoded": 0,
            "unassigned": 0,
            "north": 0,
            "south": 0,
            "east": 0,
            "west": 0,
        }

    # 2) Load and geocode
    df = pd.read_csv(input_csv)
    df_geo = geocode_hybrid_batch(df)

    # Save all geocoded addresses for debugging/download
    all_path = outputs_dir / "all_addresses_geocoded.csv"
    df_geo.to_csv(all_path, index=False)

    # 3) Filter into zones
    df_geo_valid = df_geo.dropna(subset=["lat", "lon"]).copy()

    north_df = filter_by_polygon(df_geo_valid, NORTH_SA_RECT)
    south_df = filter_by_polygon(df_geo_valid, SOUTH_SA_RECT)
    east_df = filter_by_polygon(df_geo_valid, EAST_SA_RECT)
    west_df = filter_by_polygon(df_geo_valid, WEST_SA_RECT)

    # 4) Save per-zone CSVs
    (outputs_dir / "north_san_antonio.csv").write_text("") if len(north_df) == 0 else north_df.to_csv(outputs_dir / "north_san_antonio.csv", index=False)
    (outputs_dir / "south_san_antonio.csv").write_text("") if len(south_df) == 0 else south_df.to_csv(outputs_dir / "south_san_antonio.csv", index=False)
    (outputs_dir / "east_san_antonio.csv").write_text("") if len(east_df) == 0 else east_df.to_csv(outputs_dir / "east_san_antonio.csv", index=False)
    (outputs_dir / "west_san_antonio.csv").write_text("") if len(west_df) == 0 else west_df.to_csv(outputs_dir / "west_san_antonio.csv", index=False)

    # 5) Compute stats
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
    """Pipeline that starts from a user-provided CSV.

    - Loads and normalizes columns (address, city, state, zip)
    - Geocodes with hybrid method
    - Splits into zones and writes outputs
    - Returns stats like the PDF pipeline
    """
    outputs_dir = Path("data/outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Load CSV with column normalization
    df = load_csv_normalized(csv_path)
    # Harmonize common typo 'adress' -> 'address'
    if "address" not in df.columns and "adress" in df.columns:
        df = df.rename(columns={"adress": "address"})

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

    # Zones
    df_geo_valid = df_geo.dropna(subset=["lat", "lon"]).copy()

    north_df = filter_by_polygon(df_geo_valid, NORTH_SA_RECT)
    south_df = filter_by_polygon(df_geo_valid, SOUTH_SA_RECT)
    east_df = filter_by_polygon(df_geo_valid, EAST_SA_RECT)
    west_df = filter_by_polygon(df_geo_valid, WEST_SA_RECT)

    # Save per-zone CSVs
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

# ------------------------------
# src/property_enrichment.py
# Adds optional property details (neighborhood, type, etc.) to geocoded rows.
# ------------------------------

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

REFERENCE_PATH = Path("data/property_reference.csv")
EXTRA_COLUMNS: List[str] = [
    "neighborhood",
    "property_type",
    "property_sqft",
    "appraised_value",
]


def _normalize_addr(value: str | None) -> str:
    """Simple address normalizer for matching."""
    if not isinstance(value, str):
        return ""
    return " ".join(value.upper().strip().split())


def _load_reference() -> pd.DataFrame | None:
    """Load optional reference dataset if available."""
    if not REFERENCE_PATH.exists():
        return None
    try:
        df_ref = pd.read_csv(REFERENCE_PATH)
    except Exception:
        return None

    if "address" not in df_ref.columns:
        return None

    df_ref = df_ref.copy()
    df_ref["__norm_address__"] = df_ref["address"].map(_normalize_addr)
    return df_ref


def enrich_properties(df: pd.DataFrame) -> pd.DataFrame:
    """Return dataframe with additional property metadata columns.

    If `data/property_reference.csv` exists with columns:
      address, neighborhood, property_type, property_sqft, appraised_value
    the values are merged based on the normalized address. Otherwise the
    columns are created empty so downstream exports are consistent.
    """
    df_out = df.copy()

    for col in EXTRA_COLUMNS:
        if col not in df_out.columns:
            df_out[col] = None

    reference = _load_reference()
    if reference is None:
        return df_out

    df_out["__norm_address__"] = df_out.get("address", "").map(_normalize_addr)
    try:
        merged = df_out.merge(
            reference[
                ["__norm_address__"]
                + [col for col in EXTRA_COLUMNS if col in reference.columns]
            ],
            on="__norm_address__",
            how="left",
            suffixes=("", "_ref"),
        )
    except Exception:
        df_out.drop(columns="__norm_address__", inplace=True)
        return df_out

    for col in EXTRA_COLUMNS:
        ref_col = f"{col}_ref"
        if ref_col in merged.columns:
            merged[col] = merged[col].combine_first(merged[ref_col])
            merged.drop(columns=ref_col, inplace=True)
    merged.drop(columns="__norm_address__", inplace=True, errors="ignore")
    return merged


__all__ = ["enrich_properties", "EXTRA_COLUMNS", "REFERENCE_PATH"]

"""
src/pdf_extractor.py

Deprecated compatibility shim. The new app version removes the PDF flow.
This module exists only to satisfy legacy imports like `import src.pdf_extractor`.

If called, functions will raise a clear error with next steps.
"""

from typing import Any
import pandas as pd


def extract_addresses_from_pdf(pdf_path: str, *args: Any, **kwargs: Any) -> pd.DataFrame:
    """Legacy stub kept for backward compatibility.

    Raises:
        RuntimeError: Always, since PDF extraction is no longer supported.
    """
    raise RuntimeError(
        "PDF import is no longer supported. Convert your PDF to CSV/Excel and use the app upload, or call run_csv_pipeline/run_excel_pipeline instead."
    )


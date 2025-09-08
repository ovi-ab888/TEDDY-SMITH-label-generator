from __future__ import annotations
import pandas as pd
from pathlib import Path

SUPPORTED_EXT = {".csv", ".tsv", ".xlsx", ".xls"}

def read_table(path_or_bytes, filename: str | None = None) -> pd.DataFrame:
    """
    Read CSV/TSV/XLSX/XLS to DataFrame.
    - path_or_bytes: str/Path or BytesIO-like
    - filename: required when using uploaded file buffer (to detect extension)
    """
    if isinstance(path_or_bytes, (str, Path)):
        p = Path(path_or_bytes)
        ext = p.suffix.lower()
        if ext not in SUPPORTED_EXT:
            raise ValueError(f"Unsupported file type: {ext}")
        if ext == ".csv":
            return pd.read_csv(p)
        if ext == ".tsv":
            return pd.read_csv(p, sep="\t")
        if ext in (".xlsx", ".xls"):
            return pd.read_excel(p)
    else:
        if not filename:
            raise ValueError("filename is required for uploaded buffers")
        ext = Path(filename).suffix.lower()
        if ext == ".csv":
            return pd.read_csv(path_or_bytes)
        if ext == ".tsv":
            return pd.read_csv(path_or_bytes, sep="\t")
        if ext in (".xlsx", ".xls"):
            return pd.read_excel(path_or_bytes)
        raise ValueError(f"Unsupported file type: {ext}")

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Lower + strip + spaces to underscores, but keep original in a mapping if needed.
    """
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    return df

DEFAULT_COLUMN_GUESSES = [
    ("STYLE_NAME", ["style", "style_name", "product", "style name"]),
    ("COLOR_NAME_REF", ["color", "colour", "color_name", "color ref", "color_name_ref"]),
    ("ART_SEASON_STYLE_REF", ["season", "art", "art_season_style_ref", "season_ref", "style_ref"]),
    ("SIZE_VALUE", ["size", "taille", "taille_m", "size_value"]),
    ("PRICE_VALUE", ["price", "msrp", "prix"]),
    ("BARCODE", ["ean", "barcode", "code", "ean13"]),
]

def auto_map_columns(df: pd.DataFrame) -> dict[str, str | None]:
    """
    Try to guess column mapping {SVG_ID: df_column}.
    """
    col_lower = {c.lower(): c for c in df.columns}
    mapping: dict[str, str | None] = {}
    for target, candidates in DEFAULT_COLUMN_GUESSES:
        found = None
        for cand in candidates:
            if cand in col_lower:
                found = col_lower[cand]
                break
        mapping[target] = found
    return mapping


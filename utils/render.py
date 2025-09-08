from __future__ import annotations
import cairosvg
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

def svg_to_png(svg_text: str, out_path: str, dpi: int = 300):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=out_path, dpi=dpi)

def svg_to_pdf(svg_text: str, out_path: str, dpi: int = 300):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2pdf(bytestring=svg_text.encode("utf-8"), write_to=out_path, dpi=dpi)

def make_zip(file_paths: list[str], zip_path: str) -> str:
    Path(zip_path).parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        for fp in file_paths:
            fp = str(fp)
            zf.write(fp, arcname=Path(fp).name)
    return zip_path


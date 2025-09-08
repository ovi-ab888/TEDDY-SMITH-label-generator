# app.py
import io
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# Barcode
from barcode import EAN13
from barcode.writer import ImageWriter

# -------------- Helpers --------------

REQUIRED_FIELDS = ["styleName", "colorRef", "artSeason", "styleRef", "size", "price", "barcode"]

def ean13_is_valid(code: str) -> bool:
    s = "".join([c for c in str(code) if c.isdigit()])
    if len(s) == 12:
        # python-barcode will add checksum; treat as valid input
        return True
    if len(s) != 13:
        return False
    digits = [int(c) for c in s]
    check = digits[-1]
    body = digits[:-1]
    # EAN-13 checksum
    odd_sum = sum(body[::2])
    even_sum = sum(body[1::2]) * 3
    checksum = (10 - ((odd_sum + even_sum) % 10)) % 10
    return checksum == check

def to_code12(code: str) -> Optional[str]:
    """Return 12-digit code for EAN13 generator (drops checksum if present)."""
    s = "".join([c for c in str(code) if c.isdigit()])
    if len(s) == 13 and ean13_is_valid(s):
        return s[:-1]
    if len(s) == 12:
        return s
    return None

def make_barcode_image(code: str, dpi: int = 300, text: bool = True) -> Image.Image:
    code12 = to_code12(code)
    if not code12:
        raise ValueError("Invalid EAN-13 code")
    ean = EAN13(code12, writer=ImageWriter())
    buf = io.BytesIO()
    # Stretch a bit for print clarity
    options = {
        "module_width": 0.2,  # bar width in mm equivalent
        "module_height": 25.0,
        "font_size": 12,
        "text_distance": 1.0,
        "quiet_zone": 6.5,
        "write_text": text,
        "dpi": dpi,
    }
    ean.write(buf, options)
    buf.seek(0)
    return Image.open(buf).convert("RGB")

def mm_to_px(mm: float, dpi: int) -> int:
    return int(round(mm * dpi / 25.4))

@dataclass
class LabelSpec:
    width_mm: float = 80.0
    height_mm: float = 50.0
    margin_mm: float = 4.0
    gutter_mm: float = 4.0
    cols: int = 2
    rows: int = 5
    # A4 page
    page_w_mm: float = 210.0
    page_h_mm: float = 297.0
    dpi: int = 300

    @property
    def label_w_px(self) -> int:
        return mm_to_px(self.width_mm, self.dpi)

    @property
    def label_h_px(self) -> int:
        return mm_to_px(self.height_mm, self.dpi)

    @property
    def page_w_px(self) -> int:
        return mm_to_px(self.page_w_mm, self.dpi)

    @property
    def page_h_px(self) -> int:
        return mm_to_px(self.page_h_mm, self.dpi)

    @property
    def margin_px(self) -> int:
        return mm_to_px(self.margin_mm, self.dpi)

    @property
    def gutter_px(self) -> int:
        return mm_to_px(self.gutter_mm, self.dpi)

def render_single_label(item: Dict[str, Any], spec: LabelSpec) -> Image.Image:
    W, H = spec.label_w_px, spec.label_h_px
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    # Fonts
    try:
        # If available on system; otherwise fall back
        font_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 16)
    except Exception:
        font_bold = ImageFont.load_default()
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Top text
    top_y = 10
    d.text((16, top_y), item.get("styleName", ""), font=font_bold, fill="black")
    top_y += 32
    d.text((16, top_y), f'{item.get("colorRef", "")}  |  {item.get("size", "")}', font=font, fill="black")
    top_y += 26
    d.text((16, top_y), f'{item.get("artSeason", "")}  •  {item.get("styleRef", "")}', font=font_small, fill="black")

    # Price (right-top)
    price = str(item.get("price", "")).strip()
    pw, ph = d.textbbox((0,0), price, font=font_bold)[2:]
    d.text((W - pw - 16, 10), price, font=font_bold, fill="black")

    # Barcode
    bc_img = make_barcode_image(str(item.get("barcode", "")), dpi=spec.dpi, text=True)
    # Fit barcode to label width
    target_w = int(W * 0.88)
    scale = target_w / bc_img.width
    new_size = (target_w, int(bc_img.height * scale))
    bc_resized = bc_img.resize(new_size)
    # Place barcode near bottom
    y_bar_top = H - bc_resized.height - 12
    x_bar = (W - bc_resized.width) // 2
    img.paste(bc_resized, (x_bar, y_bar_top))

    return img

def compose_pages(items: List[Dict[str, Any]], spec: LabelSpec) -> List[Image.Image]:
    pages = []
    page = Image.new("RGB", (spec.page_w_px, spec.page_h_px), "white")

    x0, y0 = spec.margin_px, spec.margin_px
    x, y = x0, y0
    col = row = 0

    def new_page():
        return Image.new("RGB", (spec.page_w_px, spec.page_h_px), "white")

    for i, item in enumerate(items):
        label = render_single_label(item, spec)
        page.paste(label, (x, y))

        col += 1
        if col < spec.cols:
            x += spec.label_w_px + spec.gutter_px
        else:
            col = 0
            x = x0
            row += 1
            if row < spec.rows:
                y += spec.label_h_px + spec.gutter_px
            else:
                pages.append(page)
                page = new_page()
                x, y = x0, y0
                row = 0

    # Append last partially filled page
    pages.append(page)
    return pages

def pages_to_pdf_bytes(pages: List[Image.Image]) -> bytes:
    # Ensure RGB
    pages = [p.convert("RGB") for p in pages]
    buf = io.BytesIO()
    if len(pages) == 1:
        pages[0].save(buf, format="PDF", resolution=300.0)
    else:
        pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:], resolution=300.0)
    buf.seek(0)
    return buf.read()

def coerce_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    records = df.to_dict(orient="records")
    cleaned = []
    for r in records:
        obj = {k: ("" if pd.isna(v) else str(v)) for k, v in r.items()}
        # Keep only required keys (missing -> "")
        for key in REQUIRED_FIELDS:
            obj.setdefault(key, "")
        # Validate EAN13
        if not ean13_is_valid(obj.get("barcode", "")):
            continue
        cleaned.append(obj)
    return cleaned

# -------------- UI --------------

st.set_page_config(page_title="Label PDF Generator (Streamlit)", page_icon="🏷️", layout="wide")
st.title("🏷️ Label PDF Generator")
st.caption("JSON/Excel → EAN-13 barcodes → Printable PDF (A4)")

with st.sidebar:
    st.subheader("Layout")
    cols = st.number_input("Columns per page", 1, 6, 2)
    rows = st.number_input("Rows per page", 1, 12, 5)
    label_w = st.number_input("Label width (mm)", 30.0, 120.0, 80.0, step=1.0)
    label_h = st.number_input("Label height (mm)", 20.0, 120.0, 50.0, step=1.0)
    margin = st.number_input("Page margin (mm)", 0.0, 20.0, 4.0, step=0.5)
    gutter = st.number_input("Gutter (mm)", 0.0, 20.0, 4.0, step=0.5)
    dpi = st.number_input("DPI", 150, 600, 300, step=50)

uploaded = st.file_uploader("Upload JSON or Excel (columns: styleName, colorRef, artSeason, styleRef, size, price, barcode)", type=["json", "xlsx", "xls"])
example = st.toggle("Use example data (if no file uploaded)", value=(uploaded is None))

if uploaded is not None:
    suffix = pathlib.Path(uploaded.name).suffix.lower()
    try:
        if suffix == ".json":
            data = json.load(uploaded)
            df = pd.DataFrame(data)
        else:
            df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        st.stop()
elif example:
    # Starter rows
    df = pd.DataFrame([
        {"styleName":"Summer Collection T-Shirt","colorRef":"BLUE-001","artSeason":"SS2023","styleRef":"ART-12345","size":"M","price":"59,99 €","barcode":"3607186681381"},
        {"styleName":"Classic Polo","colorRef":"GRN-204","artSeason":"SS2023","styleRef":"ART-77831","size":"L","price":"69,99 €","barcode":"3607186681381"},
        {"styleName":"Denim Jacket","colorRef":"DEN-800","artSeason":"AW2024","styleRef":"DJ-00912","size":"S","price":"99,00 €","barcode":"3607186681381"},
        {"styleName":"Chino Pants","colorRef":"BEI-110","artSeason":"AW2024","styleRef":"CP-55123","size":"32","price":"79,50 €","barcode":"3607186681381"},
        {"styleName":"Hoodie","colorRef":"BLK-900","artSeason":"AW2024","styleRef":"HD-77100","size":"XL","price":"89,00 €","barcode":"3607186681381"}
    ])
else:
    st.info("Upload a file or enable example data to continue.")
    st.stop()

records = coerce_records(df)
if not records:
    st.error("No valid rows found. Check required columns and EAN-13 codes.")
    st.stop()

spec = LabelSpec(
    width_mm=label_w, height_mm=label_h, margin_mm=margin,
    gutter_mm=gutter, cols=int(cols), rows=int(rows), dpi=int(dpi)
)

if st.button("Generate PDF"):
    with st.spinner("Rendering labels…"):
        pages = compose_pages(records, spec)
        pdf_bytes = pages_to_pdf_bytes(pages)

    st.success(f"Done! Generated {len(pages)} page(s).")
    st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name="labels.pdf", mime="application/pdf")

    # Show a preview of the first page
    preview = pages[0].resize((int(pages[0].width * 0.35), int(pages[0].height * 0.35)))
    st.image(preview, caption="First page preview")

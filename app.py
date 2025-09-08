import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO

from utils.data_loader import read_table, normalize_columns, auto_map_columns
from utils.template import load_svg, set_text, set_text_multiline, clear_children, inject_svg_image, to_string
from utils.render import svg_to_png, svg_to_pdf, make_zip

# ====== App Config ======
st.set_page_config(page_title="Label Generator", page_icon="🏷️", layout="wide")
st.title("🏷️ Label Generator (SVG → PNG/PDF)")

# ====== Sidebar: Settings ======
with st.sidebar:
    st.header("⚙️ Settings")
    output_fmt = st.selectbox("Export format", ["PNG", "PDF"])
    dpi = st.slider("DPI (raster/export)", min_value=150, max_value=600, value=300, step=50)
    fname_prefix = st.text_input("Output file prefix", value="label")
    max_preview = st.number_input("Preview rows", min_value=1, max_value=20, value=3, step=1)
    st.caption("PNG/PDF দুটোই লাগলে রান দুবার করো — অথবা কোডে সহজেই ডুয়াল-এক্সপোর্ট যোগ করা যাবে।")

# ====== Inputs ======
col1, col2 = st.columns([1,1])

with col1:
    st.subheader("📄 Data")
    uploaded = st.file_uploader("Upload CSV/XLSX/XLS", type=["csv","xlsx","xls","tsv"])
    df: pd.DataFrame | None = None
    if uploaded:
        try:
            df = read_table(uploaded, filename=uploaded.name)
            df = normalize_columns(df)
            st.success(f"Loaded {len(df)} rows")
            st.dataframe(df.head(10))
        except Exception as e:
            st.error(f"Failed to read file: {e}")

with col2:
    st.subheader("🧩 Template")
    # Allow user to use provided template file path or upload
    default_tpl_path = Path("templates/Tamplate-01_patched.svg")
    use_default = st.checkbox("Use templates/Tamplate-01_patched.svg", value=default_tpl_path.exists())
    tpl_svg_text = None
    if use_default:
        if default_tpl_path.exists():
            tpl_svg_text = default_tpl_path.read_text(encoding="utf-8")
            st.success("Default template found.")
        else:
            st.warning("Default template missing. Upload your SVG below.")
    user_tpl = st.file_uploader("Or upload SVG template", type=["svg"], key="tpl")
    if user_tpl:
        tpl_svg_text = user_tpl.read().decode("utf-8")
        st.success("Uploaded template will be used.")

if tpl_svg_text is None:
    st.info("Upload a template SVG or enable the default.")
    st.stop()

# ====== Column Mapping ======
if df is not None:
    st.subheader("🔗 Column Mapping")
    guessed = auto_map_columns(df)
    c1, c2, c3 = st.columns(3)

    with c1:
        col_style = st.selectbox("STYLE_NAME →", [None] + list(df.columns), index=(1 + list(df.columns).index(guessed["STYLE_NAME"])) if guessed["STYLE_NAME"] in df.columns else 0)
        col_color = st.selectbox("COLOR_NAME_REF →", [None] + list(df.columns), index=(1 + list(df.columns).index(guessed["COLOR_NAME_REF"])) if guessed["COLOR_NAME_REF"] in df.columns else 0)
    with c2:
        col_season = st.selectbox("ART_SEASON_STYLE_REF →", [None] + list(df.columns), index=(1 + list(df.columns).index(guessed["ART_SEASON_STYLE_REF"])) if guessed["ART_SEASON_STYLE_REF"] in df.columns else 0)
        col_size = st.selectbox("SIZE_VALUE →", [None] + list(df.columns), index=(1 + list(df.columns).index(guessed["SIZE_VALUE"])) if guessed["SIZE_VALUE"] in df.columns else 0)
    with c3:
        col_price = st.selectbox("PRICE_VALUE →", [None] + list(df.columns), index=(1 + list(df.columns).index(guessed["PRICE_VALUE"])) if guessed["PRICE_VALUE"] in df.columns else 0)
        col_barcode = st.selectbox("BARCODE (for EAN13/Code128) →", [None] + list(df.columns), index=(1 + list(df.columns).index(guessed.get("BARCODE") or "")) if guessed.get("BARCODE") in df.columns else 0)

    mapping = {
        "STYLE_NAME": col_style,
        "COLOR_NAME_REF": col_color,
        "ART_SEASON_STYLE_REF": col_season,
        "SIZE_VALUE": col_size,
        "PRICE_VALUE": col_price,
        "BARCODE": col_barcode,
    }

    # ====== Preview ======
    st.subheader("👀 Preview")
    n = min(int(max_preview), len(df))
    preview_rows = df.head(n).to_dict(orient="records")
    prev_imgs = []
    for i, row in enumerate(preview_rows, start=1):
        # build one SVG per row
        root = load_svg(BytesIO(tpl_svg_text.encode("utf-8")))
        r = {k: (mapping[k] and row.get(mapping[k])) for k in mapping}

        # text fields (STYLE/COLOR/SEASON multi-line safe)
        set_text_multiline(root.getroot(), "STYLE_NAME", r["STYLE_NAME"], max_chars=24)
        set_text_multiline(root.getroot(), "COLOR_NAME_REF", r["COLOR_NAME_REF"], max_chars=24)
        set_text_multiline(root.getroot(), "ART_SEASON_STYLE_REF", r["ART_SEASON_STYLE_REF"], max_chars=26)
        set_text(root.getroot(), "SIZE_VALUE", r["SIZE_VALUE"])
        set_text(root.getroot(), "PRICE_VALUE", r["PRICE_VALUE"])

        # barcode slot
        clear_children(root.getroot(), "BARCODE_SLOT")
        code = r.get("BARCODE")
        if code:
            try:
                # Prefer EAN13 if numeric length>=12, else fallback to Code128
                from barcode import EAN13, Code128
                from barcode.writer import SVGWriter
                from io import BytesIO
                bw = SVGWriter()
                buff = BytesIO()
                code_str = str(code).strip()
                if code_str.isdigit() and len(code_str) >= 12:
                    EAN13(code_str[:12], writer=bw).write(buff, {"module_width":0.20, "module_height":12, "font_size":8})
                else:
                    Code128(code_str, writer=bw).write(buff, {"module_width":0.28, "module_height":12, "font_size":8})
                barcode_svg = buff.getvalue().decode("utf-8")
                inject_svg_image(root.getroot(), "BARCODE_SLOT", barcode_svg, width_mm=22.0, height_mm=10.0)
            except Exception as e:
                st.warning(f"Row {i}: barcode render failed ({e})")

        svg_text = to_string(root.getroot())
        # render to PNG in memory for preview
        try:
            import cairosvg, base64
            png_bytes = cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), dpi=300)
            b64 = base64.b64encode(png_bytes).decode("ascii")
            prev_imgs.append((i, f"data:image/png;base64,{b64}", svg_text))
        except Exception as e:
            st.error(f"Preview render failed on row {i}: {e}")

    # show previews
    cols = st.columns(n if n>0 else 1)
    for (i, b64_png, _svg) in prev_imgs:
        with cols[(i-1) % len(cols)]:
            st.image(b64_png, caption=f"Row {i}")

    # ====== Generate Button ======
    st.subheader("📦 Export")
    out_dir = Path("outputs")
    if st.button("Generate All"):
        exported_paths = []
        for idx, row in df.iterrows():
            root = load_svg(BytesIO(tpl_svg_text.encode("utf-8")))
            r = {k: (mapping[k] and row.get(mapping[k])) for k in mapping}

            set_text_multiline(root.getroot(), "STYLE_NAME", r["STYLE_NAME"], max_chars=24)
            set_text_multiline(root.getroot(), "COLOR_NAME_REF", r["COLOR_NAME_REF"], max_chars=24)
            set_text_multiline(root.getroot(), "ART_SEASON_STYLE_REF", r["ART_SEASON_STYLE_REF"], max_chars=26)
            set_text(root.getroot(), "SIZE_VALUE", r["SIZE_VALUE"])
            set_text(root.getroot(), "PRICE_VALUE", r["PRICE_VALUE"])

            clear_children(root.getroot(), "BARCODE_SLOT")
            code = r.get("BARCODE")
            if code:
                try:
                    from barcode import EAN13, Code128
                    from barcode.writer import SVGWriter
                    from io import BytesIO
                    bw = SVGWriter()
                    buff = BytesIO()
                    code_str = str(code).strip()
                    if code_str.isdigit() and len(code_str) >= 12:
                        EAN13(code_str[:12], writer=bw).write(buff, {"module_width":0.20, "module_height":12, "font_size":8})
                    else:
                        Code128(code_str, writer=bw).write(buff, {"module_width":0.28, "module_height":12, "font_size":8})
                    barcode_svg = buff.getvalue().decode("utf-8")
                    inject_svg_image(root.getroot(), "BARCODE_SLOT", barcode_svg, width_mm=22.0, height_mm=10.0)
                except Exception:
                    pass

            svg_text = to_string(root.getroot())

            # file name parts
            style = str(r.get("STYLE_NAME") or "").strip().replace(" ", "_")[:30]
            color = str(r.get("COLOR_NAME_REF") or "").strip().replace(" ", "_")[:30]
            size  = str(r.get("SIZE_VALUE") or "").strip().replace(" ", "_")[:10]
            base = f"{fname_prefix}_{idx:04d}_{style}_{color}_{size}".strip("_")

            if output_fmt == "PNG":
                out_path = out_dir / f"{base}.png"
                svg_to_png(svg_text, str(out_path), dpi=dpi)
            else:
                out_path = out_dir / f"{base}.pdf"
                svg_to_pdf(svg_text, str(out_path), dpi=dpi)

            exported_paths.append(str(out_path))

        if exported_paths:
            zip_path = make_zip(exported_paths, str(out_dir / f"{fname_prefix}_batch.zip"))
            with open(zip_path, "rb") as f:
                st.success(f"Generated {len(exported_paths)} files")
                st.download_button("Download ZIP", data=f.read(), file_name=Path(zip_path).name, mime="application/zip")

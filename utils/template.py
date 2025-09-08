from __future__ import annotations
from lxml import etree
from io import BytesIO
import base64
from typing import Optional

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
NSMAP = {"svg": SVG_NS, "xlink": XLINK_NS}

def load_svg(path: str) -> etree._ElementTree:
    return etree.parse(path)

def set_text(root, element_id: str, value: str | None, hide_if_empty: bool = True):
    nodes = root.xpath(f'//*[@id="{element_id}"]')
    if not nodes:
        return
    node = nodes[0]
    if (value is None or str(value).strip() == "") and hide_if_empty:
        node.attrib["display"] = "none"
        return
    # ensure visible
    if "display" in node.attrib:
        del node.attrib["display"]
    node.text = str(value)

def clear_children(root, group_id: str):
    nodes = root.xpath(f'//*[@id="{group_id}"]')
    if not nodes:
        return
    g = nodes[0]
    for ch in list(g):
        g.remove(ch)

def inject_svg_image(root, group_id: str, svg_string: str, width_mm: float = 22.0, height_mm: float = 10.0):
    """Embed an SVG barcode as <image> (base64) into a group slot."""
    b64 = base64.b64encode(svg_string.encode("utf-8")).decode("ascii")
    nodes = root.xpath(f'//*[@id="{group_id}"]')
    if not nodes:
        return
    g = nodes[0]
    image_el = etree.Element(f"{{{SVG_NS}}}image", {
        f"{{{XLINK_NS}}}href": f"data:image/svg+xml;base64,{b64}",
        "width": f"{width_mm}mm",
        "height": f"{height_mm}mm",
        "x": "0mm",
        "y": "0mm",
        "preserveAspectRatio": "xMidYMid meet",
    })
    g.append(image_el)

def to_string(root) -> str:
    return etree.tostring(root, encoding="utf-8").decode("utf-8")

def wrap_text_simple(text: str, max_chars: int = 24) -> str:
    """
    A simple soft-wrap to insert newline (for later <tspan> handling if needed).
    """
    text = str(text or "")
    if len(text) <= max_chars:
        return text
    words = text.split()
    lines = []
    current = ""
    for w in words:
        if len((current + " " + w).strip()) <= max_chars:
            current = (current + " " + w).strip()
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return "\n".join(lines)

def set_text_multiline(root, element_id: str, value: str | None, max_chars: int = 24):
    """
    Replace the <text> contents with multiple <tspan> lines if needed.
    Assumes the <text> has x/y and text-anchor already set in the template.
    """
    nodes = root.xpath(f'//*[@id="{element_id}"]')
    if not nodes:
        return
    text_el = nodes[0]
    if value is None or str(value).strip() == "":
        text_el.attrib["display"] = "none"
        return

    if "display" in text_el.attrib:
        del text_el.attrib["display"]

    # clear existing children
    for ch in list(text_el):
        text_el.remove(ch)

    wrapped = wrap_text_simple(str(value), max_chars=max_chars).split("\n")
    # read y from attribute; if missing, default dy increments
    y = float(text_el.attrib.get("y", "0"))
    x = text_el.attrib.get("x", None)
    dy_first = 0
    dy_next = 4 # approximate line gap (in SVG user units; template uses mm viewBox -> tune if needed)

    for i, line in enumerate(wrapped):
        tspan = etree.Element(f"{{{SVG_NS}}}tspan")
        if x is not None:
            tspan.attrib["x"] = x
        if i == 0:
            tspan.attrib["dy"] = str(dy_first)
        else:
            tspan.attrib["dy"] = str(dy_next)
        tspan.text = line
        text_el.append(tspan)


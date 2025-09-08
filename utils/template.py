# utils/template.py  (pure stdlib, no lxml)
from __future__ import annotations
from xml.etree import ElementTree as ET
import base64

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

def load_svg(path_or_filelike) -> ET.ElementTree:
    if hasattr(path_or_filelike, "read"):
        data = path_or_filelike.read()
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        root = ET.fromstring(data)
        return ET.ElementTree(root)
    return ET.parse(path_or_filelike)

def _find_by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    for el in root.iter():
        if el.attrib.get("id") == element_id:
            return el
    return None

def set_text(root: ET.Element, element_id: str, value: str | None, hide_if_empty: bool = True):
    node = _find_by_id(root, element_id)
    if node is None:
        return
    if (value is None or str(value).strip() == "") and hide_if_empty:
        node.attrib["display"] = "none"
        return
    if "display" in node.attrib:
        del node.attrib["display"]
    node.text = str(value)

def _wrap(text: str, max_chars: int = 24) -> list[str]:
    s = str(text or "").strip()
    if len(s) <= max_chars:
        return [s]
    words, lines, cur = s.split(), [], ""
    for w in words:
        nxt = (cur + " " + w).strip()
        if len(nxt) <= max_chars:
            cur = nxt
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def set_text_multiline(root: ET.Element, element_id: str, value: str | None, max_chars: int = 24):
    node = _find_by_id(root, element_id)
    if node is None:
        return
    if value is None or str(value).strip() == "":
        node.attrib["display"] = "none"
        return
    if "display" in node.attrib:
        del node.attrib["display"]
    for ch in list(node):
        node.remove(ch)
    x = node.attrib.get("x")
    for i, line in enumerate(_wrap(value, max_chars=max_chars)):
        tspan = ET.Element(f"{{{SVG_NS}}}tspan")
        if x is not None: tspan.set("x", x)
        tspan.set("dy", "0" if i == 0 else "4")  # line gap tune
        tspan.text = line
        node.append(tspan)

def clear_children(root: ET.Element, group_id: str):
    g = _find_by_id(root, group_id)
    if g is None: return
    for ch in list(g):
        g.remove(ch)

def inject_svg_image(root: ET.Element, group_id: str, svg_string: str, width_mm: float = 22.0, height_mm: float = 10.0):
    g = _find_by_id(root, group_id)
    if g is None: return
    b64 = base64.b64encode(svg_string.encode("utf-8")).decode("ascii")
    img = ET.Element(f"{{{SVG_NS}}}image")
    img.set(f"{{{XLINK_NS}}}href", f"data:image/svg+xml;base64,{b64}")
    img.set("width", f"{width_mm}mm"); img.set("height", f"{height_mm}mm")
    img.set("x", "0mm"); img.set("y", "0mm")
    img.set("preserveAspectRatio", "xMidYMid meet")
    g.append(img)

def to_string(root: ET.Element) -> str:
    return ET.tostring(root, encoding="unicode")

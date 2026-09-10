"""Adaptive per-page PDF compression.

Shrinks the embedded scan image on each page by downsampling to a target DPI
and re-encoding as JPEG. Each page is classified automatically: pages that are
essentially black text become grayscale (smaller); pages containing color
figures stay in color. Images are shrunk by transforming the embedded image
bytes directly (extract -> resize -> recompress -> swap), so this composes with
the deskew rotation transform without re-rotating, and the OCR text layer is
left untouched.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, asdict

import numpy as np
import pymupdf
from PIL import Image


@dataclass
class CompressOptions:
    dpi: int = 120                # target resolution for the page image
    quality_color: int = 55       # JPEG quality for color pages
    quality_gray: int = 45        # JPEG quality for grayscale pages
    color_threshold: float = 0.015  # min fraction of colored pixels -> keep color
    color_mode: str = "auto"      # auto | force_color | force_gray


def _colored_fraction(pil) -> float:
    a = np.asarray(pil.convert("RGB")).astype(np.int16)
    spread = a.max(2) - a.min(2)
    return float((spread > 40).mean())


def _keep_color(pil, o: CompressOptions) -> bool:
    if o.color_mode == "force_color":
        return True
    if o.color_mode == "force_gray":
        return False
    return _colored_fraction(pil) > o.color_threshold


def compress_pdf_bytes(data: bytes, o: CompressOptions | None = None):
    """Return (output_pdf_bytes, report_dict)."""
    o = o or CompressOptions()
    doc = pymupdf.open(stream=data, filetype="pdf")
    pages = []

    for i, page in enumerate(doc):
        pw_in = page.rect.width / 72.0
        ph_in = page.rect.height / 72.0
        imgs = page.get_images(full=True)
        page_mode = "none"
        for im in imgs:
            xref = im[0]
            try:
                d = doc.extract_image(xref)
            except Exception:  # noqa: BLE001
                continue
            pil = Image.open(io.BytesIO(d["image"]))
            tw = max(1, int(round(o.dpi * pw_in)))
            th = max(1, int(round(o.dpi * ph_in)))
            if pil.width > tw or pil.height > th:
                pil = pil.resize((tw, th), Image.LANCZOS)
            color = _keep_color(pil, o)
            page_mode = "color" if color else "gray"
            out = io.BytesIO()
            if color:
                pil.convert("RGB").save(out, "JPEG", quality=o.quality_color, optimize=True)
            else:
                pil.convert("L").save(out, "JPEG", quality=o.quality_gray, optimize=True)
            page.replace_image(xref, stream=out.getvalue())
        pages.append({"page": i + 1, "mode": page_mode})

    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True, clean=True)
    out_bytes = buf.getvalue()

    report = {
        "pages": pages,
        "page_count": len(pages),
        "color_pages": sum(1 for p in pages if p["mode"] == "color"),
        "gray_pages": sum(1 for p in pages if p["mode"] == "gray"),
        "options": asdict(o),
        "in_bytes": len(data),
        "out_bytes": len(out_bytes),
    }
    return out_bytes, report

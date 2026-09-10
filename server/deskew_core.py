"""Core deskew logic for predictable ADF scanner tilt.

Odd and even pages tilt in opposite directions by a near-constant amount.
Each page's content is rotated around its center via a PDF transform, so the
scanned image is never re-encoded and any OCR text layer stays aligned.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, asdict

import numpy as np
import pymupdf
from deskew import determine_skew
from pypdf import PdfReader, PdfWriter, Transformation


@dataclass
class Options:
    mode: str = "hybrid"          # hybrid | auto | fixed
    base: float = 1.4             # fixed parity magnitude (deg)
    odd_sign: float = -1.0        # direction for odd pages
    even_sign: float = 1.0        # direction for even pages
    min_mag: float = 0.3          # hybrid clamp floor
    max_mag: float = 2.5          # clamp ceiling
    dpi: int = 150                # measurement rasterization DPI
    search_limit: float = 8.0     # only look for skew within +/- this
    resolution: float = 0.2       # angular search resolution (deg)


def _measure(page, o: Options):
    pix = page.get_pixmap(dpi=o.dpi, colorspace=pymupdf.csGRAY)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    a = determine_skew(img, min_angle=-o.search_limit, max_angle=o.search_limit,
                        min_deviation=o.resolution)
    return None if a is None else float(a)


def _choose(page_no: int, measured, o: Options):
    expected = (o.odd_sign if page_no % 2 == 1 else o.even_sign) * o.base
    if o.mode == "fixed":
        return expected, "fixed"
    if measured is None:
        return expected, "fallback: no skew detected"
    if o.mode == "auto":
        return float(np.sign(measured)) * min(abs(measured), o.max_mag), "auto"
    # hybrid
    if np.sign(measured) != np.sign(expected) and abs(measured) > 1e-6:
        return expected, "fallback: sign mismatch"
    mag = min(max(abs(measured), o.min_mag), o.max_mag)
    return float(np.sign(expected)) * mag, "hybrid"


def _rotate(page, angle: float):
    cx = float(page.mediabox.width) / 2.0
    cy = float(page.mediabox.height) / 2.0
    page.add_transformation(
        Transformation().translate(-cx, -cy).rotate(angle).translate(cx, cy)
    )


def deskew_pdf_bytes(data: bytes, o: Options | None = None):
    """Return (output_pdf_bytes, report_dict)."""
    o = o or Options()
    reader = PdfReader(io.BytesIO(data))
    writer = PdfWriter()
    mdoc = pymupdf.open(stream=data, filetype="pdf")
    n = len(reader.pages)

    pages = []
    for i in range(n):
        page_no = i + 1
        measured = None if o.mode == "fixed" else _measure(mdoc[i], o)
        angle, reason = _choose(page_no, measured, o)
        page = reader.pages[i]
        _rotate(page, angle)
        writer.add_page(page)
        pages.append({
            "page": page_no,
            "parity": "odd" if page_no % 2 == 1 else "even",
            "measured": None if measured is None else round(measured, 2),
            "applied": round(angle, 2),
            "reason": reason,
        })

    mdoc.close()  # release the measurement copy before writing the output
    if reader.metadata:
        writer.add_metadata(reader.metadata)
    buf = io.BytesIO()
    writer.write(buf)
    out = buf.getvalue()

    report = {
        "pages": pages,
        "page_count": n,
        "options": asdict(o),
        "in_bytes": len(data),
        "out_bytes": len(out),
    }
    return out, report

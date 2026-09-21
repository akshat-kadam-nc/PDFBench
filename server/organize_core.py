"""Organize pages: render page thumbnails, and rebuild a PDF from a new page
order with per-page rotation and deletions.

Reordering / rotating / deleting is a lossless pypdf structural operation — the
page content (including the OCR/searchable text layer) is copied untouched.
"""
from __future__ import annotations

import base64
import io

import pymupdf
from pypdf import PdfReader, PdfWriter


def render_thumbs(data: bytes, scale: float = 0.2) -> dict:
    """Return small PNG thumbnails (data URLs) for every page."""
    doc = pymupdf.open(stream=data, filetype="pdf")
    mat = pymupdf.Matrix(scale, scale)
    pages = []
    try:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=mat, alpha=False)
            b64 = base64.b64encode(pix.tobytes("png")).decode("ascii")
            pages.append({"i": i, "w": pix.width, "h": pix.height,
                          "thumb": "data:image/png;base64," + b64})
        count = doc.page_count
    finally:
        doc.close()
    return {"count": count, "pages": pages}


def organize(data: bytes, ops: list[dict]) -> tuple[bytes, dict]:
    """Build a new PDF from `ops` = [{index, rotate}], in order.

    `index` is the 0-based page in the source; `rotate` is clockwise degrees
    (multiple of 90). Pages not listed are dropped.
    """
    reader = PdfReader(io.BytesIO(data))
    n = len(reader.pages)
    writer = PdfWriter()
    for op in ops:
        idx = int(op["index"])
        if idx < 0 or idx >= n:
            continue
        rot = int(op.get("rotate", 0)) % 360
        page = reader.pages[idx]
        if rot:
            page.rotate(rot)  # lossless: adds to /Rotate, content untouched
        writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    out = buf.getvalue()
    return out, {"pages": len(writer.pages), "out_bytes": len(out)}

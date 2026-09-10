"""Merge multiple PDFs into one (lossless)."""
from __future__ import annotations

import io

from pypdf import PdfReader, PdfWriter


def merge_pdfs(files: list[tuple[str, bytes]]):
    """files: list of (name, bytes) in the desired order.
    Return (merged_bytes, report_dict)."""
    writer = PdfWriter()
    parts = []
    for name, data in files:
        reader = PdfReader(io.BytesIO(data))
        n = len(reader.pages)
        for page in reader.pages:
            writer.add_page(page)
        parts.append({"name": name, "pages": n, "bytes": len(data)})

    buf = io.BytesIO()
    writer.write(buf)
    out = buf.getvalue()
    report = {
        "parts": parts,
        "file_count": len(parts),
        "total_pages": sum(p["pages"] for p in parts),
        "out_bytes": len(out),
    }
    return out, report

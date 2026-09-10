"""FastAPI server: serves the React frontend and runs deskew / compress / merge."""
from __future__ import annotations

import json
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .deskew_core import Options as DeskewOptions, deskew_pdf_bytes
from .compress_core import CompressOptions, compress_pdf_bytes
from .merge_core import merge_pdfs

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(os.path.dirname(HERE), "web")

app = FastAPI(title="DeskewPDF")


def _pdf_response(out: bytes, filename: str, report: dict) -> Response:
    return Response(
        content=out,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Report": json.dumps(report),
            "Access-Control-Expose-Headers": "X-Report, Content-Disposition",
        },
    )


@app.post("/api/process")
async def process(
    file: UploadFile = File(...),
    deskew: bool = Form(True),
    compress: bool = Form(False),
    # deskew params
    mode: str = Form("hybrid"),
    base: float = Form(1.4),
    odd_sign: float = Form(-1.0),
    even_sign: float = Form(1.0),
    # compress params
    dpi: int = Form(120),
    quality_color: int = Form(55),
    quality_gray: int = Form(45),
    color_mode: str = Form("auto"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a .pdf file.")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")

    in_bytes = len(data)
    report: dict = {"steps": []}
    try:
        if deskew:
            data, dsrep = deskew_pdf_bytes(
                data, DeskewOptions(mode=mode, base=base, odd_sign=odd_sign, even_sign=even_sign)
            )
            report["deskew"] = dsrep
            report["steps"].append("deskew")
        if compress:
            data, crep = compress_pdf_bytes(
                data, CompressOptions(dpi=dpi, quality_color=quality_color,
                                      quality_gray=quality_gray, color_mode=color_mode)
            )
            report["compress"] = crep
            report["steps"].append("compress")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Failed to process PDF: {e}")

    report["in_bytes"] = in_bytes
    report["out_bytes"] = len(data)
    if not report["steps"]:
        raise HTTPException(400, "Nothing to do: enable deskew and/or compress.")

    stem = os.path.splitext(os.path.basename(file.filename))[0]
    suffix = "_" + "_".join(report["steps"])
    return _pdf_response(data, f"{stem}{suffix}.pdf", report)


@app.post("/api/merge")
async def merge(files: list[UploadFile] = File(...), name: str = Form("book")):
    if len(files) < 2:
        raise HTTPException(400, "Select at least two PDFs to merge.")
    parts = []
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(400, f"Not a PDF: {f.filename}")
        parts.append((f.filename, await f.read()))
    try:
        out, report = merge_pdfs(parts)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Failed to merge: {e}")
    safe = "".join(c for c in name if c.isalnum() or c in " _-").strip() or "book"
    return _pdf_response(out, f"{safe}.pdf", report)


# ── static frontend ────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(os.path.join(WEB, "index.html"))


app.mount("/", StaticFiles(directory=WEB), name="web")

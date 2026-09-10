"""FastAPI server: serves the React frontend and runs the deskew endpoint."""
from __future__ import annotations

import json
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .deskew_core import Options, deskew_pdf_bytes

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(os.path.dirname(HERE), "web")

app = FastAPI(title="DeskewPDF")


@app.post("/api/deskew")
async def deskew(
    file: UploadFile = File(...),
    mode: str = Form("hybrid"),
    base: float = Form(1.4),
    odd_sign: float = Form(-1.0),
    even_sign: float = Form(1.0),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a .pdf file.")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")
    try:
        out, report = deskew_pdf_bytes(
            data, Options(mode=mode, base=base, odd_sign=odd_sign, even_sign=even_sign)
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Failed to process PDF: {e}")

    stem = os.path.splitext(os.path.basename(file.filename))[0]
    return Response(
        content=out,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{stem}_deskewed.pdf"',
            "X-Deskew-Report": json.dumps(report),
            "Access-Control-Expose-Headers": "X-Deskew-Report, Content-Disposition",
        },
    )


@app.get("/")
async def index():
    return FileResponse(os.path.join(WEB, "index.html"))


app.mount("/", StaticFiles(directory=WEB), name="web")

"""FastAPI server: serves the React frontend and runs deskew / compress / merge."""
from __future__ import annotations

import gc
import json
import logging
import os
import sys
import time

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .deskew_core import Options as DeskewOptions, deskew_pdf_bytes
from .compress_core import CompressOptions, compress_pdf_bytes
from .merge_core import merge_pdfs
from .organize_core import render_thumbs, organize as organize_pdf
from . import history

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("deskewpdf")

HERE = os.path.dirname(os.path.abspath(__file__))
# When frozen by PyInstaller, bundled data lives under sys._MEIPASS/web.
if getattr(sys, "frozen", False):
    WEB = os.path.join(sys._MEIPASS, "web")  # type: ignore[attr-defined]
else:
    WEB = os.path.join(os.path.dirname(HERE), "web")

# Guard rails
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "80"))

app = FastAPI(title="PDF Bench")


def _peak_mem_mb() -> float | None:
    """Peak resident memory of this process, in MB (Linux/Mac). None on Windows."""
    try:
        import resource  # not available on Windows
        kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return kb / 1024.0  # ru_maxrss is in KB on Linux
    except Exception:  # noqa: BLE001
        return None


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.time()
    try:
        resp = await call_next(request)
    except Exception:  # noqa: BLE001 — last-resort net so the client gets JSON, not a bare 500
        log.exception("Unhandled error: %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500,
                            content={"detail": "Internal server error (see server logs)."})
    if request.url.path.startswith("/api"):
        log.info("%s %s -> %s (%.0f ms)", request.method, request.url.path,
                 resp.status_code, (time.time() - start) * 1000)
    return resp


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


def _check_size(name: str, data: bytes):
    if not data:
        raise HTTPException(400, f"{name} is empty.")
    mb = len(data) / 1_048_576
    if mb > MAX_UPLOAD_MB:
        raise HTTPException(
            413, f"{name} is {mb:.0f} MB, over the {MAX_UPLOAD_MB} MB limit. "
                 f"Split it into smaller chapters, or raise MAX_UPLOAD_MB / server RAM.")


@app.post("/api/process")
async def process(
    file: UploadFile = File(...),
    deskew: bool = Form(True),
    compress: bool = Form(False),
    mode: str = Form("hybrid"),
    base: float = Form(1.4),
    odd_sign: float = Form(-1.0),
    even_sign: float = Form(1.0),
    dpi: int = Form(110),
    quality_color: int = Form(52),
    quality_gray: int = Form(45),
    color_mode: str = Form("force_color"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a .pdf file.")
    data = await file.read()
    _check_size(file.filename, data)
    in_bytes = len(data)
    log.info("process start: file=%s size=%.1fMB deskew=%s compress=%s dpi=%s q=%s/%s color=%s",
             file.filename, in_bytes / 1e6, deskew, compress, dpi, quality_color, quality_gray, color_mode)

    report: dict = {"steps": []}
    try:
        if deskew:
            t = time.time()
            data, dsrep = deskew_pdf_bytes(
                data, DeskewOptions(mode=mode, base=base, odd_sign=odd_sign, even_sign=even_sign))
            report["deskew"] = dsrep
            report["steps"].append("deskew")
            log.info("  deskew ok: %d pages in %.1fs", dsrep["page_count"], time.time() - t)
            gc.collect()
        if compress:
            t = time.time()
            data, crep = compress_pdf_bytes(
                data, CompressOptions(dpi=dpi, quality_color=quality_color,
                                      quality_gray=quality_gray, color_mode=color_mode))
            report["compress"] = crep
            report["steps"].append("compress")
            log.info("  compress ok: %d pages, %.1fMB in %.1fs",
                     crep["page_count"], crep["out_bytes"] / 1e6, time.time() - t)
    except MemoryError:
        log.exception("process OOM: file=%s size=%.1fMB", file.filename, in_bytes / 1e6)
        raise HTTPException(
            507, "The server ran out of memory processing this file. Try a smaller chapter, "
                 "a lower DPI, or a larger server plan.")
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        log.exception("process failed: file=%s", file.filename)
        raise HTTPException(500, f"{type(e).__name__}: {e}")

    if not report["steps"]:
        raise HTTPException(400, "Nothing to do: enable deskew and/or compress.")

    report["in_bytes"] = in_bytes
    report["out_bytes"] = len(data)
    peak = _peak_mem_mb()
    if peak:
        report["peak_mem_mb"] = round(peak)
    log.info("process done: %s %.1fMB -> %.1fMB%s",
             file.filename, in_bytes / 1e6, len(data) / 1e6,
             f", peak RSS {peak:.0f}MB" if peak else "")

    stem = os.path.splitext(os.path.basename(file.filename))[0]
    out_name = f"{stem}_{'_'.join(report['steps'])}.pdf"
    pages = ((report.get("deskew") or report.get("compress") or {}).get("page_count"))
    history.record({"op": "process", "name": out_name, "inputs": [file.filename],
                    "steps": report["steps"], "pages": pages,
                    "in_bytes": in_bytes, "out_bytes": len(data)})
    return _pdf_response(data, out_name, report)


@app.post("/api/merge")
async def merge(files: list[UploadFile] = File(...), name: str = Form("book")):
    if len(files) < 2:
        raise HTTPException(400, "Select at least two PDFs to merge.")
    parts = []
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(400, f"Not a PDF: {f.filename}")
        d = await f.read()
        _check_size(f.filename, d)
        parts.append((f.filename, d))
    log.info("merge start: %d files, %.1fMB total", len(parts), sum(len(d) for _, d in parts) / 1e6)
    try:
        out, report = merge_pdfs(parts)
    except MemoryError:
        log.exception("merge OOM")
        raise HTTPException(507, "The server ran out of memory merging these files. "
                                 "Merge fewer at a time or use a larger server plan.")
    except Exception as e:  # noqa: BLE001
        log.exception("merge failed")
        raise HTTPException(500, f"{type(e).__name__}: {e}")
    log.info("merge done: %d pages, %.1fMB", report["total_pages"], report["out_bytes"] / 1e6)
    safe = "".join(c for c in name if c.isalnum() or c in " _-").strip() or "book"
    out_name = f"{safe}.pdf"
    history.record({"op": "merge", "name": out_name,
                    "inputs": [n for n, _ in parts], "pages": report.get("total_pages"),
                    "in_bytes": sum(len(d) for _, d in parts), "out_bytes": report["out_bytes"]})
    return _pdf_response(out, out_name, report)


@app.post("/api/pages")
async def pages(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a .pdf file.")
    data = await file.read()
    _check_size(file.filename, data)
    try:
        return render_thumbs(data)
    except Exception as e:  # noqa: BLE001
        log.exception("thumbnails failed: %s", file.filename)
        raise HTTPException(500, f"{type(e).__name__}: {e}")


@app.post("/api/organize")
async def organize_ep(file: UploadFile = File(...), ops: str = Form(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a .pdf file.")
    data = await file.read()
    _check_size(file.filename, data)
    try:
        op_list = json.loads(ops)
    except Exception:  # noqa: BLE001
        raise HTTPException(400, "Invalid page operations.")
    if not op_list:
        raise HTTPException(400, "Keep at least one page.")
    try:
        out, report = organize_pdf(data, op_list)
    except Exception as e:  # noqa: BLE001
        log.exception("organize failed: %s", file.filename)
        raise HTTPException(500, f"{type(e).__name__}: {e}")
    report["in_bytes"] = len(data)
    stem = os.path.splitext(os.path.basename(file.filename))[0]
    out_name = f"{stem}_organized.pdf"
    history.record({"op": "organize", "name": out_name, "inputs": [file.filename],
                    "pages": report["pages"], "in_bytes": len(data), "out_bytes": len(out)})
    return _pdf_response(out, out_name, report)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "max_upload_mb": MAX_UPLOAD_MB}


@app.get("/api/history")
async def get_history(limit: int = 500):
    return {"items": history.read(limit=limit), "stats": history.stats(),
            "dir": history.data_dir()}


@app.delete("/api/history")
async def clear_history():
    history.clear()
    return {"ok": True}


# ── static frontend ────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(os.path.join(WEB, "index.html"))


app.mount("/", StaticFiles(directory=WEB), name="web")

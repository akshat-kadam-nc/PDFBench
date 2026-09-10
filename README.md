# DeskewPDF

Local full-stack tool to prepare scanned book chapters: **straighten** the
predictable ADF-scanner tilt, **compress** each chapter, and **merge** the
chapters into the finished book.

Two tabs:

- **Deskew & Compress** — drop one chapter PDF. Deskew rotates each page around
  its center as a **lossless transform** (scan image not re-encoded, OCR text
  layer stays selectable). Compress downsamples the page image to a target DPI
  and re-encodes it, deciding color per page automatically: pages that are
  basically black text become grayscale, pages with color figures stay color.
- **Merge** — drop all the processed chapters, order them (auto-sorted by
  filename), and combine into one PDF. Lossless. Tells you if the result is
  under 10 MB.

### Size expectations

300 pages of textured color textbook scans won't fit under 10 MB in one file at
readable quality — that needs JBIG2/MRC, which harms color diagrams. At the
default 120 DPI adaptive settings expect roughly 20–30 MB for the whole book.
Lower the DPI (e.g. 100) for smaller files, or split the book into volumes with
the Merge tab if you need each file under a hard cap.

## Run it

Double-click **`run.bat`**.

The first run creates a virtual environment and installs dependencies (takes a
minute); after that it starts instantly and opens your browser at
<http://127.0.0.1:8765>.

## How correction is decided

- **Hybrid** (default): measures each page's real skew, clamps it to a sane
  band (0.3°–2.5°), and falls back to the fixed parity angle if measurement
  fails or points the wrong way.
- **Auto**: trust the measured skew (clamped only at the top).
- **Fixed**: ignore measurement, always apply the fixed parity angle.

Controls in the UI:
- **Fallback tilt** — magnitude used for fixed/fallback (default 1.4°).
- **Direction** — which way odd vs. even pages rotate.

The result table shows, per page, the measured and applied angle plus which
method was used, so a large batch is easy to trust at a glance.

## Share it as a standalone app (no install, no server)

The heavy work (rendering, skew detection, image recompression) is too much for
a small cloud instance's RAM. The robust way to share it is to run it on each
user's own machine — which keeps the searchable OCR text layer intact (needed
for RAG) and costs nothing.

Build a single self-contained Windows executable:

```
build_exe.bat        (after run.bat has created the .venv once)
```

This produces `dist\DeskewPDF.exe` (~110 MB). Send that one file to a teammate.
They double-click it, their browser opens to the app, and everything runs
locally. Closing the console window quits it. First launch takes ~15–20s while
the bundle unpacks.

`desktop.py` is the entry point (starts the server, opens the browser); it also
works with `python desktop.py` during development.

## Deploy to Render (shareable URL)

No database required — the tool is stateless. The repo is containerized
(`Dockerfile`) and includes a Render Blueprint (`render.yaml`).

1. Push this repo to GitHub.
2. In Render: **New + → Blueprint**, pick the repo. It reads `render.yaml` and
   creates a Docker web service on the free plan.
3. Wait for the build (a few minutes), then open the service URL and share it.

Notes:
- **Free plan sleeps when idle** — the first request after a lull takes ~30–60s
  to wake, then it's fast.
- Free plan has 512 MB RAM; processing one chapter at a time stays well within
  it. Deskew/compress a big chapter, not the whole 300-page book at once.
- Not a fit for Vercel: its serverless functions cap request bodies at ~4.5 MB
  (chapters are larger) and limit execution time. Render runs it as a normal
  long-lived server with no such caps.

Run the container locally to test:

```
docker build -t deskewpdf .
docker run -p 8000:8000 deskewpdf   # then open http://localhost:8000
```

## Layout

```
DeskewPDF/
  run.bat                 local launcher (double-click)
  Dockerfile              container for Render / Railway / Fly.io
  render.yaml             Render Blueprint
  server/
    main.py               FastAPI app: serves UI + /api/process + /api/merge
    deskew_core.py        rotation + skew detection
    compress_core.py      per-page adaptive image recompression
    merge_core.py         lossless PDF merge
    requirements.txt
  web/
    index.html            React single-page frontend (drag & drop)
```

## Tech

React (frontend) + FastAPI/Python (backend). Skew detection via `deskew`,
rendering via PyMuPDF, lossless rotation via `pypdf`.

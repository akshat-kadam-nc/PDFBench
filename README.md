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

## Layout

```
DeskewPDF/
  run.bat                 launcher (double-click)
  server/
    main.py               FastAPI app: serves the UI + /api/deskew
    deskew_core.py        rotation + skew-detection logic
    requirements.txt
  web/
    index.html            React single-page frontend (drag & drop)
```

## Tech

React (frontend) + FastAPI/Python (backend). Skew detection via `deskew`,
rendering via PyMuPDF, lossless rotation via `pypdf`.

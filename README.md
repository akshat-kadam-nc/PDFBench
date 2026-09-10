# DeskewPDF

Local full-stack tool that straightens scanned PDFs where odd and even pages
tilt in opposite directions (predictable ADF scanner skew).

Drag a PDF into the page, and the corrected file downloads automatically. Each
page is rotated around its center as a **lossless PDF transform** — the scanned
image is not re-encoded and any OCR text layer stays selectable and aligned.

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

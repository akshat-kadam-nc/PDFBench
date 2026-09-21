# PDF Bench

A local desktop toolbox for scanned PDFs: **deskew** the predictable ADF-scanner
tilt, **compress** each chapter, and **merge** chapters into the finished book.
Everything runs on your own machine — no server, no cloud, and the searchable
OCR text layer is always preserved (so the output still feeds a RAG pipeline).

Tabs:

- **Deskew & Compress** — choose one chapter PDF, set options, click **Start**.
  Deskew rotates each page around its center as a **lossless transform** (scan
  image not re-encoded, OCR text layer stays selectable). Compress downsamples
  the page image to a target DPI and re-encodes it, deciding color per page.
- **Merge** — add processed chapters, order them (auto-sorted by filename), and
  combine into one lossless PDF.
- **History** — a local log of every file processed, with totals (files, input
  vs. output size, space saved). Stored at `%LOCALAPPDATA%\PDFBench`.

## Install & run (Windows)

Run the installer and launch it from the Start Menu:

```
installer\Output\PDFBench-Setup.exe
```

It installs per-user (no admin prompt), adds a Start Menu entry (and an optional
desktop shortcut), and registers an uninstaller. Then launch **PDF Bench** from
the Start Menu — it opens in its own window (no browser, no console). First
launch takes ~15–20s while the bundle unpacks. An unsigned build triggers
SmartScreen once: **More info → Run anyway**.

To share with a teammate, send them that one `PDFBench-Setup.exe`. They need no
Python and nothing else installed.

## Build from source

```
run.bat            # dev: creates .venv, runs the server in your browser
build_exe.bat      # builds dist\PDFBench.exe (windowed onefile)
```

Then compile the installer with Inno Setup 6:

```
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\PDFBench.iss
```

`desktop.py` is the app entry point: it starts the local FastAPI server on a
background thread and shows the UI in a native window (Edge WebView2). It also
runs with `python desktop.py` during development.

## How deskew correction is decided

- **Hybrid** (default): measures each page's real skew, clamps it to a sane band
  (0.3°–2.5°), and falls back to the fixed parity angle if measurement fails or
  points the wrong way.
- **Auto**: trust the measured skew (clamped only at the top).
- **Fixed**: ignore measurement, always apply the fixed parity angle.

The result table shows, per page, the measured and applied angle plus which
method was used, so a large batch is easy to trust at a glance.

### Size expectations

300 pages of textured color textbook scans won't fit under 10 MB in one file at
readable quality. At the default adaptive settings expect roughly 20–30 MB for a
whole book. Lower the DPI for smaller files, or split into volumes with Merge.

## Layout

```
PDFBench/
  desktop.py              app entry point (native window + local server)
  run.bat                 dev launcher (browser)
  build_exe.bat           builds dist\PDFBench.exe
  installer/
    PDFBench.iss          Inno Setup installer script
  assets/
    PDFBench.ico          app icon
  server/
    main.py               FastAPI app: UI + /api/process + /api/merge + /api/history
    deskew_core.py        rotation + skew detection
    compress_core.py      per-page adaptive image recompression
    merge_core.py         lossless PDF merge
    history.py            local usage log (JSONL)
    requirements.txt
  web/
    index.html            React single-page frontend
```

The repo also contains a `Dockerfile` and `render.yaml` from an earlier
cloud-hosting experiment; cloud hosting was abandoned (RAM limits vs. real
chapter sizes) in favor of this local desktop app.

## Tech

React (frontend) + FastAPI/Python (backend), packaged with PyInstaller and
pywebview. Skew detection via `deskew`, rendering via PyMuPDF, lossless rotation
via `pypdf`.

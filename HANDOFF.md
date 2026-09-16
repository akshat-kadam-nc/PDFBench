# DeskewPDF — Handoff

Paste this context into Claude Code on a new machine (after cloning the repo) to
continue work with full context.

---

I'm continuing work on **DeskewPDF**, a project already built in a previous
session. Here's the full context.

**What it is:** A local full-stack tool to prepare scanned book chapters for a
RAG pipeline. It (1) **deskews** pages — an ADF scanner tilts odd pages one way
and even pages the other by a near-constant angle; (2) **compresses** them; and
(3) **merges** chapters into a book. Scans are ~14 MB per 16-page chapter,
~300 pages total per book.

**Repo:** `https://github.com/akshat-kadam-nc/DeskewPDF` (private, branch
`master`). Clone it, then `run.bat` sets up a `.venv` and launches the app at
`http://localhost:8765`. Requires Python 3.11 + Git installed.

**Architecture:**
- Backend: FastAPI (`server/main.py`) with endpoints `/api/process` (deskew
  and/or compress) and `/api/merge`. Serves a React (CDN, single-file) frontend
  at `web/index.html` with two tabs: "Deskew & Compress" and "Merge".
- `server/deskew_core.py` — rotates each page around its center as a **lossless
  pypdf transform** (image not re-encoded, OCR text layer preserved). Hybrid
  skew detection via the `deskew` lib (scikit-image), clamped, with a fixed
  parity-angle fallback.
- `server/compress_core.py` — shrinks the embedded page image (extract → JPEG
  draft-decode → resize → recompress → `replace_image`), which composes with the
  deskew transform without double-rotating. Default 110 DPI, quality 52, **full
  color on every page** (borders/design must stay consistent).
- `server/merge_core.py` — lossless pypdf merge.

**Critical constraints (do not break):**
- **The OCR/searchable text layer must always be preserved** — the whole point
  is running RAG on the output. Never rasterize pages in a way that flattens
  text.
- Deskew sign convention is verified empirically; pypdf `rotate(detected_angle)`
  corrects it (residual → 0).

**Deployment history / decisions:**
- Vercel fails (4.5 MB serverless body cap vs 14 MB files) — don't use it.
- Render deploys via the repo's `Dockerfile` + `render.yaml`, but the **free
  tier (512 MB / 0.1 CPU) OOMs → 502** on real chapters. Works only on a paid
  ≥2 GB instance.
- **Chosen solution: a standalone Windows `.exe`** (`build_exe.bat` →
  PyInstaller → `dist\DeskewPDF.exe`, ~112 MB). Runs entirely on the user's own
  machine, no server, keeps full OCR. `desktop.py` is the entry point (starts
  server, opens browser); `main.py` resolves `web/` from `sys._MEIPASS` when
  frozen. Distribute the exe by file-share.

**Not in git (regenerate, don't copy):** `.venv/`, `build/`, `dist/`, `*.spec`,
`__pycache__/`. Also the test PDF isn't in the repo.

**Everything is committed and pushed; working tree is clean.** Please start by
reading the README and confirming the app runs via `run.bat`. I may want to keep
iterating on compression/quality or the exe packaging.

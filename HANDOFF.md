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

**PRIMARY GOAL — this is the main thing to work on:** Ship this as a proper
**installable Windows `.exe`** that anyone can download and install on their own
machine, then run locally in their browser. All processing happens on the
user's machine (no server, no cost, full OCR). Right now there is a working
*portable* onefile exe (`build_exe.bat` → `dist\DeskewPDF.exe`, ~112 MB) that
runs but is not yet a polished installable product. The next work is to turn it
into a real installer and app:
- Wrap it with an installer (Inno Setup or NSIS) that installs to Program Files,
  adds Start Menu + desktop shortcuts, and an uninstaller.
- Add an app icon (currently none).
- Consider hiding the console window (windowed launch) while keeping a way to
  quit; handle the "keep this window open" UX cleanly.
- Note Windows SmartScreen will warn on an unsigned exe ("More info → Run
  anyway"); code signing is optional/out of scope unless a cert is available.
- Keep it a single downloadable artifact that a non-technical teammate can
  install with no Python and no setup.

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

**Distribution decision — the .exe is the product; cloud hosting was rejected:**
- Cloud hosting was tried and abandoned. Vercel fails (4.5 MB serverless body
  cap vs 14 MB files). Render's free tier (512 MB / 0.1 CPU) OOMs → 502 on real
  chapters and only works on a paid ≥2 GB instance. The `Dockerfile` +
  `render.yaml` are left in the repo but are NOT the path forward. **Do not
  re-suggest cloud hosting** — the deliverable is a local installable app.
- **The path forward: a standalone, installable Windows `.exe`.** Current state:
  `build_exe.bat` → PyInstaller → `dist\DeskewPDF.exe` (~112 MB), a working
  portable onefile. `desktop.py` is the entry point (picks a free port, starts
  the FastAPI server, opens the browser); `main.py` resolves `web/` from
  `sys._MEIPASS` when frozen. Next step is packaging this into a real installer
  (see PRIMARY GOAL above).

**Not in git (regenerate, don't copy):** `.venv/`, `build/`, `dist/`, `*.spec`,
`__pycache__/`. Also the test PDF isn't in the repo.

**Everything is committed and pushed; working tree is clean.** Start by
confirming the app runs via `run.bat`, then rebuild the current exe with
`build_exe.bat` to verify the baseline. Then work on the PRIMARY GOAL: turning
`dist\DeskewPDF.exe` into a proper downloadable, installable Windows app
(installer + shortcuts + icon). Propose an installer approach (Inno Setup / NSIS)
before building. Never break the OCR text layer.

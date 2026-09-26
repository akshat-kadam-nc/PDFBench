# Changelog

All notable changes to PDF Bench are recorded here. This project uses
[Semantic Versioning](https://semver.org): MAJOR.MINOR.PATCH.

The version lives in `server/version.py` (`__version__`) and is mirrored in
`installer/PDFBench.iss` (`AppVersion`). On each release: bump both, add an
entry here, rebuild, then tag the commit `vX.Y.Z`.

## [1.1.0] - 2026-09-26

### Added
- History now records the full per-page breakdown of each process job
  (deskew: parity, measured and applied angle, method; compress: per-page
  color/gray mode) plus the options used. History rows for these jobs are
  expandable to show a page-by-page table.
- App version is shown next to the title and returned from `/healthz`.

### Notes
- Only jobs run on 1.1.0 or later store the per-page detail; earlier log
  entries stay summary-only.

## [1.0.0] - 2026-09-21

### Added
- First public release: local Windows desktop app (deskew, compress, merge,
  organize pages, history log). Installable per-user via Inno Setup.

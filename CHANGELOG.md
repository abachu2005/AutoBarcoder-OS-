# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2026-05-19

### Added
- `.zenodo.json` for automatic Zenodo archival + DOI minting on every release.

## [1.0.0] - 2026-05-19

First public release suitable for general OSS distribution.

### Added
- FastAPI + modern HTML/JS web frontend (`webapp/`) with file drop-zone,
  real-time progress, interactive 96-well plate grid, JSON results, and
  TXT/PDF downloads.
- Interactive setup wizard at `bin/autobarcoder-setup` (venv + deps +
  smoke test against the bundled sample dataset).
- Bundled synthetic sample dataset in `sample_data/` for the demo button.
- `LICENSE` (MIT), `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `CITATION.cff`.
- GitHub Actions CI: pytest + ruff on Python 3.9–3.12.
- Docker image published to GHCR on every tag.
- pytest unit tests for the core clustering and extraction logic.

### Changed
- `barcodes/processing.py` now accepts `use_offset`, `expected_len`,
  `prism_export_wells`, and `progress_cb` parameters (backward-compatible).
- Tkinter GUI gained a "Use 20-nt left-flank offset" checkbox.
- `viz.py` no longer hardcodes personal `/Users/abhinavbachu/Downloads/...`
  paths; it now takes `--out-dir`.

### Removed
- `offset.py` (its monolithic duplicate-module trick is replaced by the
  `use_offset` parameter on the regular pipeline).
- Hardcoded `R1C1`/`R5C3` Prism-CSV export (now opt-in via the API).

[Unreleased]: https://github.com/abachu2005/AutoBarcoder-OS-/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/abachu2005/AutoBarcoder-OS-/releases/tag/v1.0.1
[1.0.0]: https://github.com/abachu2005/AutoBarcoder-OS-/releases/tag/v1.0.0

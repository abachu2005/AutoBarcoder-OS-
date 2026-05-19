# AutoBarcoder Web UI

A modern browser-based interface for AutoBarcoder. Upload sequencing reads, configure your plate, hit run, and explore per-well clustering results in real time.

## Quick start

From the repo root:

```bash
bash webapp/run.sh
```

This creates a virtualenv on first run, installs everything, and serves the UI at <http://127.0.0.1:8000>.

## Manual setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r webapp/requirements.txt
uvicorn webapp.backend.main:app --host 127.0.0.1 --port 8000
```

## API surface

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | HTML UI |
| GET | `/api/health` | Liveness probe |
| GET | `/api/sample` / `/api/sample/file` | Bundled demo dataset + config |
| POST | `/api/jobs` | Submit a new analysis (multipart form) |
| GET | `/api/jobs/{id}` | Status + progress |
| GET | `/api/jobs/{id}/results` | JSON results (per-well top barcodes) |
| GET | `/api/jobs/{id}/summary` | TXT summary download |
| GET | `/api/jobs/{id}/pdf` | PDF charts download |

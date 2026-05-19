"""FastAPI backend for the AutoBarcoder web UI.

Run with:

    uvicorn webapp.backend.main:app --reload --host 127.0.0.1 --port 8000

or use the convenience script ``webapp/run.sh``.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from barcodes.processing import (
    process_single_plate_for_reads,
    process_all_pairs_multiple,
)

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "webapp" / "frontend"
DATA_DIR = ROOT / "webapp" / "data" / "jobs"
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AutoBarcoder", version="1.0.0")

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _job_dir(job_id: str) -> Path:
    return DATA_DIR / job_id


def _set_status(job_id: str, **fields):
    with _jobs_lock:
        _jobs.setdefault(job_id, {}).update(fields)
        (_job_dir(job_id) / "status.json").write_text(json.dumps(_jobs[job_id], default=str))


def _run_job(job_id: str, params: dict, file_path: Path):
    job_dir = _job_dir(job_id)
    try:
        _set_status(job_id, state="running", progress=0)

        rows = [r.strip() for r in params["rows"].splitlines() if r.strip()]
        columns = [c.strip() for c in params["columns"].splitlines() if c.strip()]
        plate_ids = [p.strip() for p in params.get("plate_ids", "").splitlines() if p.strip()]
        expected_len = int(params["expected_len"])
        length_threshold = expected_len + 5
        distance_threshold = int(params["distance_threshold"])
        use_offset = bool(params.get("use_offset", False))

        out_txt = job_dir / "summary.txt"
        out_pdf = job_dir / "results.pdf"

        def progress_cb(done, total):
            _set_status(job_id, state="running", progress=int(100 * done / max(total, 1)))

        if plate_ids:
            results = process_all_pairs_multiple(
                str(out_txt), str(out_pdf), str(file_path),
                params["start_text"], params["end_text"],
                length_threshold, distance_threshold,
                plate_ids, rows, columns,
                use_offset=use_offset, expected_len=expected_len,
                progress_cb=progress_cb,
            )
        else:
            with open(file_path) as fin:
                results = process_single_plate_for_reads(
                    str(out_txt), str(out_pdf), fin.readlines(),
                    params["start_text"], params["end_text"],
                    length_threshold, distance_threshold,
                    rows, columns,
                    use_offset=use_offset, expected_len=expected_len,
                    progress_cb=progress_cb,
                )

        (job_dir / "results.json").write_text(json.dumps(results, default=str))
        _set_status(job_id, state="done", progress=100)
    except Exception as e:
        _set_status(job_id, state="error", error=str(e))


@app.get("/", response_class=HTMLResponse)
def index():
    idx = FRONTEND_DIR / "index.html"
    if not idx.exists():
        return HTMLResponse("<h1>Frontend missing</h1>", status_code=500)
    return HTMLResponse(idx.read_text())


@app.get("/api/health")
def health():
    return {"ok": True, "version": app.version}


@app.get("/api/sample")
def sample_dataset():
    """Return contents of the bundled sample dataset for the demo button."""
    sample = ROOT / "sample_data" / "sample_reads.txt"
    meta = ROOT / "sample_data" / "sample_config.json"
    if not (sample.exists() and meta.exists()):
        raise HTTPException(404, "Sample dataset not available")
    return JSONResponse({
        "filename": sample.name,
        "config": json.loads(meta.read_text()),
    })


@app.get("/api/sample/file")
def sample_file():
    sample = ROOT / "sample_data" / "sample_reads.txt"
    if not sample.exists():
        raise HTTPException(404, "Sample file not found")
    return FileResponse(str(sample), media_type="text/plain", filename=sample.name)


@app.post("/api/jobs")
async def create_job(
    sequencing_file: UploadFile = File(...),
    rows: str = Form(...),
    columns: str = Form(...),
    start_text: str = Form(...),
    end_text: str = Form(...),
    expected_len: int = Form(...),
    distance_threshold: int = Form(2),
    use_offset: bool = Form(False),
    plate_ids: str = Form(""),
):
    job_id = uuid.uuid4().hex[:12]
    job_dir = _job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    file_path = job_dir / sequencing_file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(sequencing_file.file, f)

    params = dict(
        rows=rows, columns=columns,
        start_text=start_text, end_text=end_text,
        expected_len=expected_len, distance_threshold=distance_threshold,
        use_offset=use_offset, plate_ids=plate_ids,
    )
    _set_status(job_id, id=job_id, state="queued", progress=0, params=params,
                filename=sequencing_file.filename)
    threading.Thread(target=_run_job, args=(job_id, params, file_path), daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    with _jobs_lock:
        if job_id not in _jobs:
            status_file = _job_dir(job_id) / "status.json"
            if status_file.exists():
                return json.loads(status_file.read_text())
            raise HTTPException(404, "Unknown job")
        return _jobs[job_id]


@app.get("/api/jobs/{job_id}/results")
def job_results(job_id: str):
    rf = _job_dir(job_id) / "results.json"
    if not rf.exists():
        raise HTTPException(404, "Results not ready")
    return JSONResponse(json.loads(rf.read_text()))


@app.get("/api/jobs/{job_id}/summary")
def job_summary(job_id: str):
    f = _job_dir(job_id) / "summary.txt"
    if not f.exists():
        raise HTTPException(404, "Summary not ready")
    return FileResponse(str(f), media_type="text/plain", filename=f"{job_id}_summary.txt")


@app.get("/api/jobs/{job_id}/pdf")
def job_pdf(job_id: str):
    f = _job_dir(job_id) / "results.pdf"
    if not f.exists():
        raise HTTPException(404, "PDF not ready")
    return FileResponse(str(f), media_type="application/pdf", filename=f"{job_id}_results.pdf")


def main():
    import uvicorn
    uvicorn.run("webapp.backend.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()

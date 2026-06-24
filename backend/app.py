from __future__ import annotations

import io
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend import crud, models, schemas  # noqa: E402
from backend.database import DB_PATH, UPLOAD_DIR, SessionLocal, init_db  # noqa: E402
from backend.predictor import predictor  # noqa: E402
from well_common import load_and_clean_well  # noqa: E402

FRONTEND_FILE = BASE_DIR / "frontend" / "index.html"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist" / "index.html"
MODEL_NAME = "WellLog-LSTM"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _dt(value):
    return value.isoformat() if value else None


def serialize_prediction(pred: models.Prediction, well_name: str | None = None) -> dict:
    import json

    return {
        "id": pred.id,
        "well_id": pred.well_id,
        "well_name": well_name or (pred.well.name if pred.well else ""),
        "import_id": pred.import_id,
        "model_name": pred.model_name,
        "metrics": json.loads(pred.metrics_json),
        "depth": json.loads(pred.depth_json),
        "y_true": json.loads(pred.y_true_json),
        "y_pred": json.loads(pred.y_pred_json),
        "created_at": _dt(pred.created_at),
    }


def serialize_import(record: models.WellImport) -> dict:
    return {
        "id": record.id,
        "well_id": record.well_id,
        "original_name": record.original_name,
        "stored_path": record.stored_path,
        "row_count": record.row_count,
        "created_at": _dt(record.created_at),
    }


def serialize_well(well: models.Well) -> dict:
    latest_import = max(well.imports, key=lambda item: item.id, default=None)
    latest_prediction = max(well.predictions, key=lambda item: item.id, default=None)
    return {
        "id": well.id,
        "name": well.name,
        "location": well.location,
        "remark": well.remark,
        "created_at": _dt(well.created_at),
        "updated_at": _dt(well.updated_at),
        "import_count": len(well.imports),
        "prediction_count": len(well.predictions),
        "last_import_at": _dt(latest_import.created_at) if latest_import else None,
        "last_prediction_at": _dt(latest_prediction.created_at) if latest_prediction else None,
    }


def _safe_filename(name: str) -> str:
    base = Path(name).name.replace(" ", "_")
    return "".join(ch for ch in base if ch.isalnum() or ch in "._-")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="WellLog LSTM Admin", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    if FRONTEND_DIST.exists():
        return FileResponse(FRONTEND_DIST)
    return {
        "message": "Vue frontend is expected to run from frontend/ with Vite.",
        "hint": "cd frontend && npm install && npm run dev",
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "database": str(DB_PATH),
        "model_ready": predictor.ready,
    }


@app.get("/api/summary")
def summary(db: Session = Depends(get_db)):
    return crud.dashboard_summary(db)


@app.get("/api/wells")
def list_wells(db: Session = Depends(get_db)):
    return [serialize_well(well) for well in crud.list_wells(db)]


@app.post("/api/wells")
def create_well(payload: schemas.WellCreate, db: Session = Depends(get_db)):
    existed = db.query(models.Well).filter(models.Well.name == payload.name).first()
    if existed:
        raise HTTPException(status_code=400, detail="Well name already exists.")
    well = crud.create_well(db, payload)
    return serialize_well(well)


@app.get("/api/wells/{well_id}")
def get_well(well_id: int, db: Session = Depends(get_db)):
    well = crud.get_well(db, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found.")
    return serialize_well(well)


@app.put("/api/wells/{well_id}")
def update_well(well_id: int, payload: schemas.WellUpdate, db: Session = Depends(get_db)):
    well = crud.get_well(db, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found.")
    if payload.name and payload.name != well.name:
        existed = db.query(models.Well).filter(models.Well.name == payload.name).first()
        if existed:
            raise HTTPException(status_code=400, detail="Well name already exists.")
    return serialize_well(crud.update_well(db, well, payload))


@app.delete("/api/wells/{well_id}")
def delete_well(well_id: int, db: Session = Depends(get_db)):
    well = crud.get_well(db, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found.")
    for record in well.imports:
        path = Path(record.stored_path)
        if path.exists():
            path.unlink()
    crud.delete_well(db, well)
    return {"ok": True}


@app.get("/api/wells/{well_id}/imports")
def list_imports(well_id: int, db: Session = Depends(get_db)):
    if not crud.get_well(db, well_id):
        raise HTTPException(status_code=404, detail="Well not found.")
    return [serialize_import(item) for item in crud.list_imports(db, well_id)]


@app.post("/api/wells/{well_id}/imports")
async def import_csv(
    well_id: int,
    file: Annotated[UploadFile, File(...)],
    db: Session = Depends(get_db),
):
    well = crud.get_well(db, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found.")
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    stored_name = f"well_{well_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex}_{_safe_filename(file.filename)}"
    stored_path = UPLOAD_DIR / stored_name
    stored_path.write_bytes(content)

    try:
        df_raw = load_and_clean_well(io.BytesIO(content))
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"CSV parse failed: {exc}") from exc

    record = crud.create_import(
        db,
        well_id=well_id,
        original_name=file.filename,
        stored_path=str(stored_path.resolve()),
        row_count=int(len(df_raw)),
    )
    return serialize_import(record)


@app.get("/api/wells/{well_id}/predictions")
def list_well_predictions(well_id: int, db: Session = Depends(get_db)):
    well = crud.get_well(db, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found.")
    return [serialize_prediction(item, well_name=well.name) for item in crud.list_predictions(db, well_id)]


@app.post("/api/wells/{well_id}/predict")
def predict_well(
    well_id: int,
    import_id: int | None = None,
    db: Session = Depends(get_db),
):
    well = crud.get_well(db, well_id)
    if not well:
        raise HTTPException(status_code=404, detail="Well not found.")

    import_record = None
    if import_id is not None:
        import_record = db.query(models.WellImport).filter(models.WellImport.id == import_id).first()
        if not import_record or import_record.well_id != well_id:
            raise HTTPException(status_code=404, detail="Import record not found.")
    else:
        import_record = crud.latest_import(db, well_id)

    if not import_record:
        raise HTTPException(status_code=400, detail="Please import a CSV file first.")
    if not Path(import_record.stored_path).exists():
        raise HTTPException(status_code=404, detail="Stored CSV file not found on disk.")

    try:
        result = predictor.predict_file(import_record.stored_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    record = crud.create_prediction(
        db,
        well_id=well_id,
        import_id=import_record.id,
        model_name=MODEL_NAME,
        result=result,
    )
    payload = serialize_prediction(record, well_name=well.name)
    payload["source_import"] = serialize_import(import_record)
    return payload


@app.get("/api/predictions")
def list_predictions(db: Session = Depends(get_db), well_id: int | None = None):
    items = crud.list_predictions(db, well_id=well_id)
    return [serialize_prediction(item) for item in items]


@app.get("/api/predictions/{prediction_id}")
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    item = crud.get_prediction(db, prediction_id)
    if not item:
        raise HTTPException(status_code=404, detail="Prediction not found.")
    well = crud.get_well(db, item.well_id)
    return serialize_prediction(item, well_name=well.name if well else "")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)

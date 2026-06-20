from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from . import models, schemas


def utc_now() -> datetime:
    return datetime.utcnow()


def create_well(db: Session, well_in: schemas.WellCreate) -> models.Well:
    now = utc_now()
    well = models.Well(
        name=well_in.name,
        location=well_in.location,
        remark=well_in.remark,
        created_at=now,
        updated_at=now,
    )
    db.add(well)
    db.commit()
    db.refresh(well)
    return well


def list_wells(db: Session) -> list[models.Well]:
    return db.query(models.Well).order_by(models.Well.id.desc()).all()


def get_well(db: Session, well_id: int) -> models.Well | None:
    return db.query(models.Well).filter(models.Well.id == well_id).first()


def update_well(db: Session, well: models.Well, well_in: schemas.WellUpdate) -> models.Well:
    if well_in.name is not None:
        well.name = well_in.name
    if well_in.location is not None:
        well.location = well_in.location
    if well_in.remark is not None:
        well.remark = well_in.remark
    well.updated_at = utc_now()
    db.commit()
    db.refresh(well)
    return well


def delete_well(db: Session, well: models.Well) -> None:
    db.delete(well)
    db.commit()


def create_import(
    db: Session,
    well_id: int,
    original_name: str,
    stored_path: str,
    row_count: int,
) -> models.WellImport:
    record = models.WellImport(
        well_id=well_id,
        original_name=original_name,
        stored_path=stored_path,
        row_count=row_count,
        created_at=utc_now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_imports(db: Session, well_id: int) -> list[models.WellImport]:
    return (
        db.query(models.WellImport)
        .filter(models.WellImport.well_id == well_id)
        .order_by(models.WellImport.id.desc())
        .all()
    )


def latest_import(db: Session, well_id: int) -> models.WellImport | None:
    return (
        db.query(models.WellImport)
        .filter(models.WellImport.well_id == well_id)
        .order_by(models.WellImport.id.desc())
        .first()
    )


def create_prediction(
    db: Session,
    well_id: int,
    import_id: int | None,
    model_name: str,
    result: dict,
) -> models.Prediction:
    record = models.Prediction(
        well_id=well_id,
        import_id=import_id,
        model_name=model_name,
        metrics_json=json.dumps(result["metrics"], ensure_ascii=False),
        depth_json=json.dumps(result["depth"], ensure_ascii=False),
        y_true_json=json.dumps(result["y_true"], ensure_ascii=False),
        y_pred_json=json.dumps(result["y_pred"], ensure_ascii=False),
        created_at=utc_now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_predictions(db: Session, well_id: int | None = None) -> list[models.Prediction]:
    query = db.query(models.Prediction).order_by(models.Prediction.id.desc())
    if well_id is not None:
        query = query.filter(models.Prediction.well_id == well_id)
    return query.all()


def get_prediction(db: Session, prediction_id: int) -> models.Prediction | None:
    return db.query(models.Prediction).filter(models.Prediction.id == prediction_id).first()


def dashboard_summary(db: Session) -> dict:
    latest = db.query(models.Prediction).order_by(models.Prediction.id.desc()).first()
    latest_payload = None
    if latest:
        well = db.query(models.Well).filter(models.Well.id == latest.well_id).first()
        latest_payload = {
            "id": latest.id,
            "well_id": latest.well_id,
            "well_name": well.name if well else "",
            "created_at": latest.created_at.isoformat(),
            "metrics": json.loads(latest.metrics_json),
        }

    return {
        "wells": db.query(models.Well).count(),
        "imports": db.query(models.WellImport).count(),
        "predictions": db.query(models.Prediction).count(),
        "latest_prediction": latest_payload,
    }


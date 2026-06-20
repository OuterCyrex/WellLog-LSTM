from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Well(Base):
    __tablename__ = "wells"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    imports: Mapped[list["WellImport"]] = relationship(back_populates="well", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="well", cascade="all, delete-orphan")


class WellImport(Base):
    __tablename__ = "well_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    well_id: Mapped[int] = mapped_column(ForeignKey("wells.id"), nullable=False, index=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    well: Mapped[Well] = relationship(back_populates="imports")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    well_id: Mapped[int] = mapped_column(ForeignKey("wells.id"), nullable=False, index=True)
    import_id: Mapped[int | None] = mapped_column(ForeignKey("well_imports.id"), nullable=True, index=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    depth_json: Mapped[str] = mapped_column(Text, nullable=False)
    y_true_json: Mapped[str] = mapped_column(Text, nullable=False)
    y_pred_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    well: Mapped[Well] = relationship(back_populates="predictions")

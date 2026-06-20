from __future__ import annotations

from pydantic import BaseModel


class WellCreate(BaseModel):
    name: str
    location: str | None = None
    remark: str | None = None


class WellUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    remark: str | None = None


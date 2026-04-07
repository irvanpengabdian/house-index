"""Response schemas for house index analysis (aligned with PRD output)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ConditionCode = Literal["C1", "C2", "C3", "C4", "C5", "C6"]
MaterialCategory = Literal["LAYAK", "TIDAK_LAYAK"]


class MaterialElement(BaseModel):
    """Assessment for one structural element (roof / wall / floor)."""

    model_config = ConfigDict(extra="ignore")

    terlihat: bool = Field(default=False, description="Whether this element is visible in the photo")
    kategori: MaterialCategory | None = None
    kondisi: ConditionCode | None = None


class MaterialsBlock(BaseModel):
    model_config = ConfigDict(extra="ignore")

    atap: MaterialElement | None = None
    dinding: MaterialElement | None = None
    lantai: MaterialElement | None = None


class WealthProxies(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ac_outdoor_terdeteksi: bool = False
    garasi_atau_parkir_tertutup: bool = False
    plafon_interior_mewah: bool = False
    furnitur_berkualitas: bool = False
    estimasi_luas_ruang: str | None = None


class HouseIndexAnalysis(BaseModel):
    """Structured JSON returned to Simaster after vision + validation."""

    model_config = ConfigDict(extra="ignore")

    student_id: str = Field(description="Echo of request student identifier")
    house_index_score: float = Field(
        description="1.0–5.0 scale, or -1 if image is not a valid house photo"
    )
    confidence_level: float = Field(ge=0.0, le=1.0)
    materials: MaterialsBlock = Field(default_factory=MaterialsBlock)
    wealth_proxies: WealthProxies = Field(default_factory=WealthProxies)
    verification_notes: str | None = None

    @field_validator("house_index_score")
    @classmethod
    def score_range(cls, v: float | int) -> float:
        x = float(v)
        if x == -1.0:
            return -1.0
        if 1.0 <= x <= 5.0:
            return x
        raise ValueError("house_index_score must be in [1.0, 5.0] or -1 for invalid")

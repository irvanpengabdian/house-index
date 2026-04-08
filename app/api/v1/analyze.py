"""House photo analysis endpoint for Simaster."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.auth import SimasterAuthDep
from app.core.rate_limit import rate_limit_analyze
from app.models.house_index import HouseIndexAnalysis
from app.services.analysis import analyze_house_photos

router = APIRouter(
    dependencies=[SimasterAuthDep, Depends(rate_limit_analyze)],
)


@router.post(
    "/analyze",
    response_model=HouseIndexAnalysis,
    summary="Analisis indeks rumah dari foto",
    description=(
        "Menerima `student_id` dan satu atau beberapa file gambar (multipart, field **files**). "
        "Semua foto dianggap satu rumah yang sama; hasilnya satu JSON indeks. "
        "Default: 1–5 foto per mahasiswa (atur lewat MIN_IMAGES_PER_REQUEST / MAX_IMAGES_PER_REQUEST)."
    ),
)
async def analyze_house_index(
    student_id: str = Form(..., description="ID mahasiswa di Simaster"),
    files: list[UploadFile] = File(
        ...,
        description="Foto rumah (JPEG, PNG, atau WebP). Ulangi field `files` untuk beberapa foto.",
    ),
) -> HouseIndexAnalysis:
    return await analyze_house_photos(student_id=student_id, files=files)

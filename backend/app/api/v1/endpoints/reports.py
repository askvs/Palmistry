"""Reading report endpoints (FR-057, FR-058, FR-062, FR-063)."""
from __future__ import annotations

import re
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.rbac import get_optional_current_user
from app.db.session import get_db
from app.models.reading import Reading
from app.models.user import User
from app.services.reading.service import ReadingNotFound
from app.services.reports.generator import build_reading_report
from app.services.reports.pdf_exporter import export_report_to_pdf
from app.services.reports.excel_exporter import export_report_to_excel

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_verified_reading(db: Session, reading_id: uuid.UUID, user: User | None) -> Reading:
    reading = db.get(Reading, reading_id)
    if reading is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "READING_NOT_FOUND", "message": "Reading not found", "request_id": ""},
        )
    # Check access permission if reading belongs to a specific user
    if reading.user_id is not None:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "UNAUTHORIZED", "message": "Authentication required to access this report", "request_id": ""},
            )
        is_owner = user.id == reading.user_id
        is_staff = getattr(user.role, "value", str(user.role)) in ("tarot_reader", "spiritual_consultant", "admin")
        if not (is_owner or is_staff):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "You do not have access to this report", "request_id": ""},
            )
    return reading


def _slugify(text: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", str(text or ""))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", ascii_text).strip().lower()
    return re.sub(r"[-\s]+", "-", s) or "report"


def _download_headers(filename: str, report_id: str) -> Dict[str, str]:
    # RFC 5987: ascii fallback + utf-8 filename* for international titles.
    safe = filename.replace('"', "")
    return {
        "Content-Disposition": f'attachment; filename="{safe}"; filename*=UTF-8\'\'{safe}',
        "Cache-Control": "no-store",
        "X-Report-ID": report_id,
    }


@router.get("/reading/{reading_id}", summary="Get structured reading report (FR-057, FR-058)")
def get_reading_report(
    reading_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    reading = _get_verified_reading(db, reading_id, user)
    return build_reading_report(reading, user)


@router.get("/reading/{reading_id}/pdf", summary="Export reading report as PDF (FR-062)")
def download_reading_pdf(
    reading_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
):
    import io as _io

    reading = _get_verified_reading(db, reading_id, user)
    report = build_reading_report(reading, user)
    pdf_bytes = export_report_to_pdf(report)
    filename = f"{_slugify(reading.title)}-{reading_id.hex[:8]}.pdf"

    return StreamingResponse(
        _io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            **_download_headers(filename, str(report.get("report_id", ""))),
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.get("/reading/{reading_id}/excel", summary="Export reading report as Excel (FR-063)")
def download_reading_excel(
    reading_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
):
    import io as _io

    reading = _get_verified_reading(db, reading_id, user)
    report = build_reading_report(reading, user)
    excel_bytes = export_report_to_excel(report)
    filename = f"{_slugify(reading.title)}-{reading_id.hex[:8]}.xlsx"

    return StreamingResponse(
        _io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            **_download_headers(filename, str(report.get("report_id", ""))),
            "Content-Length": str(len(excel_bytes)),
        },
    )

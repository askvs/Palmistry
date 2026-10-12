"""Life trend analysis endpoints (FR-017)."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.rbac import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.life_trends import LifeTrendOut
from app.services.life_trends import generate_life_trends

router = APIRouter()


@router.get("/life-trends", response_model=LifeTrendOut)
async def get_life_trends(
    db=Depends(get_db),
    user=Depends(get_current_user),
):
    """Generate life trend analysis for the authenticated user."""
    result = generate_life_trends(db, user)
    return LifeTrendOut(**result)
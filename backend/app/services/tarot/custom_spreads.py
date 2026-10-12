"""Reader-authored tarot spreads."""
from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.custom_spread import CustomSpread, SpreadVisibility
from app.models.user import User


class CustomSpreadError(Exception):
    code = "CUSTOM_SPREAD_ERROR"
    status_code = 400

    def __init__(self, message: str = "Custom spread operation failed"):
        self.message = message
        super().__init__(message)


class SpreadNotFound(CustomSpreadError):
    code = "SPREAD_NOT_FOUND"
    status_code = 404


class SpreadNameTaken(CustomSpreadError):
    code = "SPREAD_NAME_TAKEN"
    status_code = 409


class SpreadNotAllowed(CustomSpreadError):
    code = "SPREAD_NOT_ALLOWED"
    status_code = 403


MIN_POSITIONS = 1
MAX_POSITIONS = 10
MAX_NAME_LENGTH = 120


def normalise_positions(positions) -> list[dict]:
    """Validate and normalise an authoring payload into stored position dicts."""
    if not isinstance(positions, list) or not (
        MIN_POSITIONS <= len(positions) <= MAX_POSITIONS
    ):
        raise CustomSpreadError(
            f"A spread needs between {MIN_POSITIONS} and {MAX_POSITIONS} card positions"
        )

    normalised: list[dict] = []
    for index, entry in enumerate(positions, start=1):
        if not isinstance(entry, dict):
            raise CustomSpreadError(f"Position {index} must be an object")
        name = str(entry.get("name") or "").strip()
        if not name:
            raise CustomSpreadError(f"Position {index} needs a name")
        if len(name) > 80:
            raise CustomSpreadError("A position name may be at most 80 characters")
        description = str(entry.get("description") or "").strip()
        normalised.append(
            {
                "position": index,
                "name": name,
                "description": description[:500],
            }
        )
    return normalised


def list_for_reader(db: Session, user: User, *, include_shared: bool = True) -> list[CustomSpread]:
    """The reader's own spreads, plus shared spreads from other readers."""
    conditions = [CustomSpread.is_active.is_(True)]
    if include_shared:
        conditions.append(
            or_(
                CustomSpread.owner_id == user.id,
                CustomSpread.visibility == SpreadVisibility.shared,
            )
        )
    else:
        conditions.append(CustomSpread.owner_id == user.id)
    return list(
        db.scalars(
            select(CustomSpread)
            .where(*conditions)
            .order_by(CustomSpread.created_at.desc())
        ).all()
    )


def create(db: Session, user: User, *, data: dict) -> CustomSpread:
    name = (data.get("name") or "").strip()
    if not name:
        raise CustomSpreadError("A spread needs a name")
    if len(name) > MAX_NAME_LENGTH:
        raise CustomSpreadError("A spread name may be at most 120 characters")

    _assert_name_available(db, user, name)

    positions = normalise_positions(data.get("positions"))
    visibility = _parse_visibility(data.get("visibility"))

    spread = CustomSpread(
        owner_id=user.id,
        name=name,
        description=(data.get("description") or "").strip()[:2000] or None,
        category=(data.get("category") or "custom").strip()[:60] or "custom",
        positions=positions,
        card_count=len(positions),
        visibility=visibility,
    )
    db.add(spread)
    db.commit()
    db.refresh(spread)
    return spread


def update(db: Session, user: User, spread_id: uuid.UUID, *, data: dict) -> CustomSpread:
    spread = get_owned(db, user, spread_id)

    if "name" in data and data["name"] is not None:
        name = str(data["name"]).strip()
        if not name:
            raise CustomSpreadError("A spread needs a name")
        if name != spread.name:
            _assert_name_available(db, user, name)
        spread.name = name[:MAX_NAME_LENGTH]

    if "description" in data:
        spread.description = (data.get("description") or "").strip()[:2000] or None

    if data.get("category"):
        spread.category = str(data["category"]).strip()[:60]

    if data.get("visibility") is not None:
        spread.visibility = _parse_visibility(data.get("visibility"))

    if data.get("positions") is not None:
        positions = normalise_positions(data["positions"])
        spread.positions = positions
        spread.card_count = len(positions)

    db.commit()
    db.refresh(spread)
    return spread


def deactivate(db: Session, user: User, spread_id: uuid.UUID) -> None:
    spread = get_owned(db, user, spread_id)
    spread.is_active = False
    db.commit()


def get_owned(db: Session, user: User, spread_id: uuid.UUID) -> CustomSpread:
    spread = db.get(CustomSpread, spread_id)
    if spread is None or not spread.is_active:
        raise SpreadNotFound("Custom spread not found")
    if spread.owner_id != user.id:
        raise SpreadNotFound("Custom spread not found")
    return spread


def resolve_for_use(db: Session, user: User, spread_ref: str) -> CustomSpread | None:
    """Resolve a spread reference the caller may run a reading with."""
    try:
        parsed = uuid.UUID(str(spread_ref))
    except (ValueError, AttributeError, TypeError):
        return None
    spread = db.get(CustomSpread, parsed)
    if spread is None or not spread.is_active:
        return None
    if spread.owner_id != user.id and spread.visibility != SpreadVisibility.shared:
        raise SpreadNotAllowed("You do not have access to this spread")
    return spread


def to_definition(spread: CustomSpread) -> dict:
    """Convert a stored spread into the engine's spread-definition shape."""
    return {
        "id": str(spread.id),
        "name": spread.name,
        "spec_requirement": None,
        "card_count": spread.card_count,
        "category": spread.category,
        "description": spread.description or f"{spread.card_count}-card custom spread.",
        "positions": [
            {
                "position": index + 1,
                "name": position["name"],
                "description": position.get("description") or "",
            }
            for index, position in enumerate(spread.positions or [])
        ],
        "interpretation_order": list(range(1, len(spread.positions or []) + 1)),
    }


def _parse_visibility(value) -> SpreadVisibility:
    """Coerce a payload value into SpreadVisibility, defaulting to private."""
    if value is None or value == "":
        return SpreadVisibility.private
    try:
        return SpreadVisibility(str(value))
    except ValueError as exc:
        raise CustomSpreadError(
            f"visibility must be one of {[v.value for v in SpreadVisibility]}"
        ) from exc


def _assert_name_available(db: Session, user: User, name: str) -> None:
    existing = db.scalar(
        select(CustomSpread).where(
            CustomSpread.owner_id == user.id,
            CustomSpread.name == name,
        )
    )
    if existing is not None:
        raise SpreadNameTaken("You already have a spread with that name")

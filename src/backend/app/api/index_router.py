"""Real Index (business/core/index) HTTP surface (2026-08-29, Preferred
Indexes picker) -- IndexManager existed Manager-level only until now
(see the 2026-08-28 MEMORY.md entry: "no api/index_router.py/HTTP
surface yet ... a real, disclosed, separate future scope"). List-only,
same "thin wrapper, one business call, return the real dataclass list"
convention as sections_router.py's own `GET /sections`."""
from __future__ import annotations

from fastapi import APIRouter

from app.business.core.index.index import Index
from app.business.core.index.index_manager import IndexManager

router = APIRouter(prefix="")
_index_manager = IndexManager()


@router.get("/indexes")
def list_indexes() -> list[Index]:
    return _index_manager.get_all()

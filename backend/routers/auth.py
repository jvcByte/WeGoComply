from __future__ import annotations

from fastapi import APIRouter, Depends

from core.security import get_current_user
from schemas.security import AuthenticatedUser

router = APIRouter()


@router.get("/me", response_model=AuthenticatedUser)
def get_authenticated_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    return current_user

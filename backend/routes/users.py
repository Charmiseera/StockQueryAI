"""
routes/users.py — Authenticated user profile endpoints.
"""

from fastapi import APIRouter
from auth.dependencies import CurrentUser

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(current_user: CurrentUser):
    """Return basic profile info for the authenticated user."""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
    }

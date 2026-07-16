"""
Multi-tenancy: resolves which company the authenticated user belongs to.

Every /api/* route should depend on get_current_company_id instead of
(or in addition to) require_auth — it already implies require_auth ran,
since it needs the verified user id from the token.

Invite-only model: there's no self-serve signup, so a user with no
company_members row is a real error (they were never onboarded), not
a "create a default company" situation.
"""

from fastapi import Depends, HTTPException

from auth import require_auth
from db import supabase


def get_current_company_id(claims: dict = Depends(require_auth)) -> str:
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject")

    response = (
        supabase.table("company_members")
        .select("company_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=403,
            detail="This account isn't linked to a company yet.",
        )

    return response.data[0]["company_id"]

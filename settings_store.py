"""
Reads/writes a company's settings row. One row per company now (see
multi_tenant_schema.sql) — company_id is the primary key.
"""

from db import supabase

DEFAULT_ESTIMATION_PROMPT = """List your common jobs and how long each usually takes your team. \
Be specific — the more detail you give, the better the AI can tell a routine job \
from one that needs an in-person look first.

For each job type, include:
- What the job is (be specific — "kitchen faucet replacement" not just "faucet work")
- How long it typically takes your team
- Anything that changes the time a lot (older homes, hard-to-reach areas, etc.)

Example:
- Ceiling fan installation (existing wiring already in place): 90 minutes
- Ceiling fan installation (no existing fixture, needs new wiring): usually needs \
an in-person estimate first, can range 2-5 hours
- Kitchen faucet replacement: 60-90 minutes
- Toilet unclogging: 30-45 minutes
- Toilet replacement (same location, no plumbing changes): 2 hours
- Drywall patch, small (under 1 sq ft): 45 minutes
- Drywall patch, large or multiple: usually needs an in-person estimate

If a job could vary a lot depending on things you can't tell from a phone \
description (what's actually causing the problem, what's behind a wall, \
what parts are needed), say so — tell the AI it's OK to book those as a \
short in-person visit first instead of guessing."""

DEFAULTS = {
    "business_hours_start": 8,
    "business_hours_end": 17,
    "estimation_prompt": DEFAULT_ESTIMATION_PROMPT,
}



def get_settings(company_id: str) -> dict:
    response = (
        supabase.table("settings")
        .select("*")
        .eq("company_id", company_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        return {**DEFAULTS, "company_id": company_id}
    return response.data[0]


def update_settings(company_id: str, fields: dict) -> dict:
    allowed = {"business_hours_start", "business_hours_end", "estimation_prompt"}
    payload = {k: v for k, v in fields.items() if k in allowed}

    response = (
        supabase.table("settings")
        .update(payload)
        .eq("company_id", company_id)
        .execute()
    )
    return response.data[0] if response.data else get_settings(company_id)


def get_company(company_id: str) -> dict:
    response = (
        supabase.table("companies")
        .select("*")
        .eq("id", company_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else {"id": company_id, "name": "", "phone_number": "", "address": ""}


def update_company(company_id: str, fields: dict) -> dict:
    allowed = {"name", "phone_number", "address"}
    payload = {k: v for k, v in fields.items() if k in allowed}

    response = (
        supabase.table("companies")
        .update(payload)
        .eq("id", company_id)
        .execute()
    )
    return response.data[0] if response.data else get_company(company_id)


def get_company_by_vapi_phone_id(phone_number_id: str) -> dict | None:
    """Used by the Vapi webhook to figure out which company a call is for."""
    response = (
        supabase.table("companies")
        .select("*")
        .eq("vapi_phone_number_id", phone_number_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None

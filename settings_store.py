"""
Reads/writes a company's settings row. One row per company now (see
multi_tenant_schema.sql) — company_id is the primary key.
"""

from db import supabase

DEFAULTS = {
    "business_hours_start": 8,
    "business_hours_end": 17,
    "estimation_prompt": "",
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

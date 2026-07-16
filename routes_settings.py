"""
Settings REST router — now company-scoped. Keeps the same flat response
shape the frontend already expects (business_name, phone_number, address,
business_hours_start, business_hours_end, estimation_prompt), even though
that data now lives across two tables (companies + settings) internally.
Nothing on the frontend needed to change because of that split.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from tenant import get_current_company_id
from settings_store import get_settings, update_settings, get_company, update_company

router = APIRouter()


class SettingsUpdate(BaseModel):
    business_name: str | None = None
    phone_number: str | None = None
    address: str | None = None
    business_hours_start: int | None = None
    business_hours_end: int | None = None
    estimation_prompt: str | None = None


@router.get("/settings")
async def read_settings(company_id: str = Depends(get_current_company_id)):
    company = get_company(company_id)
    settings = get_settings(company_id)
    return {
        "business_name": company["name"],
        "phone_number": company["phone_number"],
        "address": company["address"],
        "business_hours_start": settings["business_hours_start"],
        "business_hours_end": settings["business_hours_end"],
        "estimation_prompt": settings["estimation_prompt"],
    }


@router.put("/settings")
async def write_settings(
    body: SettingsUpdate, company_id: str = Depends(get_current_company_id)
):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}

    company_fields = {
        k: v for k, v in fields.items() if k in {"business_name", "phone_number", "address"}
    }
    settings_fields = {
        k: v for k, v in fields.items()
        if k in {"business_hours_start", "business_hours_end", "estimation_prompt"}
    }

    if company_fields:
        # company_fields uses "business_name" but the companies table column is "name"
        if "business_name" in company_fields:
            company_fields["name"] = company_fields.pop("business_name")
        update_company(company_id, company_fields)

    if settings_fields:
        update_settings(company_id, settings_fields)

    return await read_settings(company_id)

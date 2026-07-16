"""
Dashboard-facing REST endpoints — now company-scoped.

Every route depends on get_current_company_id (tenant.py), which itself
depends on require_auth (auth.py). A request with a valid JWT but no
company_members row gets a 403, not an empty result — that distinction
matters for debugging ("no data" vs "not onboarded" look identical
otherwise).

Customers are still derived from jobs (no customers table), same as
before — just filtered to one company's jobs now instead of all of them.
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from db import supabase
from tenant import get_current_company_id

router = APIRouter()


# ---------------------------------------------------
# Helpers
# ---------------------------------------------------

STATUS_MAP = {
    "booked": "scheduled",
    "scheduled": "scheduled",
    "in_progress": "in_progress",
    "in progress": "in_progress",
    "completed": "completed",
    "done": "completed",
    "cancelled": "cancelled",
    "canceled": "cancelled",
}


def normalize_status(raw: str | None) -> str:
    if not raw:
        return "scheduled"
    return STATUS_MAP.get(raw.strip().lower(), "scheduled")


def customer_id_from_phone(phone: str | None) -> str:
    digits = re.sub(r"\D", "", phone or "")
    return digits or "unknown"


def serialize_job(row: dict) -> dict:
    return {
        "id": row["id"],
        "customer_id": customer_id_from_phone(row.get("phone_number")),
        "customer_name": row.get("customer_name"),
        "phone_number": row.get("phone_number"),
        "address": row.get("address"),
        "description": row.get("description"),
        "scheduled_start_time": row.get("scheduled_start_time"),
        "scheduled_end_time": row.get("scheduled_end_time"),
        "duration_minutes": row.get("duration_minutes"),
        "status": normalize_status(row.get("status")),
        "category": row.get("category") or "General",
        "ai_confidence": row.get("ai_confidence") or 0,
    }


def fetch_all_jobs(company_id: str) -> list[dict]:
    response = (
        supabase.table("jobs")
        .select("*")
        .eq("company_id", company_id)
        .execute()
    )
    return [serialize_job(row) for row in response.data]


# ---------------------------------------------------
# Jobs
# ---------------------------------------------------

@router.get("/jobs")
async def list_jobs(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    status: str | None = Query(default=None),
    company_id: str = Depends(get_current_company_id),
):
    jobs = fetch_all_jobs(company_id)

    if start:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        jobs = [
            j for j in jobs
            if j["scheduled_start_time"]
            and datetime.fromisoformat(j["scheduled_start_time"].replace("Z", "+00:00")) >= start_dt
        ]

    if end:
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        jobs = [
            j for j in jobs
            if j["scheduled_start_time"]
            and datetime.fromisoformat(j["scheduled_start_time"].replace("Z", "+00:00")) <= end_dt
        ]

    if status:
        jobs = [j for j in jobs if j["status"] == status]

    jobs.sort(key=lambda j: j["scheduled_start_time"] or "")
    return jobs


@router.get("/jobs/today")
async def jobs_today(company_id: str = Depends(get_current_company_id)):
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    jobs = fetch_all_jobs(company_id)
    todays = [
        j for j in jobs
        if j["scheduled_start_time"]
        and start <= datetime.fromisoformat(j["scheduled_start_time"].replace("Z", "+00:00")) < end
    ]
    todays.sort(key=lambda j: j["scheduled_start_time"])
    return todays


@router.get("/jobs/upcoming")
async def jobs_upcoming(
    days: int = Query(default=7, ge=1, le=30),
    company_id: str = Depends(get_current_company_id),
):
    now = datetime.now(timezone.utc)
    tomorrow_start = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = tomorrow_start + timedelta(days=days)

    jobs = fetch_all_jobs(company_id)
    upcoming = [
        j for j in jobs
        if j["scheduled_start_time"]
        and tomorrow_start <= datetime.fromisoformat(j["scheduled_start_time"].replace("Z", "+00:00")) < end
    ]
    upcoming.sort(key=lambda j: j["scheduled_start_time"])
    return upcoming


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, company_id: str = Depends(get_current_company_id)):
    response = (
        supabase.table("jobs")
        .select("*")
        .eq("id", job_id)
        .eq("company_id", company_id)  # prevents cross-tenant lookup by guessing an id
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_job(response.data[0])


# ---------------------------------------------------
# Calendar
# ---------------------------------------------------

@router.get("/calendar/week")
async def calendar_week(
    start: str = Query(...),
    company_id: str = Depends(get_current_company_id),
):
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(days=7)

    jobs = fetch_all_jobs(company_id)
    week_jobs = [
        j for j in jobs
        if j["scheduled_start_time"]
        and start_dt <= datetime.fromisoformat(j["scheduled_start_time"].replace("Z", "+00:00")) < end_dt
    ]
    week_jobs.sort(key=lambda j: j["scheduled_start_time"])
    return week_jobs


# ---------------------------------------------------
# Customers (derived from jobs — see module docstring)
# ---------------------------------------------------

@router.get("/customers")
async def list_customers(company_id: str = Depends(get_current_company_id)):
    jobs = fetch_all_jobs(company_id)
    grouped: dict[str, list[dict]] = defaultdict(list)

    for job in jobs:
        grouped[job["customer_id"]].append(job)

    customers = []
    for cust_id, customer_jobs in grouped.items():
        customer_jobs.sort(key=lambda j: j["scheduled_start_time"] or "")
        latest = customer_jobs[-1]
        earliest = customer_jobs[0]
        customers.append({
            "id": cust_id,
            "name": latest["customer_name"],
            "phone_number": latest["phone_number"],
            "address": latest["address"],
            "total_jobs": len(customer_jobs),
            "last_job_date": latest["scheduled_start_time"],
            "created_at": earliest["scheduled_start_time"],
        })

    customers.sort(key=lambda c: c["last_job_date"] or "", reverse=True)
    return customers


@router.get("/customers/{customer_id}")
async def get_customer(
    customer_id: str, company_id: str = Depends(get_current_company_id)
):
    jobs = [j for j in fetch_all_jobs(company_id) if j["customer_id"] == customer_id]
    if not jobs:
        raise HTTPException(status_code=404, detail="Customer not found")

    jobs.sort(key=lambda j: j["scheduled_start_time"] or "")
    latest = jobs[-1]
    earliest = jobs[0]

    return {
        "customer": {
            "id": customer_id,
            "name": latest["customer_name"],
            "phone_number": latest["phone_number"],
            "address": latest["address"],
            "total_jobs": len(jobs),
            "last_job_date": latest["scheduled_start_time"],
            "created_at": earliest["scheduled_start_time"],
        },
        "jobs": jobs,
    }

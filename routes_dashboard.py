"""
Dashboard-facing REST endpoints.

Everything in here is read-only and serves the Next.js frontend — it has
nothing to do with the Vapi webhook / tool-call flow in main.py, so it's
kept in its own router rather than bloating that file further.

Mount in main.py with:

    from routes_dashboard import router as dashboard_router
    app.include_router(dashboard_router, prefix="/api")

Status values: the booking flow (main.py) writes "Booked" to the jobs
table. The frontend expects "scheduled" | "in_progress" | "completed" |
"cancelled". normalize_status() below is the one place that translates
between them — update it here, not in the frontend, if new statuses
get introduced on the backend.

Customers: there is no customers table yet. Customers are derived by
grouping jobs on phone_number, which doubles as a stable customer id
(digits only, so it's URL-safe). This is a reasonable bridge for now;
if a real customers table gets added later, these endpoints are the
only place that needs to change — the frontend already treats
customer_id as an opaque string.
"""

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from db import supabase

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


def fetch_all_jobs() -> list[dict]:
    response = supabase.table("jobs").select("*").execute()
    return [serialize_job(row) for row in response.data]


# ---------------------------------------------------
# Jobs
# ---------------------------------------------------

@router.get("/jobs")
async def list_jobs(
    start: str | None = Query(default=None, description="ISO date, inclusive"),
    end: str | None = Query(default=None, description="ISO date, inclusive"),
    status: str | None = Query(default=None),
):
    jobs = fetch_all_jobs()

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
async def jobs_today():
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    jobs = fetch_all_jobs()
    todays = [
        j for j in jobs
        if j["scheduled_start_time"]
        and start <= datetime.fromisoformat(j["scheduled_start_time"].replace("Z", "+00:00")) < end
    ]
    todays.sort(key=lambda j: j["scheduled_start_time"])
    return todays


@router.get("/jobs/upcoming")
async def jobs_upcoming(days: int = Query(default=7, ge=1, le=30)):
    now = datetime.now(timezone.utc)
    tomorrow_start = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = tomorrow_start + timedelta(days=days)

    jobs = fetch_all_jobs()
    upcoming = [
        j for j in jobs
        if j["scheduled_start_time"]
        and tomorrow_start <= datetime.fromisoformat(j["scheduled_start_time"].replace("Z", "+00:00")) < end
    ]
    upcoming.sort(key=lambda j: j["scheduled_start_time"])
    return upcoming


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    response = (
        supabase.table("jobs").select("*").eq("id", job_id).limit(1).execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return serialize_job(response.data[0])


# ---------------------------------------------------
# Calendar
# ---------------------------------------------------

@router.get("/calendar/week")
async def calendar_week(start: str = Query(..., description="ISO date, Monday of the week")):
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(days=7)

    jobs = fetch_all_jobs()
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
async def list_customers():
    jobs = fetch_all_jobs()
    grouped: dict[str, list[dict]] = defaultdict(list)

    for job in jobs:
        grouped[job["customer_id"]].append(job)

    customers = []
    for customer_id, customer_jobs in grouped.items():
        customer_jobs.sort(key=lambda j: j["scheduled_start_time"] or "")
        latest = customer_jobs[-1]
        earliest = customer_jobs[0]
        customers.append({
            "id": customer_id,
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
async def get_customer(customer_id: str):
    jobs = [j for j in fetch_all_jobs() if j["customer_id"] == customer_id]
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

from fastapi import FastAPI, Request
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from db import supabase

app = FastAPI()

# ---------------------------------------------------
# CORS (helps when using the Vapi Test Tool)
# ---------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# Database Helpers
# ---------------------------------------------------

def book_job(job):

    return (
        supabase
        .table("jobs")
        .insert(job)
        .execute()
    )

def overlaps(candidate_start, candidate_end, booked_start, booked_end):

    print("=" * 60)

    print("candidate_start:", repr(candidate_start))
    print("candidate_end:  ", repr(candidate_end))
    print("booked_start:   ", repr(booked_start))
    print("booked_end:     ", repr(booked_end))

    print("candidate tz:", candidate_start.tzinfo)
    print("booked tz:   ", booked_start.tzinfo)

    print("candidate aware?", candidate_start.tzinfo is not None)
    print("booked aware?   ", booked_start.tzinfo is not None)

    return (
        candidate_start < booked_end
        and candidate_end > booked_start
    )

def matches_weekday(dt, weekdays):

    if not weekdays:
        return True

    return dt.isoweekday() in weekdays

def matches_time_of_day(dt, preference):

    if preference is None:
        return True

    preference = preference.lower()

    hour = dt.hour

    if preference == "any":
        return True

    if preference == "morning":
        return 8 <= hour < 12

    if preference == "afternoon":
        return 12 <= hour < 17

    if preference == "evening":
        return 17 <= hour < 21

    return True

def estimate_duration(description: str):

    description = description.lower()

    if "ceiling fan" in description:
        return 90

    if "toilet" in description:
        return 60

    if "faucet" in description:
        return 45

    if "sink" in description:
        return 60

    if "light" in description:
        return 45

    if "door" in description:
        return 30

    return 60

def search_schedule(
    start_date,
    end_date,
    duration_minutes,
    weekdays=None,
    time_of_day="any",
    max_results=5
):

    booked = get_booked_jobs()

    

    start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    print(start)
    print(start.tzinfo)
    results = []

    current_day = start.date()

    while current_day <= end.date():

        candidate = datetime.combine(
            current_day,
            datetime.min.time()
        ).replace(
            hour=8,
            tzinfo=start.tzinfo
        )

        end_of_day = candidate.replace(hour=17)

        while candidate + timedelta(minutes=duration_minutes) <= end_of_day:

            if not matches_weekday(candidate, weekdays):
                candidate += timedelta(minutes=30)
                continue

            if not matches_time_of_day(candidate, time_of_day):
                candidate += timedelta(minutes=30)
                continue

            candidate_end = candidate + timedelta(
                minutes=duration_minutes
            )

            conflict = False

            for job in booked:

                if overlaps(
                    candidate,
                    candidate_end,
                    job["start"],
                    job["end"]
                ):
                    conflict = True
                    break

            if not conflict:

                results.append(
                    candidate.isoformat()
                )

                if len(results) >= max_results:
                    return results

            candidate += timedelta(minutes=30)

        current_day += timedelta(days=1)

    return results

def get_booked_jobs():

    response = (
        supabase
        .table("jobs")
        .select("scheduled_start_time,duration_minutes")
        .execute()
    )

    booked = []

    for row in response.data:

        if row["scheduled_start_time"] is None:
            continue

        start = datetime.fromisoformat(
            row["scheduled_start_time"].replace("Z", "+00:00")
        )

        duration = row["duration_minutes"] or 60

        end = start + timedelta(minutes=duration)

        booked.append({
            "start": start,
            "end": end
        })

    return booked

    response = (
        supabase
        .table("jobs")
        .select("scheduled_start_time")
        .execute()
    )

    print("\nRETURNING TO VAPI:")
    print(json.dumps(response, indent=2))

    return [
        row["scheduled_start_time"]
        for row in response.data
        if row["scheduled_start_time"] is not None
    ]


# ---------------------------------------------------
# Tool Handler
# ---------------------------------------------------

def handle_tool(tool_name, tool_id, args):

    print("\n" + "=" * 60)
    print("Tool:", tool_name)
    print("Arguments:")
    print(json.dumps(args, indent=2))
    print("=" * 60)



    # ------------------------------------------------
    # search_schedule
    # ------------------------------------------------

    if tool_name == "search_schedule":

        slots = search_schedule(

            start_date=args["start_date"],

            end_date=args["end_date"],

            duration_minutes=args["duration_minutes"],

            weekdays=args.get("weekdays"),

            time_of_day=args.get("time_of_day", "any"),

            max_results=args.get("max_results", 5)
        )

        return {
            "results": [
                {
                    "toolCallId": tool_id,
                    "result": {
                        "available_slots": slots
                    }
                }
            ]
        }

    # ------------------------------------------------
    # book_job
    # ------------------------------------------------

    if tool_name == "book_job":

        start = datetime.fromisoformat(
            args["scheduled_time"].replace("Z", "+00:00")
        )

        duration = estimate_duration(
            args["description"]
        )

        end = start + timedelta(minutes=duration)

        jobs = (
            supabase
            .table("jobs")
            .select("scheduled_start_time, scheduled_end_time")
            .execute()
        )

        for job in jobs.data:

            if (
                job["scheduled_start_time"] is None
                or job["scheduled_end_time"] is None
            ):
                continue

            existing_start = datetime.fromisoformat(
                job["scheduled_start_time"].replace("Z", "+00:00")
            )

            existing_end = datetime.fromisoformat(
                job["scheduled_end_time"].replace("Z", "+00:00")
            )

            if start < existing_end and end > existing_start:

                return {
                    "results": [
                        {
                            "toolCallId": tool_id,
                            "result": {
                                "success": False,
                                "message": "That time overlaps an existing appointment."
                            }
                        }
                    ]
                }

        job = {

            "customer_name": args["customer_name"],
            "phone_number": args["phone_number"],
            "address": args["address"],
            "description": args["description"],

            "scheduled_start_time": start.isoformat(),
            "scheduled_end_time": end.isoformat(),

            "duration_minutes": duration,

            "status": "Booked",
            "category": "General",
            "ai_confidence": 1.0
        }

        inserted = (
            supabase
            .table("jobs")
            .insert(job)
            .execute()
        )

        return {
            "results": [
                {
                    "toolCallId": tool_id,
                    "result": {
                        "success": True,
                        "job": inserted.data[0]
                    }
                }
            ],
            "endCall": True
        }
    
    
    # ------------------------------------------------
    # estimate_duration
    # ------------------------------------------------

    if tool_name == "estimate_duration":

        duration = estimate_duration(
            args.get("description", "")
        )

        return {
            "results": [
                {
                    "toolCallId": tool_id,
                    "result": {
                        "duration_minutes": duration
                    }
                }
            ]
        }

    # ------------------------------------------------
    # Unknown Tool
    # ------------------------------------------------

    return {
        "results": [
            {
                "toolCallId": tool_id,
                "result": f"Unknown tool: {tool_name}"
            }
        ]
    }


# ---------------------------------------------------
# Webhook
# ---------------------------------------------------

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):

    raw = await request.body()

    print("\n")
    print("=" * 70)
    print("RAW REQUEST")
    print(raw.decode("utf-8", errors="replace"))
    print("=" * 70)

    try:
        payload = json.loads(raw)

    except Exception as e:

        print("JSON Error:", e)

        return {
            "status": "error",
            "message": str(e)
        }

    print(json.dumps(payload, indent=2))

    message = payload.get("message", {})
    message_type = message.get("type")

    print("Message Type:", message_type)

    # ------------------------------------------------
    # NEW VAPI FORMAT
    # ------------------------------------------------

    if message_type == "tool-calls":

        tool_calls = message.get("toolCalls", [])

        results = []

        for tool in tool_calls:

            tool_id = tool["id"]

            tool_name = tool["function"]["name"]

            args = tool["function"].get("arguments", {})

            response = handle_tool(
                tool_name,
                tool_id,
                args
            )

            results.extend(response["results"])

        return {
            "results": results
        }

    # ------------------------------------------------
    # LEGACY FORMAT
    # ------------------------------------------------

    if message_type == "function-call":

        func = message["functionCall"]

        return handle_tool(
            func["name"],
            func["id"],
            func.get("parameters", {})
        )

    print("Unhandled message type.")

    return {
        "status": "ignored"
    }


# ---------------------------------------------------
# Debug Endpoints
# ---------------------------------------------------

@app.get("/test/db")
async def test_db():

    return (
        supabase
        .table("jobs")
        .select("*")
        .execute()
        .data
    )


@app.post("/test/book")
async def test_book():

    return handle_tool(
        "book_job",
        "debug123",
        {
            "customer_name": "John",
            "phone_number": "5551234567",
            "address": "123 Main St",
            "description": "Kitchen sink clogged",
            "scheduled_time": "2026-07-03T09:00:00-07:00"
        }
    )


@app.post("/test/search_schedule")
async def test_search():

    return handle_tool(
        "search_schedule",
        "debug123",
        {}
    )


@app.get("/")
async def root():

    return {
        "message": "Server is running."
    }


if __name__ == "__main__":

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
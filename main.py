from fastapi import FastAPI, Request
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


def get_booked_times():

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


    if tool_name == "get_availability":

        requested_time = args.get("requested_time")

        response = (
            supabase
            .table("jobs")
            .select("scheduled_start_time")
            .eq("scheduled_start_time", requested_time)
            .execute()
        )

        available = len(response.data) == 0

        return {
            "results": [
                {
                    "toolCallId": tool_id,
                    "result": {
                        "available": available,
                        "requested_time": requested_time
                    }
                }
            ]
        }
    # ------------------------------------------------
    # search_schedule
    # ------------------------------------------------

    if tool_name == "search_schedule":

        from datetime import datetime, timedelta

        start = datetime.fromisoformat(
            args["start_range"].replace("Z", "+00:00")
        )

        end = datetime.fromisoformat(
            args["end_range"].replace("Z", "+00:00")
        )

        max_results = args.get("max_results", 3)

        booked = (
            supabase
            .table("jobs")
            .select("scheduled_start_time")
            .gte("scheduled_start_time", start.isoformat())
            .lte("scheduled_start_time", end.isoformat())
            .execute()
        )

        booked_times = {
            row["scheduled_start_time"]
            for row in booked.data
            if row["scheduled_start_time"]
        }

        slots = []

        current = start

        while current <= end:

            if 8 <= current.hour < 17:

                if current.isoformat() not in booked_times:

                    slots.append(current.isoformat())

            current += timedelta(hours=1)

        slots = slots[:max_results]

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

        scheduled_time = args.get("scheduled_time")

        existing = (
            supabase
            .table("jobs")
            .select("id")
            .eq("scheduled_start_time", scheduled_time)
            .execute()
        )

        if len(existing.data) > 0:

            return {
                "results": [
                    {
                        "toolCallId": tool_id,
                        "result": {
                            "success": False,
                            "message": "That appointment has already been booked."
                        }
                    }
                ]
            }

        job = {

            "customer_name": args.get("customer_name"),
            "phone_number": args.get("phone_number"),
            "address": args.get("address"),
            "description": args.get("description"),

            "scheduled_start_time": scheduled_time,

            "status": "Booked",
            "category": "General",
            "duration_minutes": 60,
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
                        "message": "Appointment booked successfully.",
                        "job": inserted.data[0]
                    }
                }
            ],
            "endCall": True
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
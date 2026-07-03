from db import supabase

try:
    data = {"job_type": "Kitchen", "start_time": "2026-06-25T10:00:00Z", "duration_minutes": 30, "comment": "Direct test"}
    response = supabase.table("jobs").insert(data).execute()
    print("Database write successful!")
except Exception as e:
    print(f"Database Error: {e}")
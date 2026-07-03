import requests

# This simulates what Vapi sends to your server
mock_payload = {
    "message": {
        "type": "function-call",
        "functionCall": {
            "name": "book_job",
            "id": "test-123",
            "parameters": {
                "job_type": "Kitchen",
                "start_time": "2026-06-25T10:00:00Z",
                "duration_minutes": 60,
                "comment": "Testing the system"
            }
        }
    }
}

response = requests.post("http://127.0.0.1:8000/vapi-webhook", json=mock_payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
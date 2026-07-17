import os, httpx

GOOGLE_MAPS_API_KEY = os.environ["GOOGLE_MAPS_API_KEY"]

async def get_travel_info(origin: str, destination: str) -> dict | None:
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": origin, "destinations": destination,
                "key": GOOGLE_MAPS_API_KEY, "units": "imperial"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
    element = resp.json()["rows"][0]["elements"][0]
    if element["status"] != "OK":
        return None
    return {
        "distance_miles": element["distance"]["value"] / 1609.34,
        "travel_minutes": round(element["duration"]["value"] / 60),
    }
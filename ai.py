import os
import json
from dotenv import load_dotenv
from google import genai
from pathlib import Path


load_dotenv()
BUSINESS_PROMPT = Path("prompt.txt").read_text()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def estimate_duration(description: str):

    prompt = f"""
    {BUSINESS_PROMPT}

    Customer description:

    "{description}"

    Estimate the duration.

    Return JSON:

    {{
        "duration_minutes": integer,
        "confidence": float,
        "reason": "..."
    }}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    print("========== GEMINI RESPONSE ==========")
    print(repr(response.text))
    print("=====================================")

    
    text = response.text.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()

        # Remove first line (```json)
        lines = lines[1:]

        # Remove last line (```)
        if lines[-1].startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines)

    return json.loads(text)
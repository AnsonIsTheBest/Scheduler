import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def estimate_duration(description: str, business_prompt: str = ""):

    prompt = f"""
{business_prompt}

You are estimating how long a job will take based on a customer's phone description.

Customer description:
"{description}"

Estimate the duration in minutes for a typical job like this.

Set "confidence" LOW (below 0.5) if any of these are true:
- The description is vague, unclear, or missing key details
- The scope could vary a lot depending on things you can't know over the phone
- You genuinely cannot tell what's wrong just from what the customer said

Set "confidence" HIGH (0.7 or above) only when the description is specific and clearly a standard job.

When confidence is low, this means an in-person visit is needed before the real job can be scheduled — "duration_minutes" should reflect a short initial inspection visit, not a full-job guess.

Return ONLY valid JSON, no other text:
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

    text = response.text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    return json.loads(text)
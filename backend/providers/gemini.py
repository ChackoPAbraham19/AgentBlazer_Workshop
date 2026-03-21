# ─────────────────────────────────────────────────────────
# providers/gemini.py
# Handles all API communication with Google Gemini.
# Model: Gemini 1.5 Flash (gemini-1.5-flash)
# ─────────────────────────────────────────────────────────

import os
import httpx
from backend.config import GEMINI_API_URL


def call(model: str, system_prompt: str, user_message: str) -> str:
    """
    Send a chat completion request to the Google Gemini API.

    Args:
        model:         Gemini model string (e.g. 'gemini-1.5-pro')
        system_prompt: Instruction prompt defining response structure
        user_message:  The actual content to respond to

    Returns:
        The model's response as a plain string.

    Raises:
        RuntimeError: If the API returns a non-200 status or an unexpected payload.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment.")

    # Use the v1beta endpoint which should have the latest models
    base_url = "https://generativelanguage.googleapis.com/v1beta/models/"
    url = f"{base_url}{model}:generateContent?key={api_key}"

    # Gemini API expects system instructions in a different format
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": system_prompt}
                ]
            },
            {
                "parts": [
                    {"text": user_message}
                ]
            }
        ]
    }

    response = httpx.post(url, json=payload, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"Gemini API error {response.status_code}: {response.text}"
        )

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response structure: {e}\n{data}")
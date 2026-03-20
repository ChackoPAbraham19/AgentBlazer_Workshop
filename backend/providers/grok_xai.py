# ─────────────────────────────────────────────────────────
# providers/grok.py
# Handles all API communication with xAI Grok.
# Note: This is different from groq.py (Groq provider)
# Model: Grok 2 (grok-2)
# ─────────────────────────────────────────────────────────

import os
import httpx
from backend.config import GROK_API_URL


def call(model: str, system_prompt: str, user_message: str) -> str:
    """
    Send a chat completion request to the xAI Grok API.

    Args:
        model:         Grok model string (e.g. 'grok-2')
        system_prompt: Instruction prompt defining response structure
        user_message:  The actual content to respond to

    Returns:
        The model's response as a plain string.

    Raises:
        RuntimeError: If the API returns a non-200 status or an unexpected payload.
    """
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        raise RuntimeError("GROK_API_KEY is not set in the environment.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }

    response = httpx.post(GROK_API_URL, json=payload, headers=headers, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"Grok API error {response.status_code}: {response.text}"
        )

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Grok response structure: {e}\n{data}")
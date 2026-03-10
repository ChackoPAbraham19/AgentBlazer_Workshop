# ─────────────────────────────────────────────────────────
# providers/groq.py
# Handles all API communication with Groq.
# Model: LLaMA 3.3 70B (llama-3.3-70b-versatile)
# ─────────────────────────────────────────────────────────

import os
import httpx
from backend.config import GROQ_API_URL


def call(model: str, system_prompt: str, user_message: str) -> str:
    """
    Send a chat completion request to the Groq API.

    Args:
        model:         Groq model string (e.g. 'llama-3.3-70b-versatile')
        system_prompt: Instruction prompt defining response structure
        user_message:  The actual content to respond to

    Returns:
        The model's response as a plain string.

    Raises:
        RuntimeError: If the API returns a non-200 status or an unexpected payload.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in the environment.")

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

    response = httpx.post(GROQ_API_URL, json=payload, headers=headers, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"Groq API error {response.status_code}: {response.text}"
        )

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Groq response structure: {e}\n{data}")
# ─────────────────────────────────────────────────────────
# config.py
# Central configuration for the LLM Council.
# Workshop participants can modify this file to swap models,
# adjust prompts, or change API settings.
# ─────────────────────────────────────────────────────────

# --- API Base URLs ---
GROQ_API_URL    = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_API_URL  = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

# --- Council Models ---
COUNCIL_MODELS = [
    {
        "id":       "llama",
        "name":     "LLaMA 3.3 70B",
        "model":    "llama-3.3-70b-versatile",
        "provider": "groq",
    },
    {
    "id":       "compound",
    "name":     "Compound Beta",
    "model":    "compound-beta",
    "provider": "groq",
},
]

# --- Judge Model ---
JUDGE_MODEL = {
    "id":       "mistral",
    "name":     "Mistral Small",
    "model":    "mistral-small-latest",
    "provider": "mistral",
}

# --- Stage Prompts ---

STAGE1_PROMPT = STAGE1_PROMPT = """You are a council member answering a question.
You must structure your response exactly as follows:

## Reasoning
Think through the problem deeply before answering. Your reasoning must include:
- What is actually being asked
- What you already know about this topic
- Any edge cases, nuances, or common misconceptions worth addressing
- How you will structure your answer and why
Be thorough — at least 150 words of genuine thinking.

## Answer
Your final answer, clearly stated with a concrete code example where relevant.

Do not skip steps. Do not jump straight to the answer."""

STAGE2_PROMPT = """You are a council member reviewing the responses of your peers.
The responses have been anonymised — do not attempt to identify the authors.

You must structure your response exactly as follows:

## Critique
<Evaluate the reasoning quality of each response. Be specific about what is strong or weak.>

## Ranking
<Rank the responses from best to worst and explain why.>

Do not deviate from this format."""

STAGE3_PROMPT = """You are the judge of an LLM council.
You have received multiple model responses and peer reviews for the same question.
Your task is to synthesise a final authoritative answer.

You must structure your response exactly as follows:

## Summary
<One paragraph summarising where the models agreed and where they diverged.>

## Verdict
<The best possible answer to the original question, incorporating the strongest reasoning from all responses.>

Do not deviate from this format."""
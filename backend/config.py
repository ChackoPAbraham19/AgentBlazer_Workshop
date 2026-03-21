# ─────────────────────────────────────────────────────────
# config.py
# Central configuration for the LLM Council.
# Workshop participants can modify this file to swap models,
# adjust prompts, or change API settings.
# ─────────────────────────────────────────────────────────

# --- API Base URLs ---
GROQ_API_URL    = "https://api.groq.com/openai/v1/chat/completions"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
GEMINI_API_URL  = "https://generativelanguage.googleapis.com/v1beta/models/"
GROK_API_URL    = "https://api.x.ai/v1/chat/completions"

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
        "model":    "groq/compound",
        "provider": "groq",
    },
    {
        "id":       "gemini",
        "name":     "Gemini 2.0 Flash",
        "model":    "gemini-2.0-flash",
        "provider": "gemini",
    },
    {
        "id":       "grok",
        "name":     "Grok 2",
        "model":    "grok-2",
        "provider": "grok",
    },
    {
        "id":       "mistral-large",
        "name":     "Mistral Large",
        "model":    "mistral-large-latest",
        "provider": "mistral",
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

STAGE1_PROMPT = """You are a council member answering a question.
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
The responses have been anonymised — you do NOT know which model gave which answer.
You must remain anonymous and not reveal your identity.

You must structure your response exactly as follows:

## Critique
Provide detailed, constructive feedback on each response:
- What is strong about their reasoning and answer?
- What could be improved or is weak?
- Be specific and honest (this is a "roast" but constructive)
- Compare the approaches between the different responses
- Point out any flaws, biases, or oversights

## Ranking
Rank the responses from best (#1) to worst and explain:
- Why the top response is strongest
- Why the bottom response has issues
- What makes one approach better than another

Be thorough, honest, and helpful in your feedback."""

STAGE3_PROMPT = """You are the judge of an LLM council.
You have received multiple model responses and anonymous peer reviews.
Your task is to synthesise a final authoritative answer.

You must structure your response exactly as follows:

## Summary
<One paragraph summarising where the models agreed and disagreed, including key critiques from the reviews.>

## Verdict
<The best possible answer to the original question, incorporating the strongest reasoning from all responses and addressing the critiques.>

Do not deviate from this format."""
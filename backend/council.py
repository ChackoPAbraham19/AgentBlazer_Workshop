# ─────────────────────────────────────────────────────────
# council.py
# Core orchestration logic for the three-stage council.
# This is the brain of the application.
#
# Stage 1 — Each council model answers independently
# Stage 2 — Each model reviews the others (anonymised)
# Stage 3 — The judge synthesises a final verdict
# ─────────────────────────────────────────────────────────

import random
from backend.config import COUNCIL_MODELS, JUDGE_MODEL, STAGE1_PROMPT, STAGE2_PROMPT, STAGE3_PROMPT
from backend.providers import call_provider


# ─────────────────────────────────────────────────────────
# Stage 1 — Independent Opinions
# ─────────────────────────────────────────────────────────

def run_stage1(question: str) -> list[dict]:
    """
    Send the question to each council model sequentially.
    Each model is prompted to show its reasoning before answering.

    Args:
        question: The user's question.

    Returns:
        List of dicts with keys: model_id, model_name, raw, reasoning, answer.
    """
    responses = []

    for member in COUNCIL_MODELS:
        raw = call_provider(
            provider=member["provider"],
            model=member["model"],
            system_prompt=STAGE1_PROMPT,
            user_message=question,
        )

        reasoning, answer = _parse_sections(raw, ["## Reasoning", "## Answer"])

        responses.append({
            "model_id":   member["id"],
            "model_name": member["name"],
            "raw":        raw,
            "reasoning":  reasoning,
            "answer":     answer,
        })

    return responses


# ─────────────────────────────────────────────────────────
# Stage 2 — Peer Review
# ─────────────────────────────────────────────────────────

def run_stage2(question: str, stage1_responses: list[dict]) -> list[dict]:
    """
    Each council model reviews the anonymised responses of the others.
    Model identities are shuffled before being shown to prevent bias.

    Args:
        question:         The original user question.
        stage1_responses: Output from run_stage1().

    Returns:
        List of dicts with keys: reviewer_id, reviewer_name, raw, critique, ranking.
    """
    reviews = []

    for member in COUNCIL_MODELS:
        # Build anonymised peer responses — exclude the reviewer's own response
        peers = [r for r in stage1_responses if r["model_id"] != member["id"]]
        anonymised = _anonymise(peers)

        user_message = (
            f"Original question: {question}\n\n"
            f"Peer responses for review:\n\n{anonymised}"
        )

        raw = call_provider(
            provider=member["provider"],
            model=member["model"],
            system_prompt=STAGE2_PROMPT,
            user_message=user_message,
        )

        critique, ranking = _parse_sections(raw, ["## Critique", "## Ranking"])

        reviews.append({
            "reviewer_id":   member["id"],
            "reviewer_name": member["name"],
            "raw":           raw,
            "critique":      critique,
            "ranking":       ranking,
        })

    return reviews


# ─────────────────────────────────────────────────────────
# Stage 3 — Final Verdict
# ─────────────────────────────────────────────────────────

def run_stage3(
    question: str,
    stage1_responses: list[dict],
    stage2_reviews: list[dict],
) -> dict:
    """
    The judge model (Mistral) synthesises a final answer from all
    council responses and peer reviews.

    Args:
        question:         The original user question.
        stage1_responses: Output from run_stage1().
        stage2_reviews:   Output from run_stage2().

    Returns:
        Dict with keys: raw, summary, verdict.
    """
    responses_block = "\n\n".join([
        f"Response from Model {i+1}:\n"
        f"Reasoning: {r['reasoning']}\n"
        f"Answer: {r['answer']}"
        for i, r in enumerate(stage1_responses)
    ])

    reviews_block = "\n\n".join([
        f"Review from Reviewer {i+1}:\n"
        f"Critique: {rv['critique']}\n"
        f"Ranking: {rv['ranking']}"
        for i, rv in enumerate(stage2_reviews)
    ])

    user_message = (
        f"Original question: {question}\n\n"
        f"--- Council Responses ---\n{responses_block}\n\n"
        f"--- Peer Reviews ---\n{reviews_block}"
    )

    raw = call_provider(
        provider=JUDGE_MODEL["provider"],
        model=JUDGE_MODEL["model"],
        system_prompt=STAGE3_PROMPT,
        user_message=user_message,
    )

    summary, verdict = _parse_sections(raw, ["## Summary", "## Verdict"])

    return {
        "raw":     raw,
        "summary": summary,
        "verdict": verdict,
    }


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def _anonymise(responses: list[dict]) -> str:
    """
    Shuffle and label responses as generic identifiers (Model A, Model B...)
    so the reviewing model cannot identify authors.
    """
    shuffled = responses.copy()
    random.shuffle(shuffled)
    labels = "ABCDEFGH"

    blocks = []
    for i, r in enumerate(shuffled):
        blocks.append(
            f"Model {labels[i]}:\n"
            f"Reasoning: {r['reasoning']}\n"
            f"Answer: {r['answer']}"
        )
    return "\n\n".join(blocks)


def _parse_sections(text: str, headers: list[str]) -> tuple:
    """
    Extract content between known section headers from a model response.
    Falls back to the raw text if a header is not found.

    Args:
        text:    Raw model response string.
        headers: Ordered list of section headers to extract (e.g. ['## Reasoning', '## Answer']).

    Returns:
        Tuple of strings, one per header, in the same order.
    """
    results = []
    for i, header in enumerate(headers):
        start = text.find(header)
        if start == -1:
            results.append(text.strip())
            continue
        start += len(header)
        end = len(text)
        for next_header in headers[i+1:]:
            pos = text.find(next_header, start)
            if pos != -1:
                end = pos
                break
        results.append(text[start:end].strip())
    return tuple(results)
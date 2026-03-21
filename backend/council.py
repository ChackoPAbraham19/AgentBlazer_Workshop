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
import json
import os
from datetime import datetime
from pathlib import Path
from backend.config import COUNCIL_MODELS, JUDGE_MODEL, STAGE1_PROMPT, STAGE2_PROMPT, STAGE3_PROMPT
from backend.providers import call_provider

# Performance tracking
PERFORMANCE_FILE = Path("data/model_performance.json")

def _load_performance_data():
    """Load model performance data from file."""
    if PERFORMANCE_FILE.exists():
        try:
            with open(PERFORMANCE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def _save_performance_data(data):
    """Save model performance data to file."""
    PERFORMANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PERFORMANCE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def _get_selected_models(model_ids):
    """Get model configurations for selected model IDs."""
    if not model_ids:
        return COUNCIL_MODELS
    return [m for m in COUNCIL_MODELS if m["id"] in model_ids]

def update_model_performance(stage1_responses: list[dict], stage2_reviews: list[dict]):
    """
    Update performance metrics for models based on peer reviews.
    """
    performance_data = _load_performance_data()

    # Initialize performance data for new models
    for response in stage1_responses:
        model_id = response["model_id"]
        if model_id not in performance_data:
            performance_data[model_id] = {
                "name": response["model_name"],
                "total_sessions": 0,
                "total_rankings": [],
                "win_count": 0,  # Times ranked #1
                "avg_ranking": 0,
                "total_critiques": 0,
                "critique_scores": [],  # 1-5 star ratings of critiques
                "last_used": None
            }

    # Process reviews to extract rankings and critique quality
    for review in stage2_reviews:
        reviewer_id = review["reviewer_id"]

        # Simple ranking extraction - just count how many times each model is mentioned positively
        ranking_text = review["ranking"].lower()

        # For now, implement a simple ranking system
        # Each model gets a default ranking, and we adjust based on mentions
        model_rankings = {}
        for response in stage1_responses:
            model_id = response["model_id"]
            if model_id != reviewer_id:  # Don't rank yourself
                # Simple heuristic: look for the model name in positive contexts
                model_name = response["model_name"].lower()
                if model_name in ranking_text:
                    # If mentioned, assume it's ranked (simplified)
                    model_rankings[model_id] = 1  # Default ranking
                else:
                    model_rankings[model_id] = 2  # Lower ranking if not mentioned

        # Convert to rankings list
        for model_id, ranking in model_rankings.items():
            if model_id in performance_data:
                performance_data[model_id]["total_rankings"].append(ranking)
                if ranking == 1:
                    performance_data[model_id]["win_count"] += 1

        # Update session count and last used
        for response in stage1_responses:
            model_id = response["model_id"]
            performance_data[model_id]["total_sessions"] += 1
            performance_data[model_id]["last_used"] = datetime.utcnow().isoformat()

            # Calculate average ranking
            rankings = performance_data[model_id]["total_rankings"]
            if rankings:
                performance_data[model_id]["avg_ranking"] = sum(rankings) / len(rankings)

    _save_performance_data(performance_data)

def get_model_performance():
    """
    Get performance data for all models.
    """
    return _load_performance_data()


# ─────────────────────────────────────────────────────────
# Stage 1 — Independent Opinions
# ─────────────────────────────────────────────────────────

def run_stage1(question: str, selected_model_ids: list[str] = None) -> list[dict]:
    """
    Send the question to each selected council model sequentially.
    Each model is prompted to show its reasoning before answering.

    Args:
        question: The user's question.
        selected_model_ids: Optional list of model IDs to use. If None, uses all models.

    Returns:
        List of dicts with keys: model_id, model_name, raw, reasoning, answer.
    """
    selected_models = _get_selected_models(selected_model_ids)
    responses = []

    for member in selected_models:
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

    # Only let selected models (those in stage1_responses) do the reviewing
    selected_models = [m for m in COUNCIL_MODELS if m["id"] in [r["model_id"] for r in stage1_responses]]

    for member in selected_models:
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
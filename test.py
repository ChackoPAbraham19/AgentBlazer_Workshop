import httpx
import sys

BASE_URL = "http://localhost:8000"
TEST_QUESTION = "What is recursion in programming? Explain with an example."

def print_pass(msg): print(f"  [PASS] {msg}")
def print_fail(msg): print(f"  [FAIL] {msg}")
def print_warn(msg): print(f"  [WARN] {msg}")
def print_section(msg): print(f"\n{'─'*55}\n  {msg}\n{'─'*55}")


# ─────────────────────────────────────────────────────────
# TEST 1 — Health Check
# Verifies the FastAPI server is reachable before proceeding.
# ─────────────────────────────────────────────────────────
def test_health():
    print_section("TEST 1: Health Check")
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200
        print_pass(f"Server is reachable — {r.json()}")
    except Exception as e:
        print_fail(f"Server not reachable: {e}")
        print("\n  Ensure the backend is running:")
        print("  uvicorn backend.main:app --reload\n")
        sys.exit(1)


# ─────────────────────────────────────────────────────────
# TEST 2 — Stage 1: Independent Opinions
# Each council model (LLaMA 3.3 70B, Compound Beta) receives
# the question independently and must return a structured
# response containing a reasoning block and a final answer.
# ─────────────────────────────────────────────────────────
def test_stage1():
    print_section("TEST 2: Stage 1 — Independent Opinions")
    try:
        r = httpx.post(
            f"{BASE_URL}/stage1",
            json={"question": TEST_QUESTION, "selected_models": ["llama", "compound"]},
            timeout=30
        )
        assert r.status_code == 200, f"Unexpected status code: {r.status_code}"
        data = r.json()

        assert "responses" in data, "Response payload missing 'responses' key"
        assert len(data["responses"]) == 2, \
            f"Expected 2 model responses, received {len(data['responses'])}"

        for resp in data["responses"]:
            assert "model_id"   in resp, "Missing 'model_id' field in response"
            assert "model_name" in resp, "Missing 'model_name' field in response"
            assert "reasoning"  in resp, "Missing 'reasoning' field in response"
            assert "answer"     in resp, "Missing 'answer' field in response"
            assert len(resp["reasoning"]) > 50, \
                f"{resp['model_name']}: Reasoning block too short — check Stage 1 prompt"
            assert len(resp["answer"]) > 50, \
                f"{resp['model_name']}: Answer too short — model may have failed silently"
            print_pass(f"{resp['model_name']} — response received ({len(resp['answer'])} chars)")

        return data["responses"]

    except AssertionError as e:
        print_fail(f"Assertion error: {e}")
    except Exception as e:
        print_fail(f"Request failed: {e}")
    return None


# ─────────────────────────────────────────────────────────
# TEST 3 — Stage 2: Peer Review
# Each model receives the other's response with model
# identities anonymised. It must return a critique and
# a ranking. Anonymisation is also verified here.
# ─────────────────────────────────────────────────────────
def test_stage2(stage1_responses):
    print_section("TEST 3: Stage 2 — Peer Review")
    if not stage1_responses:
        print_fail("Skipping — Stage 1 did not return valid responses")
        return None
    try:
        r = httpx.post(
            f"{BASE_URL}/stage2",
            json={
                "question":  TEST_QUESTION,
                "responses": stage1_responses
            },
            timeout=30
        )
        assert r.status_code == 200, f"Unexpected status code: {r.status_code}"
        data = r.json()

        assert "reviews" in data, "Response payload missing 'reviews' key"
        assert len(data["reviews"]) == 2, \
            f"Expected 2 reviews, received {len(data['reviews'])}"

        for review in data["reviews"]:
            assert "reviewer_id"   in review, "Missing 'reviewer_id' field"
            assert "reviewer_name" in review, "Missing 'reviewer_name' field"
            assert "critique"      in review, "Missing 'critique' field"
            assert "ranking"       in review, "Missing 'ranking' field"
            assert len(review["critique"]) > 50, \
                f"{review['reviewer_name']}: Critique too short — check Stage 2 prompt"
            print_pass(f"{review['reviewer_name']} — review received")

        # Verify anonymisation — model provider names should not appear in critiques
        identifiers = ["llama", "gemini", "groq", "google", "mistral", "compound"]
        for review in data["reviews"]:
            for name in identifiers:
                if name.lower() in review["critique"].lower():
                    print_warn(
                        f"Identifier '{name}' detected in {review['reviewer_name']} critique "
                        f"— anonymisation may have leaked model identity"
                    )

        return data["reviews"]

    except AssertionError as e:
        print_fail(f"Assertion error: {e}")
    except Exception as e:
        print_fail(f"Request failed: {e}")
    return None


# ─────────────────────────────────────────────────────────
# TEST 4 — Stage 3: Final Verdict
# Mistral (judge) receives all council responses and peer
# reviews. It must return a synthesised verdict and a
# brief summary highlighting agreements and divergences.
# ─────────────────────────────────────────────────────────
def test_stage3(stage1_responses, stage2_reviews):
    print_section("TEST 4: Stage 3 — Mistral Judge Verdict")
    if not stage1_responses or not stage2_reviews:
        print_fail("Skipping — one or more prior stages did not complete successfully")
        return None
    try:
        r = httpx.post(
            f"{BASE_URL}/stage3",
            json={
                "question":  TEST_QUESTION,
                "responses": stage1_responses,
                "reviews":   stage2_reviews
            },
            timeout=60
        )
        assert r.status_code == 200, f"Unexpected status code: {r.status_code}"
        data = r.json()

        assert "verdict" in data, "Response payload missing 'verdict' field"
        assert "summary" in data, "Response payload missing 'summary' field"
        assert len(data["verdict"]) > 100, \
            "Verdict is too short — judge model may not have synthesised correctly"

        print_pass(f"Mistral judge — verdict received ({len(data['verdict'])} chars)")
        print_pass(f"Summary preview: {data['summary'][:80]}...")
        return data

    except AssertionError as e:
        print_fail(f"Assertion error: {e}")
    except Exception as e:
        print_fail(f"Request failed: {e}")
    return None


# ─────────────────────────────────────────────────────────
# TEST 5 — Session Persistence
# Confirms that session logs are being written to
# data/sessions/ and that the /sessions endpoint is live.
# ─────────────────────────────────────────────────────────
def test_session_save():
    print_section("TEST 5: Session Persistence")
    try:
        r = httpx.get(f"{BASE_URL}/sessions", timeout=10)
        assert r.status_code == 200
        sessions = r.json()
        assert isinstance(sessions, list), \
            "Expected /sessions to return a list"
        print_pass(f"Sessions endpoint reachable — {len(sessions)} session(s) on record")
    except Exception as e:
        print_fail(f"Session check failed: {e}")


# ─────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nLLM Council — Backend Test Suite")
    print(f"  Target  : {BASE_URL}")
    print(f"  Question: {TEST_QUESTION}")

    test_health()
    responses = test_stage1()
    reviews   = test_stage2(responses)
    test_stage3(responses, reviews)
    test_session_save()

    print_section("Test Run Complete")
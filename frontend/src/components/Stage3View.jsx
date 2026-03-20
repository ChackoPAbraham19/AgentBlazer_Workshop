import React, { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function Stage3View({ data }) {
  const [verdictRating, setVerdictRating] = useState(0);
  const [reviewRatings, setReviewRatings] = useState([]);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmitRating = async () => {
    try {
      const r = await fetch(`http://localhost:8000/rate_session/${data.session_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          verdict_rating: verdictRating,
          review_ratings: reviewRatings,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      setSubmitted(true);
    } catch (e) {
      alert("Error submitting rating: " + e.message);
    }
  };

  return (
    <div className="verdict-container">
      <div className="verdict-judge-tag">
        <span className="judge-dot" />
        MISTRAL SMALL — JUDGE
      </div>

      <div className="verdict-card">
        <div className="verdict-section">
          <div className="verdict-section-label">SUMMARY</div>
          <div className="verdict-summary">
            <ReactMarkdown>{data.summary}</ReactMarkdown>
          </div>
        </div>

        <div className="verdict-divider" />

        <div className="verdict-section">
          <div className="verdict-section-label">FINAL VERDICT</div>
          <div className="verdict-body">
            <ReactMarkdown>{data.verdict}</ReactMarkdown>
          </div>
        </div>
      </div>

      {!submitted && (
        <div className="rating-section">
          <h3>Rate this verdict</h3>
          <div>
            <label>Verdict Rating (1-5):</label>
            <select value={verdictRating} onChange={(e) => setVerdictRating(Number(e.target.value))}>
              <option value={0}>Select</option>
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
              <option value={4}>4</option>
              <option value={5}>5</option>
            </select>
          </div>
          <button onClick={handleSubmitRating} disabled={verdictRating === 0}>Submit Rating</button>
        </div>
      )}

      {submitted && <p>Thank you for your feedback!</p>}
    </div>
  );
}
import React, { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

export default function SessionsView({ onBack }) {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const BASE = "http://localhost:8000";

  useEffect(() => {
    fetchSessions();
  }, []);

  async function fetchSessions() {
    try {
      const r = await fetch(`${BASE}/sessions`);
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setSessions(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchSessionDetails(sessionId) {
    try {
      const r = await fetch(`${BASE}/sessions/${sessionId}`);
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setSelectedSession(data);
    } catch (e) {
      setError(e.message);
    }
  }

  if (loading) return <div>Loading sessions...</div>;
  if (error) return <div>Error: {error}</div>;

  if (selectedSession) {
    return (
      <div className="session-detail">
        <button onClick={() => setSelectedSession(null)}>← Back to Sessions</button>
        <h2>Session: {selectedSession.question}</h2>
        <p><strong>Timestamp:</strong> {selectedSession.timestamp}</p>
        {selectedSession.ratings && (
          <p><strong>Verdict Rating:</strong> {selectedSession.ratings.verdict_rating}/5</p>
        )}
        <div>
          <h3>Final Verdict</h3>
          <ReactMarkdown>{selectedSession.stage3.verdict}</ReactMarkdown>
        </div>
        {/* Add more details if needed */}
      </div>
    );
  }

  return (
    <div className="sessions-list">
      <h2>Past Interactions</h2>
      {sessions.length === 0 ? (
        <p>No sessions yet.</p>
      ) : (
        <ul>
          {sessions.map((session) => (
            <li key={session.session_id} onClick={() => fetchSessionDetails(session.session_id)}>
              <strong>{session.question}</strong> - {session.timestamp}
              {session.ratings && <span> (Rated {session.ratings.verdict_rating}/5)</span>}
            </li>
          ))}
        </ul>
      )}
      <button onClick={onBack}>Back to Main</button>
    </div>
  );
}
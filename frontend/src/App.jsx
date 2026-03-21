import { useState, useEffect } from "react";
import QuestionInput from "./components/QuestionInput";
import StageView from "./components/StageView";
import SessionsView from "./components/SessionsView";
import "./index.css";

export default function App() {
  const [stage, setStage] = useState(0);
  const [question, setQuestion] = useState("");
  const [selectedModels, setSelectedModels] = useState([]);
  const [availableModels, setAvailableModels] = useState([]);
  const [stage1Data, setStage1Data] = useState(null);
  const [stage2Data, setStage2Data] = useState(null);
  const [stage3Data, setStage3Data] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewingSessions, setViewingSessions] = useState(false);

  const BASE = "http://localhost:8000";

  // Load available models on component mount
  useEffect(() => {
    fetch(`${BASE}/models`)
      .then(r => r.json())
      .then(data => {
        setAvailableModels(data.models);
        // Auto-select top 2 performing models
        const sorted = data.models.sort((a, b) => b.performance.win_rate - a.performance.win_rate);
        setSelectedModels(sorted.slice(0, 2).map(m => m.id));
      })
      .catch(e => console.error("Failed to load models:", e));
  }, []);

  function toggleModelSelection(modelId) {
    setSelectedModels(prev => {
      if (prev.includes(modelId)) {
        return prev.filter(id => id !== modelId);
      } else if (prev.length < 2) {
        return [...prev, modelId];
      }
      return prev;
    });
  }

  async function handleSubmit(q) {
    setQuestion(q);
    setError(null);
    setLoading(true);
    setStage(1);
    try {
      const r = await fetch(`${BASE}/stage1`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          question: q,
          selected_models: selectedModels.length === 2 ? selectedModels : null
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setStage1Data(data.responses);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleStage2() {
    setError(null);
    setLoading(true);
    setStage(2);
    try {
      const r = await fetch(`${BASE}/stage2`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, responses: stage1Data }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setStage2Data(data.reviews);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleStage3() {
    setError(null);
    setLoading(true);
    setStage(3);
    try {
      const r = await fetch(`${BASE}/stage3`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, responses: stage1Data, reviews: stage2Data }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setStage3Data(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setStage(0);
    setQuestion("");
    setStage1Data(null);
    setStage2Data(null);
    setStage3Data(null);
    setError(null);
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-bracket">[</span>
            <span className="logo-text">LLM COUNCIL</span>
            <span className="logo-bracket">]</span>
          </div>
          <div>
            <p className="tagline">Multi-model reasoning — step by step</p>
            <button className="btn-ghost" onClick={() => setViewingSessions(true)}>View History</button>
          </div>
        </div>
        {!viewingSessions && stage > 0 && (
          <div className="stage-indicator">
            {[1, 2, 3].map((s) => (
              <div key={s} className={`stage-pip ${stage >= s ? "active" : ""} ${stage === s && loading ? "pulsing" : ""}`}>
                <span className="pip-num">{s}</span>
                <span className="pip-label">{["Opinions", "Review", "Verdict"][s - 1]}</span>
              </div>
            ))}
          </div>
        )}
      </header>

      <main className="main">
        {error && (
          <div className="error-banner">
            <span className="error-tag">ERROR</span> {error}
          </div>
        )}
        {viewingSessions ? (
          <SessionsView onBack={() => setViewingSessions(false)} />
        ) : (
          <>
            {stage === 0 && (
              <QuestionInput 
                onSubmit={handleSubmit}
                availableModels={availableModels}
                selectedModels={selectedModels}
                onToggleModel={toggleModelSelection}
              />
            )}
            {stage >= 1 && (
              <StageView
                stage={stage}
                loading={loading}
                question={question}
                stage1Data={stage1Data}
                stage2Data={stage2Data}
                stage3Data={stage3Data}
                onNext={stage === 1 && !loading && stage1Data ? handleStage2
                      : stage === 2 && !loading && stage2Data ? handleStage3
                      : null}
                onReset={handleReset}
              />
            )}
          </>
        )}
      </main>

      <footer className="footer">
        <span>AgentBlazer Workshop</span>
        <span className="footer-sep">·</span>
        <span>LLaMA 70B · Compound Beta · Mistral</span>
      </footer>
    </div>
  );
}
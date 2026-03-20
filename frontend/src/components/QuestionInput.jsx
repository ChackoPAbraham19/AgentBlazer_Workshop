import { useState } from "react";

const SAMPLE_QUESTIONS = [
  "What is recursion in programming?",
  "Explain the CAP theorem in distributed systems.",
  "What is the difference between a process and a thread?",
  "How does a neural network learn?",
  "What is Big O notation and why does it matter?",
];

export default function QuestionInput({ onSubmit, availableModels, selectedModels, onToggleModel }) {
  const [value, setValue] = useState("");

  function handleSubmit() {
    if (value.trim()) onSubmit(value.trim());
  }

  function handleKey(e) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleSubmit();
  }

  return (
    <div className="question-screen">
      <div className="question-card">
        <div className="question-header">
          <div className="question-label">SUBMIT YOUR QUESTION</div>
          <p className="question-hint">The council will reason independently, critique each other, then deliver a final verdict.</p>
        </div>

        <textarea
          className="question-textarea"
          placeholder="Ask something challenging..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKey}
          rows={4}
          autoFocus
        />

        {availableModels.length > 0 && (
          <div className="model-selection">
            <div className="model-selection-header">
              <span className="model-selection-label">SELECT 2 MODELS TO COMPETE:</span>
              <span className="model-selection-count">{selectedModels.length}/2 selected</span>
            </div>
            <div className="model-grid">
              {availableModels.map((model) => (
                <div
                  key={model.id}
                  className={`model-card ${selectedModels.includes(model.id) ? 'selected' : ''} ${selectedModels.length >= 2 && !selectedModels.includes(model.id) ? 'disabled' : ''}`}
                  onClick={() => onToggleModel(model.id)}
                >
                  <div className="model-name">{model.name}</div>
                  <div className="model-provider">{model.provider.toUpperCase()}</div>
                  <div className="model-stats">
                    <div className="stat">Sessions: {model.performance.total_sessions}</div>
                    <div className="stat">Win Rate: {(model.performance.win_rate * 100).toFixed(1)}%</div>
                    <div className="stat">Avg Rank: {model.performance.avg_ranking.toFixed(1)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="question-actions">
          <span className="question-shortcut">Ctrl + Enter to submit</span>
          <button
            className="btn-primary"
            onClick={handleSubmit}
            disabled={!value.trim()}
          >
            Convene the Council
          </button>
        </div>

        <div className="sample-questions">
          <div className="sample-label">SAMPLE QUESTIONS</div>
          <div className="sample-list">
            {SAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                className="sample-btn"
                onClick={() => setValue(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
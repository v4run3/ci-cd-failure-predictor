import { useState, useEffect } from "react";
import { fetchModelInfo } from "../api";

function ModelInfoCard() {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    fetchModelInfo().then(setInfo).catch(() => {});
  }, []);

  if (!info) {
    return (
      <div className="card">
        <div className="card-title">Model Info</div>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">Model Info</div>
      <div className="model-stat">
        <span className="label">Model</span>
        <span className="value">{info.model_name}</span>
      </div>
      <div className="model-stat">
        <span className="label">F1 Score</span>
        <span className="value">{info.best_f1_score?.toFixed(4)}</span>
      </div>
      <div className="model-stat">
        <span className="label">Train / Test</span>
        <span className="value">{info.train_size} / {info.test_size}</span>
      </div>
      <div className="model-stat">
        <span className="label">Features</span>
        <span className="value">{info.feature_count}</span>
      </div>
      <div className="model-stat">
        <span className="label">Trained At</span>
        <span className="value">{info.trained_at}</span>
      </div>
    </div>
  );
}

export default ModelInfoCard;

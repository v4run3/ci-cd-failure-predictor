import RiskGauge from "./RiskGauge";

function PredictionResult({ result }) {
  if (!result) {
    return (
      <div className="card result-panel">
        <div className="card-title">Prediction Result</div>
        <div className="empty-state">
          Submit build features to see the prediction
        </div>
      </div>
    );
  }

  return (
    <div className="card result-panel">
      <div className="card-title">Prediction Result</div>
      <RiskGauge probability={result.failure_probability} />
      <div className={`result-label ${result.label}`}>
        {result.label.toUpperCase()}
      </div>
      <div className="result-probability">
        Failure Probability: {(result.failure_probability * 100).toFixed(1)}%
      </div>
      <div className={`risk-badge ${result.risk_level}`}>
        {result.risk_level} risk
      </div>
      <div className="health-meta" style={{ marginTop: "1rem" }}>
        <span>Model: {result.model_name}</span>
        <span>Predicted: {new Date(result.predicted_at).toLocaleString()}</span>
      </div>
    </div>
  );
}

export default PredictionResult;

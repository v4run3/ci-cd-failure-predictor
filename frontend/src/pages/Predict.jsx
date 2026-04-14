import { useState } from "react";
import PredictionForm from "../components/PredictionForm";
import PredictionResult from "../components/PredictionResult";
import ScenarioSimulator from "../components/ScenarioSimulator";
import { predict } from "../api";

function Predict({ onPrediction }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastPayload, setLastPayload] = useState(null);

  const handleSubmit = async (payload, branchType, triggerType) => {
    setLoading(true);
    setError(null);
    try {
      const res = await predict(payload);
      setResult(res);
      setLastPayload(payload);

      // Save to history
      onPrediction({
        ...res,
        branch_type: branchType,
        trigger_type: triggerType,
        num_files_changed: payload.num_files_changed,
        test_fail_ratio: payload.test_fail_ratio,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Predict</h1>
        <p>Enter build features to predict failure probability</p>
      </div>

      <div className="predict-layout">
        <PredictionForm onSubmit={handleSubmit} loading={loading} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <PredictionResult result={result} />
          {error && <div className="error-msg">{error}</div>}
          
          {lastPayload && result && !error && (
            <ScenarioSimulator 
              originalPayload={lastPayload} 
              originalResult={result} 
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default Predict;

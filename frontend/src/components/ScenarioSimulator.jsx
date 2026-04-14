import { useState, useEffect, useRef } from "react";
import { predict } from "../api";
import RiskGauge from "./RiskGauge";

function ScenarioSimulator({ originalPayload, originalResult }) {
  const [simValues, setSimValues] = useState({
    num_files_changed: originalPayload.num_files_changed,
    lines_added: originalPayload.lines_added,
    test_fail_count: originalPayload.test_fail_count,
    build_duration_seconds: originalPayload.build_duration_seconds,
  });

  const [simResult, setSimResult] = useState(originalResult);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Debounce ref
  const debounceTimer = useRef(null);

  useEffect(() => {
    // Keep internal values in sync if originalPayload changes natively (new prediction)
    setSimValues({
      num_files_changed: originalPayload.num_files_changed,
      lines_added: originalPayload.lines_added,
      test_fail_count: originalPayload.test_fail_count,
      build_duration_seconds: originalPayload.build_duration_seconds,
    });
    setSimResult(originalResult);
  }, [originalPayload, originalResult]);

  const handleChange = (key, rawValue) => {
    let value = Number(rawValue);
    
    // Safety bounds based on model training ranges
    if (key === "num_files_changed" && value < 1) value = 1;
    if (value < 0) value = 0;

    const newValues = { ...simValues, [key]: value };
    setSimValues(newValues);

    // Debounce the API call to avoid spamming the backend while dragging
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    
    debounceTimer.current = setTimeout(() => {
      runSimulation(newValues);
    }, 400); // 400ms debounce
  };

  const runSimulation = async (values) => {
    setLoading(true);
    setError(null);

    // Auto-recalculate derived metrics based on the slider changes
    const linesAdded = Number(values.lines_added);
    const linesDeleted = Number(originalPayload.lines_deleted);
    const totalLines = linesAdded + linesDeleted;
    const numFiles = Number(values.num_files_changed);
    const linesPerFile = numFiles > 0 ? (totalLines / numFiles) : 0;
    
    const testCount = Number(originalPayload.test_count);
    const testFailCount = Number(values.test_fail_count);
    const testFailRatio = testCount > 0 ? (testFailCount / testCount) : 0;

    const simulatedPayload = {
      ...originalPayload,
      num_files_changed: numFiles,
      lines_added: linesAdded,
      test_fail_count: testFailCount,
      build_duration_seconds: Number(values.build_duration_seconds),
      
      // Override derived
      total_lines_changed: totalLines,
      lines_per_file: Math.round(linesPerFile * 100) / 100,
      test_fail_ratio: Math.round(testFailRatio * 10000) / 10000,
    };

    try {
      const res = await predict(simulatedPayload);
      setSimResult(res);
    } catch (err) {
      setError("Simulation failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Calculate Delta (Difference in failure probability)
  const origProb = (originalResult.failure_probability * 100);
  const simProb = (simResult.failure_probability * 100);
  const delta = (simProb - origProb).toFixed(1);
  const deltaColor = delta > 0 ? 'var(--danger-color)' : (delta < 0 ? 'var(--success-color)' : 'var(--text-color)');
  const deltaSign = delta > 0 ? '+' : '';

  return (
    <div className="card simulator-panel">
      <div className="card-title">
        "What-If" Scenario Simulator 🧪
      </div>
      <p style={{ fontSize: '0.9rem', color: 'var(--text-light)', marginBottom: '1rem' }}>
        Adjust the sliders below to see how changes to this commit impact the failure risk in real-time.
      </p>

      <div className="simulator-grid">
        <div className="slider-controls">
          <div className="slider-group">
            <label>
              Files Changed: <strong>{simValues.num_files_changed}</strong>
            </label>
            <input 
              type="range" 
              min="1" max="150" 
              value={simValues.num_files_changed}
              onChange={(e) => handleChange("num_files_changed", e.target.value)}
            />
          </div>

          <div className="slider-group">
            <label>
              Lines Added: <strong>{simValues.lines_added}</strong>
            </label>
            <input 
              type="range" 
              min="0" max="1500" step="10"
              value={simValues.lines_added}
              onChange={(e) => handleChange("lines_added", e.target.value)}
            />
          </div>

          <div className="slider-group">
            <label>
              Test Fail Count: <strong>{simValues.test_fail_count}</strong>
            </label>
            <input 
              type="range" 
              min="0" max={originalPayload.test_count || 100} 
              value={simValues.test_fail_count}
              onChange={(e) => handleChange("test_fail_count", e.target.value)}
            />
          </div>

          <div className="slider-group">
            <label>
              Build Duration (s): <strong>{simValues.build_duration_seconds}</strong>
            </label>
            <input 
              type="range" 
              min="10" max="1200" step="10"
              value={simValues.build_duration_seconds}
              onChange={(e) => handleChange("build_duration_seconds", e.target.value)}
            />
          </div>
        </div>

        <div className="simulator-result" style={loading ? {opacity: 0.5} : {}}>
          {error ? (
            <div className="error-msg">{error}</div>
          ) : (
            <>
              <RiskGauge probability={simResult.failure_probability} height={120} />
              
              <div className="risk-delta" style={{ color: deltaColor, fontWeight: 'bold', marginTop: '1rem', textAlign: 'center' }}>
                {delta === "0.0" ? "No Change in Risk" : `Risk Impact: ${deltaSign}${delta}%`}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ScenarioSimulator;

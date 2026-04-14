import { useState, useEffect } from "react";
import { fetchHealth } from "../api";

function HealthCard() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  const load = () => {
    fetchHealth()
      .then((data) => { setHealth(data); setError(null); })
      .catch((err) => setError(err.message));
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="card">
        <div className="card-title">API Health</div>
        <div className="health-status">
          <span className="status-dot degraded" />
          Offline
        </div>
        <div className="health-meta"><span>{error}</span></div>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="card">
        <div className="card-title">API Health</div>
        <div className="loading">Checking...</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">API Health</div>
      <div className="health-status">
        <span className={`status-dot ${health.status}`} />
        {health.status === "ok" ? "Healthy" : "Degraded"}
      </div>
      <div className="health-meta">
        <span>Model: {health.model_loaded ? "Loaded" : "Not loaded"}</span>
        <span>Uptime: {Math.round(health.uptime_seconds)}s</span>
        <span>Model: {health.model_name}</span>
      </div>
    </div>
  );
}

export default HealthCard;

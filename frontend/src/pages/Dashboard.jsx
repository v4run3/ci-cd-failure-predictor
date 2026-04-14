import { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import HealthCard from "../components/HealthCard";
import ModelInfoCard from "../components/ModelInfoCard";
import { fetchModelInfo } from "../api";

// Known feature importance ranking (from Random Forest on our synthetic data)
const FEATURE_IMPORTANCE = [
  { name: "test_fail_count", importance: 0.32 },
  { name: "test_fail_ratio", importance: 0.28 },
  { name: "test_pass_count", importance: 0.10 },
  { name: "build_duration", importance: 0.06 },
  { name: "num_files_changed", importance: 0.05 },
  { name: "lines_per_file", importance: 0.04 },
  { name: "total_lines_changed", importance: 0.03 },
  { name: "is_late_night", importance: 0.03 },
  { name: "branch_is_hotfix", importance: 0.02 },
  { name: "hour", importance: 0.02 },
];

const COLORS = [
  "#ef4444", "#f97316", "#f59e0b", "#eab308", "#84cc16",
  "#22c55e", "#14b8a6", "#06b6d4", "#3b82f6", "#8b5cf6",
];

function Dashboard({ predictions }) {
  const [featureNames, setFeatureNames] = useState([]);

  useEffect(() => {
    fetchModelInfo()
      .then((info) => setFeatureNames(info.feature_names || []))
      .catch(() => {});
  }, []);

  const totalPredictions = predictions.length;
  const failures = predictions.filter((p) => p.prediction === 1).length;
  const successes = totalPredictions - failures;

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>System overview and model performance</p>
      </div>

      <div className="card-grid">
        <HealthCard />
        <ModelInfoCard />
        <div className="card">
          <div className="card-title">Session Predictions</div>
          <div className="stat-number">{totalPredictions}</div>
          <div className="stat-label">
            {successes} success / {failures} failure
          </div>
        </div>
      </div>

      <div className="card chart-card">
        <div className="card-title">Feature Importance (Top 10)</div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={FEATURE_IMPORTANCE}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
          >
            <XAxis type="number" domain={[0, 0.4]} tick={{ fontSize: 12 }} />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 12, fill: "var(--text-secondary)" }}
              width={110}
            />
            <Tooltip
              formatter={(val) => `${(val * 100).toFixed(1)}%`}
              contentStyle={{
                background: "var(--bg-secondary)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                color: "var(--text-primary)",
              }}
              labelStyle={{ color: "var(--text-primary)" }}
              itemStyle={{ color: "var(--text-primary)" }}
            />
            <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
              {FEATURE_IMPORTANCE.map((_, i) => (
                <Cell key={i} fill={COLORS[i]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default Dashboard;

import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  ReferenceLine,
} from "recharts";

function History({ predictions }) {
  // Reversed so chart goes left-to-right chronologically
  const chartData = [...predictions]
    .reverse()
    .map((p, i) => ({
      index: i + 1,
      probability: p.failure_probability,
      label: p.label,
    }));

  return (
    <div>
      <div className="page-header">
        <h1>History</h1>
        <p>Past predictions stored in this browser session</p>
      </div>

      {predictions.length === 0 ? (
        <div className="card empty-state">
          No predictions yet. Go to the Predict page to make one.
        </div>
      ) : (
        <>
          <div className="card chart-card">
            <div className="card-title">Failure Probability Trend</div>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis
                  dataKey="index"
                  label={{ value: "Prediction #", position: "insideBottom", offset: -2, fontSize: 12 }}
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  domain={[0, 1]}
                  tick={{ fontSize: 12 }}
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                />
                <Tooltip
                  formatter={(val) => `${(val * 100).toFixed(1)}%`}
                  contentStyle={{
                    background: "var(--bg-secondary)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                  }}
                />
                <ReferenceLine y={0.35} stroke="var(--warning)" strokeDasharray="5 5" label="" />
                <ReferenceLine y={0.65} stroke="var(--danger)" strokeDasharray="5 5" label="" />
                <Line
                  type="monotone"
                  dataKey="probability"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  dot={{ r: 4, fill: "var(--accent)" }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="card" style={{ marginTop: "1.5rem", overflow: "auto" }}>
            <div className="card-title">Prediction Log ({predictions.length})</div>
            <table className="history-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Branch</th>
                  <th>Files</th>
                  <th>Fail Ratio</th>
                  <th>Prediction</th>
                  <th>Probability</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((p, i) => (
                  <tr key={i}>
                    <td>{new Date(p.timestamp).toLocaleTimeString()}</td>
                    <td>{p.branch_type}</td>
                    <td>{p.num_files_changed}</td>
                    <td>{(p.test_fail_ratio * 100).toFixed(1)}%</td>
                    <td>
                      <span className={`result-label ${p.label}`} style={{ fontSize: "0.85rem" }}>
                        {p.label}
                      </span>
                    </td>
                    <td>{(p.failure_probability * 100).toFixed(1)}%</td>
                    <td>
                      <span className={`risk-badge ${p.risk_level}`}>
                        {p.risk_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

export default History;

function RiskGauge({ probability = 0 }) {
  const size = 180;
  const strokeWidth = 16;
  const radius = (size - strokeWidth) / 2;
  const cx = size / 2;
  const cy = size / 2;

  // Semicircle from 180 to 0 degrees (left to right)
  const startAngle = Math.PI;
  const endAngle = 0;
  const totalArc = Math.PI;

  // Background arc (full semicircle)
  const bgX1 = cx + radius * Math.cos(startAngle);
  const bgY1 = cy - radius * Math.sin(startAngle);
  const bgX2 = cx + radius * Math.cos(endAngle);
  const bgY2 = cy - radius * Math.sin(endAngle);
  const bgPath = `M ${bgX1} ${bgY1} A ${radius} ${radius} 0 0 1 ${bgX2} ${bgY2}`;

  // Value arc
  const valueAngle = startAngle - probability * totalArc;
  const vX2 = cx + radius * Math.cos(valueAngle);
  const vY2 = cy - radius * Math.sin(valueAngle);
  const largeArc = probability > 0.5 ? 1 : 0;
  const valuePath =
    probability > 0.01
      ? `M ${bgX1} ${bgY1} A ${radius} ${radius} 0 ${largeArc} 1 ${vX2} ${vY2}`
      : "";

  // Color based on probability
  let color;
  if (probability < 0.35) color = "var(--success)";
  else if (probability < 0.65) color = "var(--warning)";
  else color = "var(--danger)";

  return (
    <div className="gauge-container">
      <svg width={size} height={size / 2 + 10} viewBox={`0 0 ${size} ${size / 2 + 10}`}>
        <path
          d={bgPath}
          fill="none"
          stroke="var(--gauge-bg)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        {valuePath && (
          <path
            d={valuePath}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            style={{
              transition: "all 0.6s ease-out",
              filter: `drop-shadow(0 0 6px ${color})`,
            }}
          />
        )}
        <text
          x={cx}
          y={cy - 5}
          textAnchor="middle"
          fontSize="28"
          fontWeight="700"
          fill="var(--text-primary)"
        >
          {(probability * 100).toFixed(1)}%
        </text>
        <text
          x={cx}
          y={cy + 12}
          textAnchor="middle"
          fontSize="10"
          fill="var(--text-secondary)"
        >
          Failure Probability
        </text>
      </svg>
    </div>
  );
}

export default RiskGauge;

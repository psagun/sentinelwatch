interface RiskGaugeProps {
  score: number;
  size?: number;
}

export default function RiskGauge({ score, size = 140 }: RiskGaugeProps) {
  const radius = size * 0.35;
  const circumference = radius * Math.PI;
  const progress = Math.min(score / 100, 1);
  const offset = circumference - progress * circumference;

  const color = score >= 70 ? '#EF4444' : score >= 40 ? '#F59E0B' : '#22C55E';
  const label = score >= 70 ? 'High Risk' : score >= 40 ? 'Medium Risk' : 'Low Risk';

  return (
    <div className="widget flex flex-col items-center justify-center h-full" style={{ minHeight: size + 40 }}>
      <h3 className="widget-title self-start mb-2">Risk Score</h3>
      <svg width={size} height={size * 0.55} viewBox={`0 0 ${size} ${size * 0.55}`} className="mb-1">
        <path
          d={`M ${size * 0.1} ${size * 0.5} A ${radius} ${radius} 0 0 1 ${size * 0.9} ${size * 0.5}`}
          fill="none"
          stroke="#1E2433"
          strokeWidth={8}
          strokeLinecap="round"
        />
        <path
          d={`M ${size * 0.1} ${size * 0.5} A ${radius} ${radius} 0 0 1 ${size * 0.9} ${size * 0.5}`}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.5s ease-out, stroke 0.5s' }}
        />
      </svg>
      <div className="text-center">
        <span className="stat-value" style={{ color }}>
          {score.toFixed(0)}
        </span>
        <span className="text-xs text-text-muted ml-1">/ 100</span>
        <p className="text-xs font-semibold mt-0.5" style={{ color }}>
          {label}
        </p>
      </div>
    </div>
  );
}

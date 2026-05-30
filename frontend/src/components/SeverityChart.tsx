import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface SeverityChartProps {
  data: { name: string; value: number; color: string }[];
}

export default function SeverityChart({ data }: SeverityChartProps) {
  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <div className="widget h-full">
      <div className="widget-header">
        <h3 className="widget-title">Severity Distribution</h3>
      </div>
      <div className="flex items-center gap-4 h-[calc(100%-32px)]">
        <div className="w-32 h-32 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={28}
                outerRadius={48}
                paddingAngle={2}
                dataKey="value"
                stroke="none"
              >
                {data.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: '#1A2035',
                  border: '1px solid #2A3348',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: '#E2E8F0',
                }}
                formatter={(value: number, name: string) => [`${value} findings`, name]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex-1 space-y-1.5">
          {data.map((entry) => {
            const pct = total > 0 ? ((entry.value / total) * 100).toFixed(1) : '0';
            return (
              <div key={entry.name} className="flex items-center gap-2 text-xs">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-text-secondary w-14">{entry.name}</span>
                <div className="flex-1 h-1.5 rounded-full bg-surface-200 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: entry.color,
                    }}
                  />
                </div>
                <span className="font-mono text-text-primary w-10 text-right">{entry.value}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

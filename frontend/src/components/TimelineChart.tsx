import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

interface TimelineChartProps {
  data: { date: string; critical: number; high: number; medium: number; low: number }[];
}

export default function TimelineChart({ data }: TimelineChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="widget">
        <div className="widget-header">
          <h3 className="widget-title">Finding Trends</h3>
        </div>
        <div className="h-[200px] flex items-center justify-center text-text-muted text-sm">
          No trend data available yet
        </div>
      </div>
    );
  }

  return (
    <div className="widget">
      <div className="widget-header">
        <h3 className="widget-title">Finding Trends</h3>
      </div>
      <div className="h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
            <defs>
              <linearGradient id="gradC" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#EF4444" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#EF4444" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradH" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#F97316" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#F97316" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradM" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#F59E0B" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gradL" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E2433" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#555E72' }}
              axisLine={{ stroke: '#1E2433' }}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 10, fill: '#555E72' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                background: '#1A2035',
                border: '1px solid #2A3348',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#E2E8F0',
              }}
            />
            <Area type="monotone" dataKey="critical" stroke="#EF4444" fill="url(#gradC)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="high" stroke="#F97316" fill="url(#gradH)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="medium" stroke="#F59E0B" fill="url(#gradM)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="low" stroke="#3B82F6" fill="url(#gradL)" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

import { useEffect, useRef, useState } from 'react';

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon?: React.ReactNode;
  color?: string;
  trend?: { value: number; positive: boolean };
  delay?: number;
  onClick?: () => void;
}

export default function StatCard({ title, value, subtitle, icon, color = '#22D3EE', trend, delay = 0, onClick }: StatCardProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const numericValue = typeof value === 'number' ? value : parseInt(value) || 0;
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (hasAnimated.current) return;
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true;
          const duration = 1200;
          const start = performance.now();
          const animate = (now: number) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            setDisplayValue(Math.round(eased * numericValue));
            if (progress < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.3 },
    );

    observer.observe(el);
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [numericValue]);

  useEffect(() => {
    hasAnimated.current = false;
    setDisplayValue(0);
  }, [value]);

  const prefix = typeof value === 'string' ? '' : '';
  const display = typeof value === 'number' ? displayValue.toLocaleString() : value;
  const finalDisplay = typeof value === 'number' ? display : value;

  return (
    <div
      ref={ref}
      className={`widget animate-fade-in ${onClick ? 'cursor-pointer hover:border-accent-cyan/30' : ''}`}
      style={{ animationDelay: `${delay}s` }}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="widget-title">{title}</span>
        {icon && (
          <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}15`, color }}>
            {icon}
          </div>
        )}
      </div>
      <div className="stat-value" style={{ color }}>
        {typeof value === 'string' ? value : display}
      </div>
      {(subtitle || trend) && (
        <div className="flex items-center gap-2 mt-1.5">
          {trend && (
            <span
              className={`text-xs font-semibold ${trend.positive ? 'text-accent-green' : 'text-accent-red'}`}
            >
              {trend.positive ? '↑' : '↓'} {Math.abs(trend.value)}%
            </span>
          )}
          {subtitle && <span className="text-xs text-text-muted">{subtitle}</span>}
        </div>
      )}
    </div>
  );
}

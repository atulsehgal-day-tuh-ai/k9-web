"use client";

import { useMemo } from "react";

function clamp01(x: number) {
  if (Number.isNaN(x)) return 0;
  return Math.max(0, Math.min(1, x));
}

function pathFromSeries(points: Array<{ x: number; y: number }>) {
  if (points.length === 0) return "";
  const [first, ...rest] = points;
  return ["M", first.x, first.y, ...rest.flatMap((p) => ["L", p.x, p.y])].join(" ");
}

export function TrajectoryChart({
  title,
  series,
  height = 180,
}: {
  title: string;
  series: Array<{ id: string; values: number[]; color: string }>;
  height?: number;
}) {
  const width = 560;
  const padding = 24;
  const innerW = width - padding * 2;
  const innerH = height - padding * 2;

  const normalized = useMemo(() => {
    const maxLen = Math.max(0, ...series.map((s) => s.values.length));
    const xStep = maxLen <= 1 ? innerW : innerW / (maxLen - 1);
    return series.map((s) => {
      const pts = s.values.map((v, i) => {
        const x = padding + i * xStep;
        const y = padding + (1 - clamp01(v)) * innerH;
        return { x, y };
      });
      return { ...s, pts };
    });
  }, [series, innerH, innerW, padding]);

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-zinc-900">{title}</div>
        <div className="flex gap-3">
          {series.map((s) => (
            <div key={s.id} className="flex items-center gap-1.5 text-xs text-zinc-600">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
              <span className="font-mono">{s.id}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-3 overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="min-w-[560px]">
          {/* grid */}
          {[0, 0.25, 0.5, 0.75, 1].map((v) => {
            const y = padding + (1 - v) * innerH;
            return (
              <g key={v}>
                <line x1={padding} x2={padding + innerW} y1={y} y2={y} stroke="#E4E4E7" strokeWidth="1" />
                <text x={4} y={y + 4} fontSize="10" fill="#71717A">
                  {(v * 100).toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* lines */}
          {normalized.map((s) => (
            <g key={s.id}>
              <path d={pathFromSeries(s.pts)} fill="none" stroke={s.color} strokeWidth="2.5" />
              {s.pts.map((p, i) => (
                <circle key={i} cx={p.x} cy={p.y} r="3" fill={s.color} />
              ))}
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}


import { useId, useState } from "react";
import type { ReplayEvent, ReplayMetric, ReplayRun } from "../domain/replay";
import {
  contiguousSegments,
  coverageLabels,
  coverageText,
  formatMetric,
  hasValue,
  metricDefinitions,
  timePosition,
  utcTime,
} from "../domain/replay";

const coverageColor = {
  complete: "#157347",
  partial: "#b77900",
  missing: "#98a2b3",
  invalid: "#b42318",
  not_applicable: "#8b7da8",
};

export function ReplayMetricPanel({
  definition,
  points,
  replay,
  events,
}: {
  definition: typeof metricDefinitions[number];
  points: ReplayMetric[];
  replay: ReplayRun;
  events: ReplayEvent[];
}) {
  const id = useId();
  const [focusIndex, setFocusIndex] = useState<number | null>(null);
  const valid = points.filter(hasValue);
  const latest = points.at(-1);
  const max = Math.max(...valid.map((point) => point.value), 0) * 1.12 || 1;
  const x = (time: string) => 40 + timePosition(time, replay.display_start_unix_nano, replay.display_end_unix_nano) * 548;
  const pointX = (point: ReplayMetric) => x(((BigInt(point.window_start_unix_nano) + BigInt(point.window_end_unix_nano)) / 2n).toString());
  const y = (point: ReplayMetric) => 204 - ((point.value ?? 0) / max) * 170;
  const active = focusIndex === null ? null : points[focusIndex];
  const noIncrement = points.filter((point) => point.reason === "no_observed_increment").length;
  const states = [...new Set(points.map((point) => point.coverage_state))];

  return (
    <section className="metric-panel replay-metric" aria-labelledby={id}>
      <h3 id={id}>{definition.title}</h3>
      <div className="replay-metric-summary">
        <p className="metric-value">
          {latest && hasValue(latest) ? `${formatMetric(latest.value, definition.decimals)} ${definition.unit}` : "—"}
        </p>
        <p className="small muted">
          Último intervalo{latest ? ` · ${utcTime(latest.window_start_unix_nano)}–${utcTime(latest.window_end_unix_nano)} UTC` : " indisponível"}
        </p>
        {latest && <p className={`small coverage-text ${latest.coverage_state}`}>{coverageText(latest)}</p>}
      </div>
      <p className="small muted">{definition.description}</p>
      {!points.length ? (
        <p className="replay-state muted">Nenhuma janela persistida para esta métrica.</p>
      ) : (
        <>
          <div
            className="replay-chart"
            tabIndex={0}
            role="img"
            aria-label={`${definition.title}. ${valid.length} de ${points.length} janelas com valor. ${noIncrement} sem incremento observado. Faixa âmbar: falha de CPU injetada. Use setas esquerda e direita para consultar intervalos; tabela de valores disponível abaixo.`}
            onFocus={() => setFocusIndex((index) => index ?? 0)}
            onBlur={() => setFocusIndex(null)}
            onKeyDown={(event) => {
              if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
              event.preventDefault();
              setFocusIndex((index) => Math.min(points.length - 1, Math.max(0, (index ?? 0) + (event.key === "ArrowRight" ? 1 : -1))));
            }}
            onMouseMove={(event) => {
              const bounds = event.currentTarget.getBoundingClientRect();
              const svgX = (event.clientX - bounds.left) / bounds.width * 600;
              let closest = 0;
              points.forEach((point, index) => {
                if (Math.abs(pointX(point) - svgX) < Math.abs(pointX(points[closest]) - svgX)) closest = index;
              });
              setFocusIndex(closest);
            }}
            onMouseLeave={() => setFocusIndex(null)}
          >
            <svg viewBox="0 0 600 264" aria-hidden="true">
              <defs><clipPath id={`${id}-clip`}><rect x="40" y="18" width="548" height="187" /></clipPath></defs>
              {[0, 0.5, 1].map((fraction) => (
                <g key={fraction}>
                  <line x1="40" x2="588" y1={204 - fraction * 170} y2={204 - fraction * 170} stroke="var(--border)" />
                  <text x="34" y={208 - fraction * 170} textAnchor="end">{formatMetric(max * fraction, 3)}</text>
                </g>
              ))}
              <g clipPath={`url(#${id}-clip)`}>
                {events.filter((event) => event.event_kind === "injected_fault").map((event) => (
                  <rect key={event.event_id} x={x(event.start_unix_nano)} y="18" width={Math.max(0, x(event.end_unix_nano) - x(event.start_unix_nano))} height="187" fill="#f5b842" opacity="0.16" />
                ))}
                {contiguousSegments(points).map((segment, index) => (
                  <g key={index}>
                    <polyline points={segment.map((point) => `${pointX(point)},${y(point)}`).join(" ")} fill="none" stroke="var(--blue)" strokeWidth="2" />
                    {segment.map((point) => (
                      <circle key={point.window_start_unix_nano} cx={pointX(point)} cy={y(point)} r={segment.length === 1 ? 3 : 1.8} fill="var(--blue)" />
                    ))}
                  </g>
                ))}
                {active && <line x1={pointX(active)} x2={pointX(active)} y1="18" y2="205" stroke="var(--muted)" strokeDasharray="3 3" />}
              </g>
              {points.map((point) => (
                <rect key={point.window_start_unix_nano} x={x(point.window_start_unix_nano)} y="218" width={Math.max(1, x(point.window_end_unix_nano) - x(point.window_start_unix_nano) - 0.5)} height="8" fill={coverageColor[point.coverage_state] ?? "#98a2b3"} />
              ))}
              {[0, 0.5, 1].map((fraction) => {
                const at = (BigInt(replay.display_start_unix_nano) + (BigInt(replay.display_end_unix_nano) - BigInt(replay.display_start_unix_nano)) * BigInt(fraction * 2) / 2n).toString();
                return <text key={fraction} x={40 + fraction * 548} y="252" textAnchor={fraction === 0 ? "start" : fraction === 1 ? "end" : "middle"}>{utcTime(at)}</text>;
              })}
            </svg>
            {active && (
              <div className="replay-chart-tooltip" role="tooltip">
                <strong>{utcTime(active.window_start_unix_nano)}–{utcTime(active.window_end_unix_nano)} UTC</strong>
                <span>{hasValue(active) ? `${formatMetric(active.value, definition.decimals)} ${definition.unit}` : "Valor não definido"}</span>
                <span>{coverageText(active)}</span>
              </div>
            )}
          </div>
          <div className="replay-coverage-legend small">
            <span><i className="event-swatch" /> Falha de CPU injetada</span>
            {states.map((state) => <span key={state}><i style={{ background: coverageColor[state] }} />{coverageLabels[state] ?? state}</span>)}
          </div>
          <p className="small muted">{valid.length}/{points.length} janelas com valor{noIncrement > 0 ? ` · ${noIncrement} sem incremento observado` : ""}. Lacunas e valores indefinidos interrompem a curva.</p>
        </>
      )}
    </section>
  );
}

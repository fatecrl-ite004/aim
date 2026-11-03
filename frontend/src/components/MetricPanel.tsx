import { useEffect, useRef, useState } from "react";
import {
  BASE_TIME,
  NORMALIZED_TIME,
  dateBRT,
  formatNumber,
  metrics,
} from "../domain/model";
import type { Service, State } from "../domain/model";
export type Period = "5 min" | "15 min" | "1 hora" | "24 horas";
export const periods: Period[] = ["5 min", "15 min", "1 hora", "24 horas"];
const minutes: Record<Period, number> = {
  "5 min": 5,
  "15 min": 15,
  "1 hora": 60,
  "24 horas": 1440,
};
export function MetricPanel({
  service,
  state,
  index,
  period,
}: {
  service: Service;
  state: State;
  index: number;
  period: Period;
}) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [fitsOriginalAsset, setFitsOriginalAsset] = useState(true);
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    const update = () => setFitsOriginalAsset(chart.clientWidth >= 484);
    update();
    const observer = new ResizeObserver(update);
    observer.observe(chart);
    return () => observer.disconnect();
  }, []);
  const [hover, setHover] = useState<number | null>(null),
    d = metrics(service, state.incident),
    normalized = ["normalized", "archived"].includes(state.incident),
    risk =
      state.incident === "active" &&
      ["checkout-service", "payment-worker", "api-gateway"].includes(
        service.id,
      );
  const title = [
    "Latência média e P99",
    "Conexões e pool de banco",
    "CPU",
    "Memória",
  ][index];
  const unit = ["ms", "conexões", "%", "GB"][index],
    values =
      index === 0
        ? [d.latency, d.p99]
        : index === 1
          ? [d.connections, d.pool]
          : index === 2
            ? [d.cpu]
            : [d.ram];
  const baselines =
    index === 0
      ? [service.latency, service.p99]
      : index === 1
        ? [service.connections, service.pool]
        : index === 2
          ? [service.cpu]
          : [service.ram];
  const max =
      index === 0 ? Math.ceil((d.p99 * 1.2) / 50) * 50 : index === 3 ? 2 : 100,
    wi = periods.indexOf(period);
  const series = values.map((end, j) =>
    normalized && service.id === "checkout-service" && index === 1
      ? j
        ? [92, 78 - wi * 2, 59, 41, 32]
        : [78, 64, 48, 32, 24]
      : risk
        ? [
            baselines[j],
            baselines[j] + (end - baselines[j]) * (0.15 + 0.06 * wi),
            baselines[j] + (end - baselines[j]) * (0.4 + 0.05 * wi),
            baselines[j] + (end - baselines[j]) * 0.78,
            end,
          ]
        : [
            end * (0.92 - 0.02 * wi),
            end * 0.99,
            end * (0.96 + 0.01 * wi),
            end * 1.02,
            end,
          ],
  );
  const clock = new Date(normalized ? NORMALIZED_TIME : BASE_TIME),
    time = (i: number) =>
      new Intl.DateTimeFormat("pt-BR", {
        timeZone: "America/Sao_Paulo",
        hour: "2-digit",
        minute: "2-digit",
      }).format(
        new Date(clock.getTime() - ((4 - i) * minutes[period] * 60000) / 4),
      );
  const current =
    index === 0
      ? `${d.latency} ms · P99 ${d.p99} ms`
      : index === 1
        ? `${d.connections} ativas · ${d.pool} / 100 no pool`
        : index === 2
          ? `${d.cpu}%`
          : `${formatNumber(d.ram)} GB`;
  const staticNames = ["8b2e9", "7c42e", "146c6", "0f367"];
  const asset =
    fitsOriginalAsset &&
    service.id === "checkout-service" &&
    period === "15 min" &&
    !risk
      ? normalized && index === 1
        ? "06a43"
        : staticNames[index]
      : null;
  return (
    <section className="metric-panel" aria-label={title}>
      <h3>{title}</h3>
      <p className="metric-value">{current}</p>
      <p className="small muted metric-legend">
        {
          [
            "— Média (azul)   -- P99 (âmbar) · ms",
            "— Ativas (azul)   -- Pool (âmbar) · conexões / capacidade 100",
            "— Utilização · %",
            "— Consumo · GB",
          ][index]
        }
      </p>
      <div
        ref={chartRef}
        className="chart"
        tabIndex={0}
        role="img"
        aria-label={`${title}: ${current}. Janela de ${period}.`}
        onFocus={() => setHover(4)}
        onBlur={() => setHover(null)}
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          setHover(
            Math.max(
              0,
              Math.min(
                4,
                Math.round(
                  ((e.clientX - rect.left - 36) / (rect.width - 36)) * 4,
                ),
              ),
            ),
          );
        }}
        onMouseLeave={() => setHover(null)}
      >
        <div className="chart-y">
          <span>{max}</span>
          <span>{max / 2}</span>
          <span>0</span>
        </div>
        <div className="chart-plot">
          {asset ? (
            <img
              src={`${import.meta.env.BASE_URL}assets/${asset}.svg`}
              width="448"
              height="140"
              alt=""
            />
          ) : (
            <svg
              viewBox="0 0 448 140"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              {[0, 70, 140].map((y) => (
                <line
                  key={y}
                  x1="0"
                  x2="448"
                  y1={y}
                  y2={y}
                  stroke="var(--border)"
                />
              ))}
              {series.map((line, j) => (
                <polyline
                  key={j}
                  points={line
                    .map(
                      (n, i) =>
                        `${i * 112},${140 - (Math.min(max, n) / max) * 140}`,
                    )
                    .join(" ")}
                  stroke={j ? "#d97706" : "#2563eb"}
                  fill="none"
                  strokeWidth="2.5"
                  strokeDasharray={j ? "6 4" : undefined}
                />
              ))}
            </svg>
          )}
        </div>
        {hover !== null && (
          <div className="chart-tooltip" role="tooltip">
            <strong>
              {time(hover)} BRT · {service.id}
            </strong>
            <span>
              {series
                .map(
                  (x, j) =>
                    (index === 0
                      ? j
                        ? "P99: "
                        : "Média: "
                      : index === 1
                        ? j
                          ? "Pool: "
                          : "Ativas: "
                        : "") +
                    formatNumber(x[hover]) +
                    " " +
                    unit,
                )
                .join(" · ")}
            </span>
          </div>
        )}
      </div>
      <div className="chart-x small muted">
        {[0, 1, 2, 3, 4].map((i) => (
          <span key={i}>{time(i)}</span>
        ))}
      </div>
      <span className="sr-only">
        Última amostra {dateBRT(clock.toISOString())}.
      </span>
    </section>
  );
}

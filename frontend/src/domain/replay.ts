export type UnixNano = string;
export type CoverageState =
  | "complete"
  | "partial"
  | "missing"
  | "invalid"
  | "not_applicable";

export interface ReplayRun {
  replay_run_id: string;
  source_name: string;
  case_id: string;
  status: string;
  display_start_unix_nano: UnixNano;
  display_end_unix_nano: UnixNano;
}
export interface ReplayService {
  service_id: string;
  service_name: string;
  instances: { instance_id: string; instance_name: string }[];
}
export interface TransformRun {
  transform_run_id: string;
  version: string;
  status: string;
  completed_at: string | null;
}
export type DemoRunStatus = "queued" | "running" | "completed" | "failed";
export interface DemoRun {
  demo_run_id: string;
  replay_run_id: string | null;
  status: DemoRunStatus;
  current_stage: string;
  total_chunks: number;
  completed_chunks: number;
  raw_point_count: number;
  expected_raw_point_count: number;
  latest_transform_run_id: string | null;
  latest_transform_60s_run_id: string | null;
  error_code: string | null;
  message: string | null;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  watermark_unix_nano?: UnixNano | null;
}
export interface ReplayMetric {
  metric_name: string;
  value: number | null;
  unit: string;
  window_start_unix_nano: UnixNano;
  window_end_unix_nano: UnixNano;
  coverage_state: CoverageState;
  reason: string | null;
}
export interface ReplayEvent {
  event_id: string;
  event_kind: "injected_fault";
  failure_type: string;
  start_unix_nano: UnixNano;
  end_unix_nano: UnixNano;
  instance_id: string;
  source_file_sha256: string;
  source_event_ordinal: number;
}
export interface MetricResponse {
  replay_run_id: string;
  transform_run_id: string;
  service_id: string;
  instance_id: string;
  metrics: ReplayMetric[];
}

export const metricDefinitions = [
  {
    name: "cpu_cores",
    title: "CPU média por intervalo",
    unit: "cores",
    description: "Δ CPU acumulada (s) / duração do intervalo (s).",
    decimals: 4,
  },
  {
    name: "success_response_rate",
    title: "Respostas bem-sucedidas por segundo",
    unit: "respostas/s",
    description: "Somente a série gRPC 0 / HTTP 200 selecionada.",
    decimals: 3,
  },
  {
    name: "success_latency_mean_ms",
    title: "Latência média das respostas 200",
    unit: "ms",
    description: "Δ duração acumulada / Δ respostas 200.",
    decimals: 3,
  },
] as const;

export const coverageLabels: Record<CoverageState, string> = {
  complete: "Completa",
  partial: "Parcial",
  missing: "Ausente",
  invalid: "Inválida",
  not_applicable: "Não aplicável",
};
const reasonLabels: Record<string, string> = {
  no_observed_increment: "Sem incremento observado",
  counter_reset: "Contador decrescente / reset",
  reset: "Contador decrescente / reset",
  gap: "Lacuna entre amostras",
  missing_point: "Amostra ausente",
  missing_series: "Série ausente",
  missing_baseline: "Sem amostra anterior",
  unmatched_timestamps: "Timestamps sem correspondência",
  source_series_missing: "Série de origem ausente",
  ambiguous_source_series: "Identidade da série ambígua",
  duplicate_timestamp: "Timestamp duplicado",
  missing_endpoint: "Amostra de um limite ausente",
  source_identity_changed: "Identidade alterada entre amostras",
  counter_start_changed: "Início do contador alterado",
  non_finite_or_negative_counter: "Contador inválido",
  counter_decreased: "Contador decrescente · intervalo inválido",
  invalid_interval: "Intervalo inválido",
  api_identity_mismatch: "Contagem e duração sem identidade comum",
  duration_without_responses: "Duração alterada sem respostas observadas",
};

export function coverageText(point: Pick<ReplayMetric, "coverage_state" | "reason">) {
  const label = coverageLabels[point.coverage_state] ?? point.coverage_state;
  return point.reason
    ? `${label} · ${reasonLabels[point.reason] ?? point.reason}`
    : label;
}

export function nanoDate(value: UnixNano): Date {
  return new Date(Number(BigInt(value) / 1_000_000n));
}

export function utcTime(value: UnixNano): string {
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "UTC",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(nanoDate(value));
}

export function utcDate(value: UnixNano): string {
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "UTC",
    dateStyle: "short",
  }).format(nanoDate(value));
}

export function formatMetric(value: number | null, decimals = 3): string {
  if (value === null || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("pt-BR", {
    maximumFractionDigits: decimals,
  }).format(value);
}

/** Convert only the small offset to Number; absolute nanoseconds stay exact. */
export function timePosition(value: UnixNano, start: UnixNano, end: UnixNano): number {
  const span = BigInt(end) - BigInt(start);
  if (span <= 0n) return 0;
  return Number(BigInt(value) - BigInt(start)) / Number(span);
}

export function metricPoints(metrics: ReplayMetric[], name: string): ReplayMetric[] {
  return metrics
    .filter((point) => point.metric_name === name)
    .sort((a, b) =>
      BigInt(a.window_start_unix_nano) < BigInt(b.window_start_unix_nano) ? -1 :
      BigInt(a.window_start_unix_nano) > BigInt(b.window_start_unix_nano) ? 1 : 0,
    );
}

export function hasValue(point: ReplayMetric): point is ReplayMetric & { value: number } {
  return (point.coverage_state === "complete" || point.coverage_state === "partial") &&
    point.value !== null && Number.isFinite(point.value);
}

/** A missing/invalid/no-traffic window breaks the curve, without imputing zeros. */
export function contiguousSegments(points: ReplayMetric[]): ReplayMetric[][] {
  const segments: ReplayMetric[][] = [];
  let segment: ReplayMetric[] = [];
  for (const point of points) {
    if (!hasValue(point)) {
      if (segment.length) segments.push(segment);
      segment = [];
      continue;
    }
    const previous = segment.at(-1);
    if (previous && previous.window_end_unix_nano !== point.window_start_unix_nano) {
      segments.push(segment);
      segment = [];
    }
    segment.push(point);
  }
  if (segment.length) segments.push(segment);
  return segments;
}

export function replayHref(replayId: string, serviceId: string, instanceId: string): string {
  return `#/replay/${encodeURIComponent(replayId)}/servico/${encodeURIComponent(serviceId)}?instancia=${encodeURIComponent(instanceId)}`;
}

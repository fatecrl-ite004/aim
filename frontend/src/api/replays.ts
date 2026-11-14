import type { DemoRun, MetricResponse, ReplayEvent, ReplayRun, ReplayService, TransformRun } from "../domain/replay";

const baseUrl = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

type JsonObject = Record<string, unknown>;
const object = (value: unknown): value is JsonObject => typeof value === "object" && value !== null && !Array.isArray(value);
const strings = (value: JsonObject, keys: string[]) => keys.every((key) => typeof value[key] === "string" && value[key] !== "");
const array = (value: unknown, check: (item: unknown) => boolean) => Array.isArray(value) && value.every(check);
const nano = (value: unknown): value is string => typeof value === "string" && /^\d{1,21}$/.test(value) && BigInt(value) < 253402300800000000000n;
const interval = (value: JsonObject, start: string, end: string) => nano(value[start]) && nano(value[end]) && BigInt(value[end] as string) > BigInt(value[start] as string);
const replayList = (value: unknown) => object(value) && array(value.replays, (run) => object(run) && strings(run, ["replay_run_id", "source_name", "case_id", "status"]) && interval(run, "display_start_unix_nano", "display_end_unix_nano"));
const serviceList = (value: unknown) => object(value) && array(value.services, (service) => object(service) && strings(service, ["service_id", "service_name"]) && array(service.instances, (instance) => object(instance) && strings(instance, ["instance_id", "instance_name"])));
const transformList = (value: unknown) => object(value) && (value.default_transform_run_id === null || typeof value.default_transform_run_id === "string") && array(value.transforms, (run) => object(run) && strings(run, ["transform_run_id", "version", "status"]) && (run.completed_at === null || typeof run.completed_at === "string"));
const eventList = (value: unknown) => object(value) && array(value.events, (event) => object(event) && strings(event, ["event_id", "failure_type", "instance_id", "source_file_sha256"]) && event.event_kind === "injected_fault" && interval(event, "start_unix_nano", "end_unix_nano") && typeof event.source_event_ordinal === "number");
const metricList = (value: unknown) => object(value) && strings(value, ["replay_run_id", "transform_run_id", "service_id", "instance_id"]) && array(value.metrics, (point) => object(point) && strings(point, ["metric_name", "unit", "coverage_state"]) && ["complete", "partial", "missing", "invalid", "not_applicable"].includes(point.coverage_state as string) && interval(point, "window_start_unix_nano", "window_end_unix_nano") && (point.value === null || typeof point.value === "number" && Number.isFinite(point.value)) && (point.reason === null || typeof point.reason === "string"));
const progressResult = (value: unknown) => object(value)
  && strings(value, ["replay_run_id", "service_id", "instance_id"])
  && Number.isInteger(value.raw_point_count) && (value.raw_point_count as number) >= 0
  && Number.isInteger(value.ingest_batch_count) && (value.ingest_batch_count as number) >= 0
  && (value.latest_source_timestamp_unix_nano === null || nano(value.latest_source_timestamp_unix_nano))
  && (value.latest_received_at === null || typeof value.latest_received_at === "string");
const demoRunResult = (value: unknown): value is DemoRun => object(value)
  && strings(value, ["demo_run_id", "status", "current_stage"])
  && ["queued", "running", "completed", "failed"].includes(value.status as string)
  && (value.replay_run_id === null || typeof value.replay_run_id === "string")
  && ["total_chunks", "completed_chunks", "raw_point_count", "expected_raw_point_count"]
    .every((key) => Number.isInteger(value[key]) && (value[key] as number) >= 0)
  && ["latest_transform_run_id", "latest_transform_60s_run_id", "error_code", "message", "created_at", "started_at", "completed_at"]
    .every((key) => value[key] === null || typeof value[key] === "string")
  && (value.watermark_unix_nano === undefined || value.watermark_unix_nano === null || nano(value.watermark_unix_nano));

async function read<T>(path: string, signal: AbortSignal, valid: (value: unknown) => boolean): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}/api/v1${path}`, {
      signal,
      headers: { Accept: "application/json" },
    });
  } catch (error) {
    if (signal.aborted) throw error;
    throw new Error("Não foi possível conectar à API. Verifique se o backend está em execução.");
  }
  if (!response.ok) {
    throw new Error(`A API não concluiu a consulta (HTTP ${response.status}).`);
  }
  try {
    const data: unknown = await response.json();
    if (!valid(data)) throw new Error("invalid_contract");
    return data as T;
  } catch {
    throw new Error("A API retornou uma resposta inválida para esta consulta.");
  }
}

export const replayApi = {
  list: (signal: AbortSignal) => read<{ replays: ReplayRun[] }>("/replays", signal, replayList),
  services: (id: string, signal: AbortSignal) =>
    read<{ services: ReplayService[] }>(`/replays/${encodeURIComponent(id)}/services`, signal, serviceList),
  transforms: (id: string, signal: AbortSignal) =>
    read<{ transforms: TransformRun[]; default_transform_run_id: string | null }>(
      `/replays/${encodeURIComponent(id)}/transforms`, signal, transformList,
    ),
  events: (id: string, signal: AbortSignal) =>
    read<{ events: ReplayEvent[] }>(`/replays/${encodeURIComponent(id)}/events`, signal, eventList),
  metrics: (
    replayId: string,
    serviceId: string,
    instanceId: string,
    transformId: string,
    from: string,
    to: string,
    signal: AbortSignal,
  ) => {
    const params = new URLSearchParams({
      instance_id: instanceId,
      transform_run_id: transformId,
      from_unix_nano: from,
      to_unix_nano: to,
    });
    return read<MetricResponse>(
      `/replays/${encodeURIComponent(replayId)}/services/${encodeURIComponent(serviceId)}/metrics?${params}`, signal, metricList,
    );
  },
  progress: (replayId: string, serviceId: string, instanceId: string, signal: AbortSignal) => {
    const params = new URLSearchParams({ instance_id: instanceId });
    return read<{
      replay_run_id: string; service_id: string; instance_id: string;
      raw_point_count: number; ingest_batch_count: number;
      latest_source_timestamp_unix_nano: string | null; latest_received_at: string | null;
    }>(`/replays/${encodeURIComponent(replayId)}/services/${encodeURIComponent(serviceId)}/progress?${params}`, signal, progressResult);
  },
  demoRun: (id: string, signal: AbortSignal) =>
    read<DemoRun>(`/demo-runs/${encodeURIComponent(id)}`, signal, demoRunResult),
  activeDemoRun: async (signal: AbortSignal) => {
    const value = await read<{ demo_run: DemoRun | null }>(
      "/demo-runs/active", signal,
      (result) => object(result) && (result.demo_run === null || demoRunResult(result.demo_run)),
    );
    return value.demo_run;
  },
  startDemoRun: async (idempotencyKey: string, signal: AbortSignal): Promise<DemoRun> => {
    let response: Response;
    try {
      response = await fetch(`${baseUrl}/api/v1/demo-runs`, {
        method: "POST",
        signal,
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "Idempotency-Key": idempotencyKey,
        },
        body: "{}",
      });
    } catch (error) {
      if (signal.aborted) throw error;
      throw new Error("Não foi possível iniciar a demonstração. Tente novamente para consultar a mesma solicitação.");
    }
    if (response.status === 409) {
      let activeId = "";
      try {
        const body: unknown = await response.json();
        if (object(body) && object(body.detail) && typeof body.detail.demo_run_id === "string") {
          activeId = body.detail.demo_run_id;
        }
      } catch {
        // The active endpoint below provides a second way to recover from a conflict response.
      }
      if (activeId) return replayApi.demoRun(activeId, signal);
      const active = await replayApi.activeDemoRun(signal);
      if (active) return active;
    }
    if (!response.ok) throw new Error(`A API não iniciou a demonstração (HTTP ${response.status}).`);
    try {
      const data: unknown = await response.json();
      if (!demoRunResult(data)) throw new Error("invalid_contract");
      return data;
    } catch {
      throw new Error("A API retornou uma resposta inválida para a demonstração.");
    }
  },
};

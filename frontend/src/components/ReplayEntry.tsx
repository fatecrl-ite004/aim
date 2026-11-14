import { useEffect, useRef, useState } from "react";
import { replayApi } from "../api/replays";
import type { DemoRun, ReplayRun, ReplayService } from "../domain/replay";
import { replayHref, utcDate, utcTime } from "../domain/replay";
import { Button } from "./ui";

const retryStorageKey = "aim.demo-run.idempotency-key";
const latestRunStorageKey = "aim.demo-run.latest-id";
const activeStatuses = new Set(["queued", "running"]);

function rememberDemoRun(run: DemoRun) {
  try { window.sessionStorage.setItem(latestRunStorageKey, run.demo_run_id); } catch { /* The in-memory status remains available. */ }
}

function demoStatusLabel(status: DemoRun["status"]) {
  if (status === "queued") return "Na fila";
  if (status === "running") return "Em andamento";
  if (status === "completed") return "Concluída";
  return "Falhou";
}

function stageLabel(stage: string) {
  const labels: Record<string, string> = {
    queued: "Na fila",
    loading_source: "Carregando fonte",
    sending: "Enviando amostras OTLP",
    transforming: "Transformando métricas",
    waiting: "Aguardando próximo lote",
    verifying: "Verificando persistência",
    importing_ground_truth: "Importando anotações da fonte",
    verifying_source: "Conferindo arquivos de origem",
    completed: "Concluída",
    failed: "Falhou",
    interrupted: "Interrompida",
  };
  return labels[stage] ?? stage;
}

export function ReplayEntry() {
  const [replays, setReplays] = useState<ReplayRun[]>([]);
  const [replayId, setReplayId] = useState("");
  const [targetReplayId, setTargetReplayId] = useState("");
  const [services, setServices] = useState<ReplayService[]>([]);
  const [servicesReplayId, setServicesReplayId] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingServices, setLoadingServices] = useState(false);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [demoRun, setDemoRun] = useState<DemoRun | null>(null);
  const [demoStarting, setDemoStarting] = useState(false);
  const [demoError, setDemoError] = useState("");
  const [demoStatusError, setDemoStatusError] = useState("");
  const [followingDemoRun, setFollowingDemoRun] = useState(false);
  const [retryKey, setRetryKey] = useState<string | null>(() => {
    try { return window.sessionStorage.getItem(retryStorageKey); } catch { return null; }
  });
  const retryKeyRef = useRef(retryKey);
  const startLock = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(!replays.length);
    setError("");
    replayApi.list(controller.signal).then(({ replays: runs }) => {
      setReplays(runs);
      setReplayId((previous) => {
        if (followingDemoRun && targetReplayId && runs.some((run) => run.replay_run_id === targetReplayId)) return targetReplayId;
        return runs.some((run) => run.replay_run_id === previous)
          ? previous : (runs.find((run) => run.status === "processed") ?? runs[0])?.replay_run_id ?? "";
      });
    }).catch((e: Error) => {
      if (!controller.signal.aborted) setError(e.message);
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });
    return () => controller.abort();
  }, [revision, targetReplayId, followingDemoRun]);

  useEffect(() => {
    const controller = new AbortController();
    let savedId: string | null = null;
    try { savedId = window.sessionStorage.getItem(latestRunStorageKey); } catch { /* Ignore unavailable session storage. */ }
    const activeRequest = replayApi.activeDemoRun(controller.signal);
    const savedRequest = savedId ? replayApi.demoRun(savedId, controller.signal) : Promise.resolve(null);
    Promise.allSettled([activeRequest, savedRequest]).then(([activeResult, savedResult]) => {
      if (controller.signal.aborted) return;
      const active = activeResult.status === "fulfilled" ? activeResult.value : null;
      const saved = savedResult.status === "fulfilled" ? savedResult.value : null;
      const run = active ?? saved;
      if (run) {
        rememberDemoRun(run);
        setDemoRun(run);
      }
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!demoRun || !activeStatuses.has(demoRun.status)) return;
    let active = true;
    let controller: AbortController | null = null;
    let timer: number | undefined;
    const poll = async () => {
      if (!active) return;
      const requestController = new AbortController();
      controller = requestController;
      try {
        const latest = await replayApi.demoRun(demoRun.demo_run_id, requestController.signal);
        if (active) {
          rememberDemoRun(latest);
          setDemoRun(latest);
          setDemoStatusError("");
        }
      } catch (e) {
        if (active && !requestController.signal.aborted) setDemoStatusError((e as Error).message);
      } finally {
        if (controller === requestController) controller = null;
        if (active) timer = window.setTimeout(() => void poll(), 1000);
      }
    };
    void poll();
    return () => {
      active = false;
      if (timer !== undefined) window.clearTimeout(timer);
      controller?.abort();
    };
  }, [demoRun?.demo_run_id, demoRun?.status]);

  useEffect(() => {
    const nextReplayId = demoRun?.replay_run_id;
    if (!nextReplayId) return;
    setTargetReplayId(nextReplayId);
    if (followingDemoRun) setReplayId(nextReplayId);
  }, [demoRun?.replay_run_id, followingDemoRun]);

  useEffect(() => {
    if (!replayId) return;
    const controller = new AbortController();
    setLoadingServices(true);
    setError("");
    replayApi.services(replayId, controller.signal).then(({ services: items }) => {
      setServices(items);
      setServicesReplayId(replayId);
    }).catch((e: Error) => {
      if (!controller.signal.aborted) setError(e.message);
    }).finally(() => {
      if (!controller.signal.aborted) setLoadingServices(false);
    });
    return () => controller.abort();
  }, [replayId, revision, demoRun?.status, demoRun?.latest_transform_run_id, demoRun?.latest_transform_60s_run_id]);

  useEffect(() => {
    const seriesReady = Boolean(demoRun?.latest_transform_run_id || demoRun?.latest_transform_60s_run_id);
    if (!followingDemoRun || (!seriesReady && demoRun?.status !== "completed") || !targetReplayId || replayId !== targetReplayId || servicesReplayId !== targetReplayId) return;
    const first = services.find((service) => service.instances.length > 0);
    const instance = first?.instances[0];
    if (first && instance) window.location.hash = replayHref(targetReplayId, first.service_id, instance.instance_id);
  }, [followingDemoRun, demoRun?.status, demoRun?.latest_transform_run_id, demoRun?.latest_transform_60s_run_id, targetReplayId, replayId, servicesReplayId, services]);

  const startOrFollowDemo = async () => {
    if (startLock.current) return;
    if (demoRun && activeStatuses.has(demoRun.status)) {
      setDemoError("");
      setFollowingDemoRun(true);
      if (demoRun.replay_run_id) {
        setTargetReplayId(demoRun.replay_run_id);
        setReplayId(demoRun.replay_run_id);
      }
      return;
    }
    startLock.current = true;
    const key = retryKeyRef.current ?? window.crypto.randomUUID();
    retryKeyRef.current = key;
    setRetryKey(key);
    try { window.sessionStorage.setItem(retryStorageKey, key); } catch { /* The in-memory key still protects this tab. */ }
    setDemoRun(null);
    setTargetReplayId("");
    setFollowingDemoRun(true);
    setDemoStarting(true);
    setDemoError("");
    setDemoStatusError("");
    try {
      const controller = new AbortController();
      const run = await replayApi.startDemoRun(key, controller.signal);
      rememberDemoRun(run);
      setDemoRun(run);
      retryKeyRef.current = null;
      setRetryKey(null);
      try { window.sessionStorage.removeItem(retryStorageKey); } catch { /* Ignore unavailable session storage. */ }
    } catch (e) {
      setDemoError((e as Error).message);
    } finally {
      startLock.current = false;
      setDemoStarting(false);
    }
  };

  const replay = replays.find((run) => run.replay_run_id === replayId);
  const demoActive = Boolean(demoRun && activeStatuses.has(demoRun.status));
  return (
    <section className="replay-entry stack" aria-labelledby="replay-entry-title" aria-busy={loading || loadingServices || demoStarting}>
      <div className="replay-section-heading">
        <div>
          <span className="source-badge connected">API + PostgreSQL</span>
          <h2 id="replay-entry-title">Replay histórico AIOpsArena</h2>
          <p className="muted">Consulte séries de origem recebidas por OTLP e transformadas no AIM após a persistência.</p>
        </div>
        <div className="replay-entry-actions">
          <Button tone="primary" disabled={demoStarting} onClick={() => void startOrFollowDemo()}>
            {demoStarting ? "Iniciando…" : demoActive ? "Acompanhar demonstração" : retryKey ? "Tentar novamente" : "Iniciar demonstração"}
          </Button>
          <Button disabled={loading} onClick={() => setRevision((n) => n + 1)}>{loading ? "Atualizando…" : "Atualizar replays"}</Button>
        </div>
      </div>

      {demoRun && <section className={`demo-run-status ${demoRun.status === "failed" ? "failed" : ""}`} aria-label="Status da demonstração" role="status" aria-live="off">
        <div className="demo-run-status-heading">
          <strong>Demonstração {demoStatusLabel(demoRun.status).toLowerCase()}</strong>
          <span>{demoRun.current_stage ? stageLabel(demoRun.current_stage) : demoStatusLabel(demoRun.status)}</span>
        </div>
        <div className="demo-run-status-counts">
          {demoRun.total_chunks > 0 && <span>{demoRun.completed_chunks.toLocaleString("pt-BR")} de {demoRun.total_chunks.toLocaleString("pt-BR")} lotes</span>}
          <span>{demoRun.raw_point_count.toLocaleString("pt-BR")} pontos OTLP persistidos{demoRun.expected_raw_point_count > 0 ? ` de ${demoRun.expected_raw_point_count.toLocaleString("pt-BR")}` : ""}</span>
          {demoRun.latest_transform_60s_run_id && <span>Transformação agregada persistida</span>}
          {demoRun.latest_transform_run_id && !demoRun.latest_transform_60s_run_id && <span>Transformação persistida</span>}
        </div>
        {demoRun.status === "failed" && <p className="small">{demoRun.message || demoRun.error_code || "A demonstração não foi concluída."}</p>}
        {demoStatusError && <p className="small" role="alert">Não foi possível atualizar o status. {demoStatusError}</p>}
        {demoRun.replay_run_id && demoRun.status === "completed" && <p className="small">{followingDemoRun ? "Replay salvo; abrindo quando houver séries disponíveis." : "Replay salvo no histórico."}</p>}
      </section>}
      {demoError && <div className="replay-state critical-text" role="alert"><strong>Não foi possível iniciar a demonstração</strong><p>{demoError}</p></div>}

      {!replays.length && loading ? (
        <p role="status">Consultando replays na API…</p>
      ) : !replays.length && error ? (
        <div className="replay-state critical-text" role="alert">
          <strong>Replay indisponível</strong>
          <p>{error}</p>
          <Button onClick={() => setRevision((n) => n + 1)}>Tentar novamente a consulta</Button>
        </div>
      ) : !replays.length ? (
        <div className="replay-state">
          <strong>Nenhum replay persistido</strong>
          <p className="muted">Inicie uma demonstração para receber o replay histórico do dataset.</p>
        </div>
      ) : (
        <>
          <label className="field replay-selector">
            Execução de replay
            <select value={replayId} onChange={(e) => { setFollowingDemoRun(false); setReplayId(e.target.value); }}>
              {replays.map((run) => (
                <option key={run.replay_run_id} value={run.replay_run_id}>
                  {run.source_name} · {run.case_id} · {run.replay_run_id.slice(0, 8)}
                </option>
              ))}
            </select>
          </label>
          {loading && <span className="small muted" role="status">Atualizando lista de replays…</span>}
          {error && <span className="small critical-text" role="alert">Falha ao atualizar a lista: {error}</span>}
          {replay && (
            <p className="small muted">
              {utcDate(replay.display_start_unix_nano)} · {utcTime(replay.display_start_unix_nano)}–{utcTime(replay.display_end_unix_nano)} UTC · Histórico
            </p>
          )}
          {loadingServices && servicesReplayId !== replayId ? <p role="status">Consultando instâncias persistidas…</p> : servicesReplayId === replayId && services.length ? (
            <div className="replay-service-grid">
              {services.flatMap((service) => service.instances.map((instance) => (
                <article key={`${service.service_id}/${instance.instance_id}`} className="replay-service-card">
                  <h3>{service.service_name}</h3>
                  <p className="muted">{instance.instance_name}</p>
                  <p className="small">CPU · respostas 200 · latência média</p>
                  <a className="button primary" href={replayHref(replayId, service.service_id, instance.instance_id)}>
                    Abrir replay histórico
                  </a>
                </article>
              )))}
            </div>
          ) : servicesReplayId === replayId ? (
            <p className="muted">Este replay ainda não possui séries de instâncias persistidas.</p>
          ) : null}
        </>
      )}
    </section>
  );
}

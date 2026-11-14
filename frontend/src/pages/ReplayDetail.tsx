import { useEffect, useState } from "react";
import { replayApi } from "../api/replays";
import { ReplayMetricPanel } from "../components/ReplayMetricPanel";
import { Banner, Button, EmptyState, PageHeading } from "../components/ui";
import type { ReplayEvent, ReplayMetric, ReplayRun, ReplayService, TransformRun } from "../domain/replay";
import { coverageText, formatMetric, hasValue, metricDefinitions, metricPoints, utcDate, utcTime } from "../domain/replay";

function replayExportUrl(kind: "raw" | "derived", replayId: string, serviceId: string, instanceId: string, from?: string, to?: string, transformId?: string) {
  const params = new URLSearchParams({ instance_id: instanceId });
  if (from && to) {
    params.set("from_unix_nano", from);
    params.set("to_unix_nano", to);
  }
  if (kind === "derived" && transformId) params.set("transform_run_id", transformId);
  const base = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
  return `${base}/api/v1/replays/${encodeURIComponent(replayId)}/services/${encodeURIComponent(serviceId)}/export/${kind}.csv?${params}`;
}

function transformCadence(version: string) {
  if (version === "counter-rates-60s-v1") return { label: "Agregada · 60 s", seconds: 60 };
  if (version === "counter-rates-v1") return { label: "Fiel · 15 s", seconds: 15 };
  return { label: "Cadência não identificada", seconds: null };
}

interface DetailData {
  replay: ReplayRun;
  service: ReplayService;
  instanceId: string;
  instanceName: string;
  transforms: TransformRun[];
  events: ReplayEvent[];
}

export function ReplayDetail({ replayId, serviceId, instanceId }: {
  replayId: string;
  serviceId: string;
  instanceId: string;
}) {
  const [data, setData] = useState<DetailData | null>(null);
  const [transformId, setTransformId] = useState("");
  const [metrics, setMetrics] = useState<ReplayMetric[]>([]);
  const [metricsTransformId, setMetricsTransformId] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [metricsConsultedAt, setMetricsConsultedAt] = useState<Date | null>(null);
  const [followIngestion, setFollowIngestion] = useState(true);
  const [followMessage, setFollowMessage] = useState("");
  const [ingestionProgress, setIngestionProgress] = useState<{
    raw_point_count: number; ingest_batch_count: number;
    latest_source_timestamp_unix_nano: string | null; latest_received_at: string | null;
  } | null>(null);
  const [error, setError] = useState("");
  const [metricError, setMetricError] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(!data);
    setRefreshing(true);
    setError("");
    Promise.all([
      replayApi.list(controller.signal),
      replayApi.services(replayId, controller.signal),
      replayApi.transforms(replayId, controller.signal),
      replayApi.events(replayId, controller.signal),
    ]).then(([runs, services, transforms, events]) => {
      const replay = runs.replays.find((run) => run.replay_run_id === replayId);
      const service = services.services.find((item) => item.service_id === serviceId);
      const instance = service?.instances.find((item) => item.instance_id === instanceId);
      if (!replay || !service || !instance) throw new Error("O replay, serviço ou instância solicitado não está disponível nesta execução.");
      setData({ replay, service, instanceId: instance.instance_id, instanceName: instance.instance_name, transforms: transforms.transforms, events: events.events.filter((event) => event.instance_id === instance.instance_id) });
      setTransformId((current) => transforms.transforms.some((run) => run.transform_run_id === current)
        ? current : transforms.default_transform_run_id ?? "");
    }).catch((e: Error) => {
      if (!controller.signal.aborted) setError(e.message);
    }).finally(() => {
      if (!controller.signal.aborted) {
        setLoading(false);
        setRefreshing(false);
      }
    });
    return () => controller.abort();
  }, [replayId, serviceId, instanceId, revision]);

  useEffect(() => {
    if (!data || !transformId) {
      setLoadingMetrics(false);
      return;
    }
    const controller = new AbortController();
    setLoadingMetrics(true);
    setMetricError("");
    const requestedTransformId = transformId;
    replayApi.metrics(replayId, serviceId, data.instanceId, requestedTransformId,
      data.replay.display_start_unix_nano, data.replay.display_end_unix_nano,
      controller.signal,
    ).then((response) => {
      if (response.replay_run_id !== replayId || response.transform_run_id !== requestedTransformId || response.service_id !== serviceId || response.instance_id !== data.instanceId) {
        throw new Error("A API retornou métricas de outra execução ou entidade. A consulta foi interrompida.");
      }
      setMetrics(response.metrics);
      setMetricsTransformId(requestedTransformId);
      setMetricsConsultedAt(new Date());
    }).catch((e: Error) => {
      if (!controller.signal.aborted) setMetricError(e.message);
    }).finally(() => {
      if (!controller.signal.aborted) setLoadingMetrics(false);
    });
    return () => controller.abort();
  }, [data?.instanceId, data?.replay.display_start_unix_nano, data?.replay.display_end_unix_nano, transformId, replayId, serviceId, revision]);

  useEffect(() => {
    if (!followIngestion || !data) return;
    let active = true;
    let controller: AbortController | null = null;
    let timer: number | undefined;
    const selectedVersion = data.transforms.find((run) => run.transform_run_id === transformId)?.version
      ?? data.transforms[0]?.version;
    const poll = async () => {
      if (!active) return;
      const requestController = new AbortController();
      controller = requestController;
      try {
        const [response, progress] = await Promise.all([
          replayApi.transforms(replayId, requestController.signal),
          replayApi.progress(replayId, serviceId, data.instanceId, requestController.signal),
        ]);
        if (!active) return;
        setIngestionProgress((previous) => previous
          && previous.raw_point_count === progress.raw_point_count
          && previous.ingest_batch_count === progress.ingest_batch_count
          && previous.latest_source_timestamp_unix_nano === progress.latest_source_timestamp_unix_nano
          && previous.latest_received_at === progress.latest_received_at
          ? previous : progress);
        setData((previous) => {
          if (!previous) return previous;
          const unchanged = previous.transforms.length === response.transforms.length
            && previous.transforms.every((run, index) => run.transform_run_id === response.transforms[index]?.transform_run_id
              && run.status === response.transforms[index]?.status
              && run.completed_at === response.transforms[index]?.completed_at);
          return unchanged ? previous : { ...previous, transforms: response.transforms };
        });
        const newest = response.transforms.find((run) => run.status === "completed" && run.version === selectedVersion)
          ?? (!selectedVersion ? response.transforms.find((run) => run.transform_run_id === response.default_transform_run_id) : undefined);
        if (newest && newest.transform_run_id !== transformId) {
          setTransformId(newest.transform_run_id);
          setFollowMessage(`Nova execução ${transformCadence(newest.version).label} persistida; atualizando as séries.`);
        }
      } catch {
        if (active && !requestController.signal.aborted) setFollowMessage("Não foi possível consultar o progresso agora; nova tentativa em instantes.");
      } finally {
        if (controller === requestController) controller = null;
        if (active) timer = window.setTimeout(() => void poll(), 2000);
      }
    };
    void poll();
    return () => {
      active = false;
      if (timer !== undefined) window.clearTimeout(timer);
      controller?.abort();
    };
  }, [followIngestion, data?.replay.replay_run_id, data?.instanceId, replayId, serviceId, transformId,
    data?.transforms.find((run) => run.transform_run_id === transformId)?.version ?? data?.transforms[0]?.version]);

  const transform = data?.transforms.find((run) => run.transform_run_id === transformId);
  const displayedTransform = data?.transforms.find((run) => run.transform_run_id === metricsTransformId) ?? transform;
  const selectedCadence = displayedTransform ? transformCadence(displayedTransform.version) : null;
  const pointGroups = metricDefinitions.map((definition) => metricPoints(metrics, definition.name));
  const intervals = [...new Set(metrics.map((point) => point.window_start_unix_nano))].sort((a, b) => BigInt(a) < BigInt(b) ? -1 : BigInt(a) > BigInt(b) ? 1 : 0);
  const problemCount = metrics.filter((point) => ["partial", "missing", "invalid"].includes(point.coverage_state)).length;
  const displayedTransformId = metricsTransformId || transformId;
  return (
    <div className="stack replay-detail" aria-busy={refreshing || loadingMetrics}>
      <PageHeading title="Replay histórico AIOpsArena">
        <a href="#/">Visão geral</a> / {data?.service.service_name ?? "Detalhe do serviço"}
      </PageHeading>
      <div className="actions replay-toolbar">
        <span className="source-badge connected">API + PostgreSQL</span>
        <span className="small muted">Séries persistidas · período histórico em UTC</span>
        <Button disabled={refreshing} onClick={() => setRevision((n) => n + 1)}>
          {refreshing ? "Atualizando…" : "Atualizar"}
        </Button>
      </div>
      {!data ? loading ? (
        <div className="replay-state" role="status">Carregando replay histórico…</div>
      ) : error ? (
        <EmptyState title="Não foi possível abrir o replay" action={<Button tone="primary" onClick={() => setRevision((n) => n + 1)}>Tentar novamente</Button>}>
          {error}
        </EmptyState>
      ) : null : (
        <>
          {error && <p className="replay-inline-error" role="alert">Atualização incompleta: {error}</p>}
          <section className="replay-context" aria-label="Contexto do replay">
            <div><span>Serviço / instância</span><strong>{data.service.service_name}</strong><p>{data.instanceName}</p></div>
            <div><span>Fonte / caso</span><strong>{data.replay.source_name} · {data.replay.case_id}</strong><p>Amostras métricas do dataset</p></div>
            <div><span>Período histórico</span><strong>{utcDate(data.replay.display_start_unix_nano)}</strong><p>[{utcTime(data.replay.display_start_unix_nano)}, {utcTime(data.replay.display_end_unix_nano)}) UTC</p></div>
          </section>
          {(followIngestion || followMessage || ingestionProgress) && <section className="replay-progress" aria-label="Chegada das métricas OTLP" role="status" aria-live="off">
            <div className="replay-progress-main">
              <strong>{ingestionProgress ? `${ingestionProgress.raw_point_count.toLocaleString("pt-BR")} pontos brutos persistidos` : "Consultando pontos persistidos"}</strong>
              <span className="small muted">{ingestionProgress ? `${ingestionProgress.ingest_batch_count.toLocaleString("pt-BR")} ${ingestionProgress.ingest_batch_count === 1 ? "lote" : "lotes"} OTLP` : "PostgreSQL"}
                {ingestionProgress?.latest_received_at ? ` · última recepção ${new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC", timeStyle: "medium" }).format(new Date(ingestionProgress.latest_received_at))} UTC` : ""}</span>
            </div>
            <span className={`replay-follow-status ${followIngestion ? "active" : ""}`}>
              {followIngestion ? "Acompanhando" : "Pausado"}
            </span>
          </section>}
          {followMessage && !followIngestion && <p className="small muted replay-follow-message" role="status">{followMessage}</p>}
          <details className="replay-method">
            <summary>Como as métricas são calculadas</summary>
            <p>CPU é a média em núcleos; respostas e latência usam os contadores de sucesso gRPC/HTTP 200. A transformação é determinística. A falha injetada é uma anotação da fonte; este replay não avalia detector nem prova causalidade.</p>
            <p>As amostras do arquivo estão em cadência de 15 s e os incrementos aparecem a cada 60 s. A versão de 15 s pode concentrar um delta acumulado em uma janela; a agregada combina quatro deltas contíguos antes de calcular a taxa por 60 s. Delta zero significa sem incremento observado no contador amostrado.</p>
          </details>
          <div className="replay-transform-row">
            <label className="field replay-selector">
              Execução de transformação
              <select value={transformId} disabled={!data.transforms.some((run) => run.status === "completed")} onChange={(e) => { setFollowIngestion(false); setFollowMessage("Acompanhamento pausado; transformação selecionada manualmente."); setTransformId(e.target.value); }}>
                {!transformId && <option value="">Nenhuma execução completa</option>}
                {data.transforms.filter((run) => run.status === "completed").map((run) => <option key={run.transform_run_id} value={run.transform_run_id}>{transformCadence(run.version).label} · {run.version} · {run.transform_run_id.slice(0, 8)}{run.completed_at ? ` · ${new Date(run.completed_at).toLocaleString("pt-BR", { timeZone: "UTC" })} UTC` : ""}</option>)}
              </select>
            </label>
            {transform && <p className="small muted">{transformCadence(transform.version).label} · versão {transform.version}</p>}
            {loadingMetrics && <span className="replay-updating" role="status">Atualizando séries…</span>}
            <Button aria-pressed={followIngestion} onClick={() => { const next = !followIngestion; setFollowIngestion(next); setFollowMessage(next ? "Acompanhando o progresso deste replay histórico…" : "Acompanhamento pausado."); }}>
              {followIngestion ? "Pausar acompanhamento" : "Acompanhar ingestão"}
            </Button>
          </div>
          {!transformId ? (
            <EmptyState title="Transformação ainda não executada">Os pontos de origem podem estar persistidos. Execute o processamento AIM para disponibilizar métricas derivadas.</EmptyState>
          ) : !metrics.length && loadingMetrics ? (
            <div className="replay-metric-placeholder" role="status">Consultando métricas persistidas…</div>
          ) : !metrics.length && metricError ? (
            <Banner tone="critical" title="Métricas indisponíveis">
              <p>{metricError}</p>
              <Button onClick={() => setRevision((n) => n + 1)}>Tentar novamente</Button>
            </Banner>
          ) : !metrics.length ? (
            <EmptyState title="Nenhuma janela derivada neste período">A execução selecionada não retornou valores nem estados de cobertura para o período histórico.</EmptyState>
          ) : (
            <>
              {metricError && <p className="replay-inline-error" role="alert">Falha ao atualizar as séries: {metricError}. Os valores exibidos continuam sendo da última consulta concluída.</p>}
              <section className="replay-series-heading" aria-label="Séries exibidas">
                <div><strong>{selectedCadence?.label ?? "Transformação selecionada"}</strong><span className="small muted">{intervals.length} {intervals.length === 1 ? "janela persistida" : "janelas persistidas"} · consulta concluída {metricsConsultedAt ? new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC", timeStyle: "short" }).format(metricsConsultedAt) + " UTC" : ""}</span></div>
                {metricsTransformId !== transformId && <span className="replay-updating">Exibindo resultado anterior</span>}
              </section>
              {problemCount > 0 && <Banner tone="attention" title="Atenção à cobertura das séries">Há {problemCount} observações parciais, ausentes ou inválidas. Consulte o motivo de cada janela; ausência não representa valor zero.</Banner>}
              <section className="actions replay-export" aria-label="Exportar CSV do replay">
                <span className="small muted">CSVs consultados do PostgreSQL · pontos brutos completos incluem aquecimento; derivadas cobrem o período exibido</span>
                <a className="button" href={replayExportUrl("raw", replayId, serviceId, data.instanceId)}>Exportar pontos brutos completos CSV</a>
                <a className="button" href={replayExportUrl("derived", replayId, serviceId, data.instanceId, data.replay.display_start_unix_nano, data.replay.display_end_unix_nano, displayedTransformId)}>Exportar métricas derivadas CSV</a>
              </section>
              <div className="replay-metrics-grid">
                {metricDefinitions.map((definition, index) => <ReplayMetricPanel key={definition.name} definition={definition} points={pointGroups[index]} replay={data.replay} events={data.events} />)}
              </div>
              <details className="replay-records">
                <summary>Consultar valores e cobertura por intervalo ({intervals.length} janelas)</summary>
                <p className="small muted">Intervalos [início, fim), em UTC. “—” significa valor não definido; zero aparece somente quando calculado a partir das amostras observadas.</p>
                <div className="table-wrap">
                  <table>
                    <caption className="sr-only">Valores derivados e cobertura da transformação selecionada</caption>
                    <thead><tr><th scope="col">Intervalo UTC</th>{metricDefinitions.map((definition) => <th scope="col" key={definition.name}>{definition.title} ({definition.unit})</th>)}</tr></thead>
                    <tbody>{intervals.map((start) => {
                      const first = metrics.find((point) => point.window_start_unix_nano === start)!;
                      return <tr key={start}><th scope="row">{utcTime(start)}–{utcTime(first.window_end_unix_nano)}</th>{metricDefinitions.map((definition, index) => {
                        const point = pointGroups[index].find((item) => item.window_start_unix_nano === start);
                        return <td key={definition.name}>{point ? <><strong>{hasValue(point) ? formatMetric(point.value, definition.decimals) : "—"}</strong><span className="replay-cell-coverage">{coverageText(point)}</span></> : <span>—<span className="replay-cell-coverage">Ausente · janela não retornada</span></span>}</td>;
                      })}</tr>;
                    })}</tbody>
                  </table>
                </div>
              </details>
            </>
          )}
          <section className="replay-event-section stack" aria-labelledby="replay-events-title">
            <div><h2 id="replay-events-title">Anotações da fonte</h2><p className="muted">Ground truth importado separadamente das métricas e das transformações.</p></div>
            {data.events.length ? data.events.map((event) => (
              <article key={event.event_id} className="replay-event">
                <span className="source-badge injected">Falha injetada</span>
                <h3>{event.failure_type === "cpu" ? "Falha de CPU injetada" : `Falha injetada: ${event.failure_type}`}</h3>
                <p>{event.instance_id} · {utcDate(event.start_unix_nano)} · [{utcTime(event.start_unix_nano)}, {utcTime(event.end_unix_nano)}) UTC</p>
                <p className="small muted">Intervenção anotada no dataset. Não representa alerta gerado pelo AIM ou impacto comprovado na API.</p>
              </article>
            )) : <p className="muted">Nenhuma anotação importada para esta instância.</p>}
          </section>
          <details className="replay-provenance">
            <summary>Identificadores e proveniência da consulta</summary>
            <dl><div><dt>Replay</dt><dd>{replayId}</dd></div><div><dt>Transformação exibida</dt><dd>{displayedTransformId || "Não executada"}</dd></div><div><dt>Serviço</dt><dd>{serviceId}</dd></div><div><dt>Instância</dt><dd>{data.instanceId}</dd></div></dl>
            {data.events.map((event) => <p key={event.event_id} className="small muted">Ground truth SHA-256: <code>{event.source_file_sha256}</code> · registro {event.source_event_ordinal}</p>)}
          </details>
        </>
      )}
    </div>
  );
}

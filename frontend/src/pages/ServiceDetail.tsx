import { useEffect, useState } from "react";
import { useStore } from "../state/Store";
import {
  BASE_TIME,
  NORMALIZED_TIME,
  dateBRT,
  monitoring,
  risk,
} from "../domain/model";
import { Banner, Button, EmptyState, PageHeading } from "../components/ui";
import type { Notify } from "../components/ui";
import { MetricPanel, periods } from "../components/MetricPanel";
import type { Period } from "../components/MetricPanel";
import { IncidentCard } from "../components/Incident";
export function ServiceDetail({ id, notify }: { id: string; notify: Notify }) {
  const { state, dispatch } = useStore(),
    service = state.services.find((x) => x.id === id),
    [period, setPeriod] = useState<Period>("15 min"),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(t);
  }, [id]);
  if (!service)
    return (
      <>
        <PageHeading title="Serviço não vinculado">
          O serviço pode ter sido desvinculado desta malha.
        </PageHeading>
        <EmptyState
          title="O histórico continua disponível"
          action={
            <a className="button primary" href="#/auditoria">
              Consultar auditoria
            </a>
          }
        >
          A desvinculação não interrompe a aplicação real.
        </EmptyState>
        <a className="button secondary" href="#/">
          Voltar à visão geral
        </a>
      </>
    );
  const active = monitoring(state, service),
    r = risk(state, service),
    normalized = state.incident === "normalized" && id === "checkout-service";
  return (
    <>
      <PageHeading title={service.id}>
        <a href="#/">Visão geral</a> / {service.id} · {service.runtime} · OTel
        conectado
      </PageHeading>
      <div className="stack">
        <Banner
          title={active ? "Monitoramento ativo" : "Ⅱ Monitoramento pausado"}
        >
          Última telemetria:{" "}
          {dateBRT(state.normalizedAt ? NORMALIZED_TIME : BASE_TIME)}
          {!active && " · Amostras congeladas; risco não avaliado."}
        </Banner>
        {state.incident === "active" &&
          ["checkout-service", "payment-worker", "api-gateway"].includes(
            id,
          ) && (
            <>
              {id !== "checkout-service" && (
                <Banner
                  tone="attention"
                  title="↳ Reflexo correlacionado ao INC-0042"
                >
                  Investigue as métricas e a topologia; a correlação não
                  determina causa raiz.
                </Banner>
              )}
              <IncidentCard />
            </>
          )}
        {normalized && (
          <>
            <Banner
              tone="success"
              title="✓ Incidente estabilizado — tendência normalizada"
            >
              INC-0042 · Normalização às 16:45:12 BRT. Estabilidade observada
              após mitigação externa pelo operador.
            </Banner>
            <div>
              <Button
                tone="primary"
                onClick={() => {
                  dispatch({ type: "archive" });
                  notify("INC-0042 arquivado. Supervisão silenciosa retomada.");
                  window.location.hash = "/";
                }}
              >
                Arquivar incidente
              </Button>
            </div>
          </>
        )}
        {state.dataStatus === "stale" && (
          <Banner tone="attention" title="◷ Telemetria desatualizada">
            Risco não avaliado. Os gráficos mostram as últimas amostras
            disponíveis.{" "}
            <Button
              onClick={() => dispatch({ type: "data-status", status: "ready" })}
            >
              Atualizar telemetria
            </Button>
          </Banner>
        )}
        <div className="periods" role="group" aria-label="Janela temporal">
          {periods.map((p) => (
            <Button
              key={p}
              tone={p === period ? "primary" : "secondary"}
              aria-pressed={p === period}
              onClick={() => setPeriod(p)}
            >
              {p}
            </Button>
          ))}
        </div>
        {loading || state.dataStatus === "loading" ? (
          <div
            className="metrics-grid"
            role="status"
            aria-label="Carregando métricas"
          >
            {[0, 1, 2, 3].map((i) => (
              <div className="metric-panel skeleton" key={i}>
                <div />
                <div />
                <div />
              </div>
            ))}
          </div>
        ) : state.dataStatus === "empty" ? (
          <EmptyState
            title="Ainda não há métricas neste período"
            action={
              <Button
                tone="primary"
                onClick={() => {
                  setLoading(true);
                  dispatch({ type: "data-status", status: "ready" });
                  setTimeout(() => setLoading(false), 500);
                }}
              >
                Buscar novos dados
              </Button>
            }
          >
            O serviço está conectado, mas não enviou amostras para a janela
            selecionada.
          </EmptyState>
        ) : (
          <div className="metrics-grid" data-risk={r}>
            {[0, 1, 2, 3].map((index) => (
              <MetricPanel
                key={index}
                index={index}
                state={state}
                service={service}
                period={period}
              />
            ))}
          </div>
        )}
        <div>
          <a className="button secondary" href="#/">
            Voltar à visão geral
          </a>
        </div>
      </div>
    </>
  );
}

import { useStore } from "../state/Store";
import { Banner, Button, EmptyState, PageHeading } from "../components/ui";
import { ServiceCard } from "../components/ServiceCard";
import { IncidentCard } from "../components/Incident";
export function Dashboard() {
  const { state, dispatch } = useStore();
  return (
    <>
      <PageHeading title="Visão geral da malha">
        Acompanhe sinais, reconheça riscos e investigue com contexto.
      </PageHeading>
      <div className="stack dashboard">
        {!state.services.length ? (
          <EmptyState
            title="Nenhum serviço cadastrado"
            action={
              <a className="button primary" href="#/servicos?novo=1">
                Cadastrar primeiro serviço
              </a>
            }
          >
            Vincule um serviço para começar a acompanhar a malha. O cadastro não
            altera a aplicação real.
          </EmptyState>
        ) : (
          <>
            {state.dataStatus === "stale" && (
              <Banner
                tone="attention"
                title="◷ Telemetria desatualizada — risco não avaliado"
              >
                As últimas amostras são mantidas para consulta.{" "}
                <Button
                  onClick={() =>
                    dispatch({ type: "data-status", status: "ready" })
                  }
                >
                  Atualizar telemetria
                </Button>
              </Banner>
            )}
            {state.dataStatus === "empty" && (
              <Banner tone="attention" title="Sem telemetria disponível">
                Conectividade não indica que já existem métricas.{" "}
                <Button
                  onClick={() =>
                    dispatch({ type: "data-status", status: "ready" })
                  }
                >
                  Buscar novos dados
                </Button>
              </Banner>
            )}
            {state.incident === "active" && <IncidentCard />}
            {state.incident === "normalized" && (
              <Banner
                tone="success"
                title="✓ INC-0042 normalizado — revisão pendente"
              >
                Tendência normalizada às 16:45:12 BRT.{" "}
                <a href="#/servico/checkout-service">
                  Revisar e arquivar incidente →
                </a>
              </Banner>
            )}
            {!state.globalPaused &&
              state.dataStatus === "ready" &&
              ["none", "archived"].includes(state.incident) && (
                <div className="banner nominal">
                  <strong>✓ Silêncio operacional — operação nominal</strong>
                  <div>
                    Serviços conectados · supervisão ativa · nenhum risco
                    sustentado identificado.
                  </div>
                </div>
              )}
            <h2>Serviços da malha</h2>
            <div className="service-grid">
              {state.services.map((s) => (
                <ServiceCard key={s.id} service={s} />
              ))}
            </div>
            <p className="small muted">
              Última telemetria: 08/10/2026 ·{" "}
              {state.normalizedAt ? "16:45:12" : "16:37:12"} BRT · Dados
              simulados
            </p>
          </>
        )}
      </div>
    </>
  );
}

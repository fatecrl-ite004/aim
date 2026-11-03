import { useState } from "react";
import { useStore } from "../state/Store";
import { canNormalize } from "../domain/model";
import { Banner, Button, Dialog } from "./ui";
export function IncidentCard() {
  const { state } = useStore(),
    [modal, setModal] = useState<"topology" | "logs" | null>(null);
  const fresh = canNormalize(state);
  return (
    <>
      <section className="incident-card">
        <h3>INC-0042 · Desvio sustentado detectado</h3>
        <div className="incident-facts">
          <div>
            <span>Origem do desvio</span>
            <strong>checkout-service</strong>
          </div>
          <div>
            <span>Métrica e divergência</span>
            <strong>Pool de conexões · +14%/min</strong>
          </div>
          <div>
            <span>Janela estimada de ação</span>
            <strong className="attention-text">
              {fresh
                ? state.estimateUpdated
                  ? "≈ 08 min 00 s"
                  : "≈ 08 min 30 s"
                : "Estimativa suspensa"}
            </strong>
          </div>
          <div>
            <span>Serviços afetados</span>
            <strong>payment-worker · api-gateway</strong>
          </div>
        </div>
        <p className="small muted">
          {fresh
            ? `Estimativa atualizada às ${state.estimateUpdated ? "16:37:12" : "16:36:42"} BRT · pode variar com novos sinais.`
            : "Sem avaliação atual. Retome o monitoramento e atualize a telemetria."}
        </p>
        <div className="actions">
          <Button onClick={() => setModal("topology")}>
            Ver topologia de impacto
          </Button>
          <Button tone="primary" onClick={() => setModal("logs")}>
            Acessar logs e traces
          </Button>
        </div>
      </section>
      {modal === "topology" && <Topology onClose={() => setModal(null)} />}{" "}
      {modal === "logs" && (
        <Dialog title="Logs e traces externos" onClose={() => setModal(null)}>
          <Banner title="Integração simulada">
            Em produção, esta ação abrirá a ferramenta de logs e traces
            configurada pelo operador.
          </Banner>
          <div className="log-preview">
            <p>
              <strong>Serviço:</strong> checkout-service
            </p>
            <p>
              <strong>Trace de exemplo:</strong>{" "}
              4bf92f3577b34da6a3ce929d0e0e4736
            </p>
            <pre>
              16:36:42 WARN pool.wait_time increased
              <br />
              16:37:12 INFO active=78 pool.used=92 capacity=100
            </pre>
          </div>
          <p className="muted">
            Estes sinais apoiam a investigação. Não determinam uma causa raiz.
          </p>
          <Button onClick={() => setModal(null)}>Voltar à triagem</Button>
        </Dialog>
      )}
    </>
  );
}
function Topology({ onClose }: { onClose: () => void }) {
  const [selected, setSelected] = useState("checkout-service");
  const symptoms: Record<string, string> = {
    "checkout-service":
      "Pool 92 / 100 · divergência +14%/min. Origem do desvio observado; não comprova causa raiz.",
    "payment-worker":
      "Latência média 96 ms · P99 168 ms. Sintoma correlacionado ao desvio em checkout-service.",
    "api-gateway":
      "Latência média 78 ms · P99 144 ms. Sintoma correlacionado ao desvio em checkout-service.",
  };
  return (
    <Dialog title="Topologia de impacto" onClose={onClose} wide>
      <p className="muted">
        checkout-service → dependentes com sinais de degradação · correlação
        OTel
      </p>
      <div className="topology-layout">
        <div className="topology-graph">
          <button
            className={`topology-node origin ${selected === "checkout-service" ? "selected" : ""}`}
            onClick={() => setSelected("checkout-service")}
            aria-pressed={selected === "checkout-service"}
          >
            <strong>checkout-service</strong>
            <span>▲ Origem do desvio</span>
          </button>
          <img
            className="topology-connectors"
            src={`${import.meta.env.BASE_URL}assets/64b6e.svg`}
            width="120"
            height="220"
            alt="Propagação direcional de checkout-service para payment-worker e api-gateway"
          />
          <div className="topology-dependents">
            {["payment-worker", "api-gateway"].map((s) => (
              <button
                key={s}
                className={`topology-node reflex ${selected === s ? "selected" : ""}`}
                aria-pressed={selected === s}
                onClick={() => setSelected(s)}
              >
                <strong>{s}</strong>
                <span>↳ Afetado por reflexo</span>
              </button>
            ))}
          </div>
        </div>
        <aside className="symptom-panel" aria-live="polite">
          <h3>
            {selected} —{" "}
            {selected === "checkout-service"
              ? "origem do desvio"
              : "reflexo correlacionado"}
          </h3>
          <p className="muted">{symptoms[selected]}</p>
        </aside>
      </div>
      <p className="small muted">
        ▲ Vermelho: origem do desvio　↳ Âmbar: reflexo　→ Direção da propagação
        correlacionada
      </p>
      <Button onClick={onClose}>Fechar topologia</Button>
    </Dialog>
  );
}

import { metrics, monitoring, risk } from "../domain/model";
import type { Service } from "../domain/model";
import { useStore } from "../state/Store";
import { Toggle } from "./ui";
export function ServiceCard({ service }: { service: Service }) {
  const { state, dispatch } = useStore(),
    m = metrics(service, state.incident),
    r = risk(state, service),
    active = monitoring(state, service);
  const labels = {
    unknown: "— Risco não avaliado",
    origin: "▲ Risco ativo · pool de conexões",
    reflex: "↳ Atenção · reflexo correlacionado",
    normal: "✓ Sem risco identificado",
  };
  return (
    <article
      className={`service-card risk-${r}`}
      onClick={(e) => {
        if (!(e.target as HTMLElement).closest("a,button"))
          window.location.hash = "/servico/" + encodeURIComponent(service.id);
      }}
    >
      <h3>
        <a href={`#/servico/${encodeURIComponent(service.id)}`}>{service.id}</a>
      </h3>
      <p className="small muted">{service.runtime} · Produção</p>
      <p className="service-latency">
        {state.dataStatus === "empty" ? "—" : `${m.latency} ms`}
      </p>
      <p className="small success-text">● Conectado · OTel</p>
      <p className="small muted">
        {active ? "● Monitoramento ativo" : "Ⅱ Monitoramento pausado"}
      </p>
      <p
        className={`small ${r === "origin" ? "critical-text" : r === "reflex" ? "attention-text" : "muted"}`}
      >
        {labels[r]}
      </p>
      <Toggle
        checked={!service.paused}
        disabled={state.globalPaused}
        ariaLabel={`${service.paused ? "Retomar" : "Pausar"} monitoramento de ${service.id}`}
        label={
          service.paused ? "Retomar monitoramento" : "Pausar monitoramento"
        }
        onChange={() => dispatch({ type: "service-toggle", id: service.id })}
      />
    </article>
  );
}

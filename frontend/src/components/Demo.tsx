import { useStore } from "../state/Store";
import { canNormalize } from "../domain/model";
import type { Scenario } from "../domain/model";
import { Button, Dialog } from "./ui";
import type { Notify } from "./ui";
export function Demo({
  onClose,
  notify,
}: {
  onClose: () => void;
  notify: Notify;
}) {
  const { state, dispatch } = useStore();
  const start = (scenario: Scenario, path = "/") => {
    dispatch({ type: "reset", scenario });
    window.location.hash = path;
    onClose();
    notify(
      "Demonstração reiniciada. Os dados anteriores foram substituídos pelos exemplos.",
    );
  };
  const exceptions: [Scenario, string, string][] = [
    ["empty", "Ausência de serviços", "/"],
    ["stale", "Telemetria desatualizada", "/"],
    ["no-data", "Métricas sem dados", "/servico/checkout-service"],
    ["endpoint-failure", "Endpoint indisponível", "/servicos?novo=1"],
    ["email-failure", "Falha no envio de teste", "/notificacoes"],
    ["no-recipients", "Nenhum destinatário ativo", "/notificacoes"],
    ["no-history", "Auditoria sem registros", "/auditoria"],
  ];
  return (
    <Dialog title="Demonstração do AIM" onClose={onClose}>
      <p className="muted">
        Escolha um modo para reiniciar os dados locais. Tudo acontece no
        navegador, sem acessar infraestrutura ou enviar e-mails.
      </p>
      <div className="demo-modes">
        <Button tone="primary" onClick={() => start("normal")}>
          Operação normal
        </Button>
        <Button onClick={() => start("incident")}>Incidente ativo</Button>
      </div>
      <div className="demo-normalize">
        <h3>Evolução do incidente</h3>
        <p className="muted">
          Após uma mitigação externa, simule a chegada de sinais normalizados e
          conclua o arquivamento.
        </p>
        <Button
          disabled={!canNormalize(state)}
          onClick={() => {
            dispatch({ type: "normalize" });
            window.location.hash = "/servico/checkout-service";
            onClose();
          }}
        >
          Simular sinais normalizados
        </Button>
        {!canNormalize(state) && (
          <p className="small muted">
            Requer incidente ativo, checkout-service vinculado, monitoramento
            ativo e telemetria atual.
          </p>
        )}
      </div>
      <details>
        <summary>Estados excepcionais</summary>
        <div className="exception-grid">
          {exceptions.map(([scenario, title, path]) => (
            <Button key={scenario} onClick={() => start(scenario, path)}>
              {title}
            </Button>
          ))}
        </div>
      </details>
      <p className="small muted">
        Para endpoint inválido ou e-mail duplicado, use os próprios formulários.
        A verificação de conectividade e o envio de teste usam respostas
        predefinidas.
      </p>
    </Dialog>
  );
}

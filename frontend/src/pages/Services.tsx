import { useEffect, useRef, useState } from "react";
import { useStore } from "../state/Store";
import { endpointValid, monitoring } from "../domain/model";
import type { Service } from "../domain/model";
import {
  Banner,
  Button,
  Dialog,
  EmptyState,
  PageHeading,
  SettingsTabs,
} from "../components/ui";
import type { Notify } from "../components/ui";
export function Services({
  notify,
  openNew = false,
}: {
  notify: Notify;
  openNew?: boolean;
}) {
  const { state, dispatch } = useStore(),
    [drawer, setDrawer] = useState(openNew),
    [menu, setMenu] = useState<string | null>(null),
    [unlink, setUnlink] = useState<Service | null>(null);
  return (
    <>
      <PageHeading title="Configurações — Serviços">
        Gerencie contratos de observabilidade. Nenhuma operação altera o runtime
        dos serviços.
      </PageHeading>
      <div className="stack">
        <div className="actions">
          <SettingsTabs active="services" />
          <Button tone="primary" onClick={() => setDrawer(true)}>
            + Novo serviço
          </Button>
        </div>
        {!state.services.length ? (
          <EmptyState
            title="Nenhum serviço vinculado"
            action={
              <Button tone="primary" onClick={() => setDrawer(true)}>
                Cadastrar serviço
              </Button>
            }
          >
            Adicione identificador, runtime e endpoint OTel para iniciar a
            supervisão.
          </EmptyState>
        ) : (
          <div className="table-wrap service-table">
            <table>
              <thead>
                <tr>
                  {[
                    "Identificador",
                    "Runtime",
                    "Conectividade",
                    "Monitoramento",
                    "Ações",
                  ].map((h) => (
                    <th key={h} scope="col">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {state.services.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <a href={`#/servico/${encodeURIComponent(s.id)}`}>
                        {s.id}
                      </a>
                    </td>
                    <td>{s.runtime}</td>
                    <td>
                      <span className="success-text">● Conectado</span>
                    </td>
                    <td>
                      {monitoring(state, s)
                        ? "● Monitoramento ativo"
                        : "Ⅱ Monitoramento pausado"}
                    </td>
                    <td className="menu-cell">
                      <div
                        className="menu-anchor"
                        onBlur={(e) => {
                          if (
                            !e.currentTarget.contains(e.relatedTarget as Node)
                          )
                            setMenu(null);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Escape") setMenu(null);
                        }}
                      >
                        <Button
                          tone="quiet"
                          aria-label={`Ações de ${s.id}`}
                          aria-expanded={menu === s.id}
                          aria-haspopup="menu"
                          onClick={() => setMenu(menu === s.id ? null : s.id)}
                        >
                          ⋮
                        </Button>
                        {menu === s.id && (
                          <div className="menu" role="menu">
                            <a
                              role="menuitem"
                              href={`#/servico/${encodeURIComponent(s.id)}`}
                            >
                              Ver métricas
                            </a>
                            <button
                              role="menuitem"
                              disabled={state.globalPaused}
                              onClick={() => {
                                dispatch({ type: "service-toggle", id: s.id });
                                setMenu(null);
                              }}
                            >
                              {s.paused ? "Retomar" : "Pausar"} monitoramento
                            </button>
                            <button
                              role="menuitem"
                              className="critical-text"
                              onClick={() => {
                                setUnlink(s);
                                setMenu(null);
                              }}
                            >
                              Desvincular serviço
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {drawer && (
        <NewService onClose={() => setDrawer(false)} notify={notify} />
      )}
      {unlink && (
        <Dialog
          title={`Desvincular ${unlink.id}?`}
          onClose={() => setUnlink(null)}
        >
          <p>
            O AIM interromperá a ingestão de telemetria deste canal.{" "}
            <strong>
              Os registros e métricas históricos serão preservados.
            </strong>
          </p>
          <p>O serviço real continuará funcionando no cluster.</p>
          <div className="actions">
            <Button
              tone="danger"
              onClick={() => {
                dispatch({ type: "service-remove", id: unlink.id });
                setUnlink(null);
                notify(
                  "Serviço desvinculado. Histórico preservado; a aplicação real continua funcionando.",
                );
              }}
            >
              Confirmar desvinculação
            </Button>
            <Button onClick={() => setUnlink(null)}>Cancelar</Button>
          </div>
        </Dialog>
      )}
    </>
  );
}
function NewService({
  onClose,
  notify,
}: {
  onClose: () => void;
  notify: Notify;
}) {
  const { state, dispatch } = useStore(),
    [id, setId] = useState(""),
    [runtime, setRuntime] = useState("Python 3.12"),
    [endpoint, setEndpoint] = useState(""),
    [errors, setErrors] = useState<Record<string, string>>({}),
    [stage, setStage] = useState<"edit" | "verifying" | "failed">("edit"),
    timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  function submit() {
    const next: Record<string, string> = {};
    if (!/^[a-z0-9][a-z0-9._-]{1,79}$/.test(id))
      next.id =
        "Use de 2 a 80 caracteres: letras minúsculas, números, ponto, hífen ou sublinhado.";
    if (state.services.some((s) => s.id === id))
      next.id = "Este identificador já está vinculado.";
    if (!endpointValid(endpoint))
      next.endpoint = "Informe uma URI HTTP, HTTPS, gRPC ou gRPCS válida.";
    setErrors(next);
    if (Object.keys(next).length) return;
    const retry = stage === "failed";
    setStage("verifying");
    timer.current = setTimeout(() => {
      if (
        !retry &&
        (state.endpointFails || endpoint.includes("indisponivel"))
      ) {
        setStage("failed");
        return;
      }
      dispatch({
        type: "service-add",
        service: {
          id,
          runtime,
          endpoint,
          paused: false,
          latency: 28,
          p99: 52,
          connections: 14,
          pool: 22,
          cpu: 20,
          ram: 0.5,
        },
      });
      notify(`${id} cadastrado. Endpoint OTel conectado — resposta simulada.`);
      onClose();
    }, 1200);
  }
  return (
    <Dialog title="Novo serviço" onClose={onClose} drawer>
      <p className="muted">
        Cadastre o contrato OTel. O AIM registra metadados e verifica a
        conectividade sem injetar agentes.
      </p>
      <form
        className="stack"
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <label className="field">
          Identificador do serviço
          <input
            aria-label="Identificador do serviço"
            autoFocus
            value={id}
            maxLength={80}
            disabled={stage === "verifying"}
            placeholder="ex.: inventory-service"
            aria-invalid={!!errors.id}
            aria-describedby={errors.id ? "service-id-error" : undefined}
            onChange={(e) => {
              setId(e.target.value);
              setErrors((x) => ({ ...x, id: "" }));
            }}
          />
          {errors.id && (
            <span className="field-error" id="service-id-error">
              {errors.id}
            </span>
          )}
        </label>
        <label className="field">
          Tecnologia / runtime
          <select
            value={runtime}
            disabled={stage === "verifying"}
            onChange={(e) => setRuntime(e.target.value)}
          >
            {[".NET 8", "Node.js 22", "Go 1.23", "Python 3.12", "Java 21"].map(
              (x) => (
                <option key={x}>{x}</option>
              ),
            )}
          </select>
        </label>
        <label className="field">
          Endpoint OTel
          <input
            aria-label="Endpoint OTel"
            value={endpoint}
            disabled={stage === "verifying"}
            placeholder="http://otel-collector:4317"
            aria-invalid={!!errors.endpoint}
            aria-describedby={errors.endpoint ? "endpoint-error" : undefined}
            onChange={(e) => {
              setEndpoint(e.target.value);
              setStage("edit");
              setErrors((x) => ({ ...x, endpoint: "" }));
            }}
          />
          {errors.endpoint && (
            <span className="field-error" id="endpoint-error">
              {errors.endpoint}
            </span>
          )}
        </label>
        <p className="small muted">
          OTel aceita URI HTTP ou gRPC. Esta demonstração não realiza
          requisições ao endpoint informado.
        </p>
        {stage === "failed" && (
          <Banner tone="critical" title="Endpoint indisponível">
            Não foi possível verificar a conectividade. Revise o endereço ou
            tente novamente. A próxima tentativa simula recuperação.
          </Banner>
        )}
        {stage === "verifying" && (
          <Banner title="Verificando conectividade…">
            Healthcheck passivo simulado · 1,2 segundo.
          </Banner>
        )}
        <Button type="submit" tone="primary" disabled={stage === "verifying"}>
          {stage === "verifying"
            ? "Verificando…"
            : stage === "failed"
              ? "Tentar novamente"
              : "Salvar contrato"}
        </Button>
        <Button onClick={onClose}>Cancelar</Button>
        <Button
          tone="quiet"
          disabled={stage === "verifying"}
          onClick={() => {
            setId("inventory-service");
            setRuntime("Python 3.12");
            setEndpoint("http://otel-collector:4317");
            setErrors({});
            setStage("edit");
          }}
        >
          Preencher exemplo
        </Button>
      </form>
    </Dialog>
  );
}

import { useEffect, useRef, useState } from "react";
import { useStore } from "../state/Store";
import { emailValid } from "../domain/model";
import {
  Banner,
  Button,
  EmptyState,
  PageHeading,
  SettingsTabs,
  Toggle,
} from "../components/ui";
import type { Notify } from "../components/ui";
export function Notifications({ notify }: { notify: Notify }) {
  const { state, dispatch } = useStore(),
    [email, setEmail] = useState(""),
    [error, setError] = useState(""),
    [sending, setSending] = useState(false),
    [failed, setFailed] = useState(false),
    [recovered, setRecovered] = useState(false),
    timer = useRef<ReturnType<typeof setTimeout> | null>(null),
    hasActive = state.recipients.some((r) => r.active);
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  function add() {
    const clean = email.trim().toLowerCase();
    if (!emailValid(clean)) {
      setError("Informe um endereço de e-mail válido.");
      return;
    }
    if (state.recipients.some((r) => r.email === clean)) {
      setError("Este endereço já está na lista de destinatários.");
      return;
    }
    dispatch({ type: "recipient-add", email: clean });
    setEmail("");
    setError("");
    notify("Destinatário adicionado.");
  }
  function send() {
    if (!hasActive) return;
    const retry = failed;
    setFailed(false);
    setSending(true);
    timer.current = setTimeout(() => {
      setSending(false);
      if (state.emailFails && !retry && !recovered) {
        setFailed(true);
        notify("Falha no envio do e-mail de teste.", "critical");
      } else {
        setRecovered(true);
        notify(
          "E-mail de teste enviado aos destinatários ativos — resposta simulada.",
        );
      }
    }, 1000);
  }
  return (
    <>
      <PageHeading title="Configurações — Notificações">
        Gerencie os destinatários de alertas. O teste usa uma resposta
        predefinida.
      </PageHeading>
      <div className="stack">
        <SettingsTabs active="notifications" />
        <h2>Destinatários de alerta</h2>
        <form
          className="recipient-form"
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            add();
          }}
        >
          <label className="field">
            E-mail do destinatário
            <input
              aria-label="E-mail do destinatário"
              type="email"
              value={email}
              autoComplete="email"
              placeholder="nome@empresa.com"
              aria-invalid={!!error}
              aria-describedby={error ? "email-error" : undefined}
              onChange={(e) => {
                setEmail(e.target.value);
                setError("");
              }}
            />
            {error && (
              <span className="field-error" id="email-error">
                {error}
              </span>
            )}
          </label>
          <Button type="submit" tone="primary" disabled={sending}>
            Adicionar
          </Button>
        </form>
        {!hasActive && (
          <Banner tone="attention" title="Nenhum destinatário ativo">
            Adicione ou ative pelo menos um destinatário para enviar o teste.
          </Banner>
        )}
        {!state.recipients.length ? (
          <EmptyState title="Nenhum destinatário cadastrado">
            Adicione um e-mail acima para receber alertas do AIM.
          </EmptyState>
        ) : (
          <ul className="recipient-list">
            {state.recipients.map((r) => (
              <li className="recipient" key={r.email}>
                <span className="recipient-email">{r.email}</span>
                <Toggle
                  checked={r.active}
                  disabled={sending}
                  label={r.active ? "Recebimento ativo" : "Recebimento pausado"}
                  ariaLabel={`Recebimento de ${r.email}`}
                  onChange={() => {
                    dispatch({ type: "recipient-toggle", email: r.email });
                    setFailed(false);
                  }}
                />
                <Button
                  disabled={sending}
                  aria-label={`Remover ${r.email}`}
                  onClick={() => {
                    dispatch({ type: "recipient-remove", email: r.email });
                    setFailed(false);
                    notify("Destinatário removido.");
                  }}
                >
                  Remover
                </Button>
              </li>
            ))}
          </ul>
        )}
        {sending && (
          <Banner title="Enviando e-mail de teste…">
            Os destinatários ativos foram selecionados. Nenhum e-mail real será
            enviado.
          </Banner>
        )}
        {failed && (
          <Banner tone="critical" title="Falha no envio do teste">
            O envio simulado não foi concluído. Tente novamente.
          </Banner>
        )}
        <div>
          <Button
            tone="primary"
            disabled={!hasActive || sending}
            onClick={send}
          >
            {sending
              ? "Enviando…"
              : failed
                ? "Tentar enviar novamente"
                : "Disparar e-mail de teste"}
          </Button>
        </div>
      </div>
    </>
  );
}

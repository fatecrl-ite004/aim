import { useState } from "react";
import { useStore } from "../state/Store";
import {
  auditValues,
  columns,
  defaultFilters,
  downloadAudit,
  filterAudit,
} from "../domain/audit";
import type { Filters } from "../domain/audit";
import { Banner, Button, EmptyState, PageHeading } from "../components/ui";
import type { Notify } from "../components/ui";
export function Audit({ notify }: { notify: Notify }) {
  const { state } = useStore(),
    [draft, setDraft] = useState<Filters>(defaultFilters),
    [filters, setFilters] = useState<Filters>(defaultFilters),
    [error, setError] = useState(""),
    [exporting, setExporting] = useState(false),
    rows = filterAudit(state.audit, filters),
    services = [
      ...new Set([
        ...state.services.map((s) => s.id),
        ...state.audit.map((r) => r.service),
      ]),
    ];
  function change(key: keyof Filters, value: string) {
    setDraft({ ...draft, [key]: value });
    setError("");
  }
  function clear() {
    setDraft(defaultFilters);
    setFilters(defaultFilters);
    setError("");
  }
  function exportFile(format: "csv" | "json") {
    setExporting(true);
    try {
      downloadAudit(rows, format);
      notify(
        `Exportação ${format.toUpperCase()} concluída: ${rows.length} registro(s).`,
      );
    } catch {
      notify("Não foi possível gerar o arquivo. Tente novamente.", "critical");
    } finally {
      setTimeout(() => setExporting(false), 300);
    }
  }
  return (
    <>
      <PageHeading title="Auditoria e testes">
        Rastreabilidade experimental · Histórico preservado · Horários em BRT
        (UTC−03)
      </PageHeading>
      <div className="stack">
        <form
          className="audit-filters"
          onSubmit={(e) => {
            e.preventDefault();
            if (draft.from && draft.to && draft.from > draft.to) {
              setError("A data inicial deve ser anterior ou igual à final.");
              return;
            }
            setFilters({ ...draft });
          }}
        >
          <label className="field">
            De
            <input
              type="date"
              value={draft.from}
              onChange={(e) => change("from", e.target.value)}
            />
          </label>
          <label className="field">
            Até
            <input
              type="date"
              value={draft.to}
              onChange={(e) => change("to", e.target.value)}
            />
          </label>
          <label className="field">
            Serviço
            <select
              aria-label="Serviço"
              value={draft.service}
              onChange={(e) => change("service", e.target.value)}
            >
              <option value="all">Todos os serviços</option>
              {services.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Tipo de anomalia
            <select
              aria-label="Tipo de anomalia"
              value={draft.type}
              onChange={(e) => change("type", e.target.value)}
            >
              <option value="all">Todos os tipos</option>
              <option value="pool">Pool de conexões</option>
              <option value="cpu">CPU</option>
            </select>
          </label>
          <Button type="submit">Aplicar filtros</Button>
          <Button tone="quiet" onClick={clear}>
            Limpar
          </Button>
        </form>
        {error && (
          <p className="field-error" role="alert">
            {error}
          </p>
        )}
        <Banner title="Definições experimentais a confirmar">
          A fonte associa MTTA à antecedência, mas não define o marco de
          impacto. MTTR também não possui marco inicial explícito. Campos
          preservados; cálculos não inferidos.
        </Banner>
        <div className="actions">
          <Button
            tone="primary"
            disabled={exporting || !rows.length}
            onClick={() => exportFile("csv")}
          >
            {exporting ? "Exportando…" : "Exportar CSV"}
          </Button>
          <Button
            disabled={exporting || !rows.length}
            onClick={() => exportFile("json")}
          >
            Exportar JSON
          </Button>
          <span className="small muted" aria-live="polite">
            {rows.length} registro(s) — ordem cronológica decrescente
          </span>
        </div>
        {!state.audit.length ? (
          <EmptyState title="Ainda não há registros">
            Os ensaios e incidentes acompanhados aparecerão aqui.
          </EmptyState>
        ) : !rows.length ? (
          <EmptyState
            title="Nenhum resultado para os filtros"
            action={<Button onClick={clear}>Limpar filtros</Button>}
          >
            Revise o período, o serviço ou o tipo de anomalia.
          </EmptyState>
        ) : (
          <>
            <p className="small muted">
              Role a tabela horizontalmente para consultar normalização e MTTR →
            </p>
            <div
              className="table-wrap audit-table"
              tabIndex={0}
              role="region"
              aria-label="Histórico de auditoria, rolagem horizontal"
            >
              <table>
                <thead>
                  <tr>
                    {columns.map((c) => (
                      <th scope="col" key={c}>
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id}>
                      {auditValues(r).map((value, i) => (
                        <td key={i}>{value}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </>
  );
}

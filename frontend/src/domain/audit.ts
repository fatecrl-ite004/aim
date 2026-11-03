import type { AuditRecord } from "./model";
import { dateBRT } from "./model";
export interface Filters {
  from: string;
  to: string;
  service: string;
  type: string;
}
export const defaultFilters: Filters = {
  from: "2026-10-08",
  to: "2026-10-08",
  service: "all",
  type: "all",
};
export function filterAudit(records: AuditRecord[], f: Filters) {
  return records
    .filter((x) => {
      const day = x.detectedAt.slice(0, 10);
      return (
        (!f.from || day >= f.from) &&
        (!f.to || day <= f.to) &&
        (f.service === "all" || x.service === f.service) &&
        (f.type === "all" || x.type === f.type)
      );
    })
    .sort((a, b) => Date.parse(b.detectedAt) - Date.parse(a.detectedAt));
}
export const columns = [
  "ID do ensaio",
  "Microsserviço",
  "Métrica divergente",
  "Timestamp da injeção de falha",
  "Timestamp da detecção proativa pelo AIM",
  "Tempo de antecedência alcançado (MTTA)",
  "Timestamp de normalização",
  "Tempo de recuperação (MTTR)",
];
export const auditValues = (r: AuditRecord) => [
  r.id,
  r.service,
  r.metric,
  dateBRT(r.injectedAt),
  dateBRT(r.detectedAt),
  "Não calculado",
  r.normalizedAt ? dateBRT(r.normalizedAt) : "Aguardando normalização",
  "Não calculado",
];
export function serializeAudit(rows: AuditRecord[], format: "csv" | "json") {
  if (format === "json")
    return JSON.stringify(
      rows.map((r) =>
        Object.fromEntries(columns.map((c, i) => [c, auditValues(r)[i]])),
      ),
      null,
      2,
    );
  const escape = (s: string) => '"' + s.replaceAll('"', '""') + '"';
  return (
    "\uFEFF" +
    [columns, ...rows.map(auditValues)]
      .map((row) => row.map(escape).join(","))
      .join("\r\n")
  );
}
export function downloadAudit(rows: AuditRecord[], format: "csv" | "json") {
  const url = URL.createObjectURL(
    new Blob([serializeAudit(rows, format)], {
      type:
        format === "csv"
          ? "text/csv;charset=utf-8"
          : "application/json;charset=utf-8",
    }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = "aim-auditoria." + format;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

import { describe, expect, it } from "vitest";
import {
  canNormalize,
  emailValid,
  endpointValid,
  initialState,
  metrics,
  monitoring,
  reducer,
  restoreState,
  risk,
} from "../src/domain/model";
import {
  auditValues,
  columns,
  defaultFilters,
  filterAudit,
  serializeAudit,
} from "../src/domain/audit";
describe("Supervisão e incidentes", () => {
  it("mantém conectividade e pausa individual ao retomar o global", () => {
    let s = initialState();
    s = reducer(s, { type: "service-toggle", id: "checkout-service" });
    s = reducer(s, { type: "global-toggle" });
    expect(monitoring(s, s.services[1])).toBe(false);
    s = reducer(s, { type: "service-toggle", id: "payment-worker" });
    expect(s.services[1].paused).toBe(false);
    s = reducer(s, { type: "global-toggle" });
    expect(monitoring(s, s.services[0])).toBe(false);
    expect(monitoring(s, s.services[1])).toBe(true);
  });
  it("distingue origem, reflexos e risco indeterminado", () => {
    let s = initialState("incident");
    expect(risk(s, s.services[0])).toBe("origin");
    expect(risk(s, s.services[1])).toBe("reflex");
    s = { ...s, dataStatus: "stale" };
    expect(risk(s, s.services[0])).toBe("unknown");
  });
  it.each(["global", "individual", "stale", "removed"] as const)(
    "bloqueia normalização: %s",
    (reason) => {
      let s = initialState("incident");
      if (reason === "global") s.globalPaused = true;
      if (reason === "individual") s.services[0].paused = true;
      if (reason === "stale") s.dataStatus = "stale";
      if (reason === "removed") s.services = s.services.slice(1);
      expect(canNormalize(s)).toBe(false);
      expect(reducer(s, { type: "normalize" }).incident).toBe("active");
      expect(reducer(s, { type: "estimate-update" }).estimateUpdated).toBe(
        false,
      );
    },
  );
  it("normaliza, registra timestamp e arquiva explicitamente", () => {
    let s = initialState("incident");
    s = reducer(s, { type: "normalize" });
    expect(s.incident).toBe("normalized");
    expect(s.audit[0].normalizedAt).toBe(s.normalizedAt);
    expect(metrics(s.services[0], s.incident).pool).toBe(32);
    s = reducer(s, { type: "archive" });
    expect(s.incident).toBe("archived");
    expect(s.audit).toHaveLength(2);
  });
  it("não permite arquivar um incidente ativo", () => {
    expect(
      reducer(initialState("incident"), { type: "archive" }).incident,
    ).toBe("active");
  });
  it("desvincula qualquer serviço preservando histórico", () => {
    const s = initialState();
    const next = reducer(s, { type: "service-remove", id: "auth-service" });
    expect(next.services.some((x) => x.id === "auth-service")).toBe(false);
    expect(next.audit).toEqual(s.audit);
  });
  it("impede cadastro duplicado sem sobrescrever o serviço", () => {
    const s = initialState();
    expect(
      reducer(s, { type: "service-add", service: s.services[0] }).services,
    ).toHaveLength(6);
  });
});
describe("Validação e persistência", () => {
  it.each([
    "http://otel:4317",
    "https://otel.exemplo.com",
    "grpc://localhost:4317",
    "grpcs://otel:4317",
  ])("aceita endpoint %s", (s) => expect(endpointValid(s)).toBe(true));
  it.each([
    "javascript:alert(1)",
    "invalido",
    "ftp://servidor",
    "https://user:senha@otel",
  ])("rejeita endpoint %s", (s) => expect(endpointValid(s)).toBe(false));
  it("valida e-mail e impede duplicado sem diferenciar caixa", () => {
    expect(emailValid("email-invalido")).toBe(false);
    expect(emailValid("time@empresa.com")).toBe(true);
    const s = initialState();
    expect(
      reducer(s, { type: "recipient-add", email: "ALERTA-SRE@EMPRESA.COM" })
        .recipients,
    ).toHaveLength(2);
  });
  it("recupera armazenamento inválido e versões incompatíveis", () => {
    expect(restoreState("{")).toEqual(initialState());
    expect(restoreState('{"version":2}')).toEqual(initialState());
    expect(
      restoreState(
        JSON.stringify({
          version: 1,
          state: { ...initialState(), services: [{}] },
        }),
      ),
    ).toEqual(initialState());
  });
  it("restaura dados válidos e recupera carregamento interrompido", () => {
    const s = { ...initialState("incident"), dataStatus: "loading" as const };
    expect(restoreState(JSON.stringify({ version: 1, state: s }))).toEqual({
      ...s,
      dataStatus: "ready",
    });
  });
});
describe("Auditoria e exportação", () => {
  it("combina filtros sem perder registros de serviços desvinculados", () => {
    const s = initialState();
    expect(
      filterAudit(s.audit, {
        ...defaultFilters,
        service: "auth-service",
        type: "cpu",
      }),
    ).toHaveLength(1);
    expect(
      filterAudit(s.audit, {
        ...defaultFilters,
        service: "auth-service",
        type: "pool",
      }),
    ).toHaveLength(0);
    expect(
      filterAudit(s.audit, { ...defaultFilters, from: "2026-10-09" }),
    ).toHaveLength(0);
  });
  it("preserva oito campos e não inventa MTTA ou MTTR", () => {
    const s = initialState();
    expect(columns).toHaveLength(8);
    expect(auditValues(s.audit[0])[5]).toBe("Não calculado");
    const data = JSON.parse(serializeAudit(s.audit, "json"));
    expect(Object.keys(data[0])).toHaveLength(8);
    expect(data[0][columns[7]]).toBe("Não calculado");
  });
  it("escapa aspas e vírgulas em CSV e inclui cabeçalhos com BOM", () => {
    const record = { ...initialState().audit[0], metric: 'Pool, "exemplo"' };
    const csv = serializeAudit([record], "csv");
    expect(csv.startsWith("\uFEFF")).toBe(true);
    expect(csv).toContain('"Pool, ""exemplo"""');
    expect(csv.split("\r\n")).toHaveLength(2);
  });
});

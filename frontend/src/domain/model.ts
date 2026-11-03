export interface Service {
  id: string;
  runtime: string;
  endpoint: string;
  paused: boolean;
  latency: number;
  p99: number;
  connections: number;
  pool: number;
  cpu: number;
  ram: number;
}
export interface Recipient {
  email: string;
  active: boolean;
}
export interface AuditRecord {
  id: string;
  service: string;
  metric: string;
  injectedAt: string;
  detectedAt: string;
  mtta: null;
  normalizedAt: string | null;
  mttr: null;
  type: "pool" | "cpu";
}
export type IncidentStatus = "none" | "active" | "normalized" | "archived";
export type DataStatus = "ready" | "loading" | "empty" | "stale";
export interface State {
  services: Service[];
  globalPaused: boolean;
  incident: IncidentStatus;
  normalizedAt: string | null;
  estimateUpdated: boolean;
  dataStatus: DataStatus;
  recipients: Recipient[];
  audit: AuditRecord[];
  endpointFails: boolean;
  emailFails: boolean;
}
export type Scenario =
  | "normal"
  | "incident"
  | "empty"
  | "stale"
  | "no-data"
  | "no-history"
  | "no-recipients"
  | "endpoint-failure"
  | "email-failure";
export type Action =
  | { type: "reset"; scenario: Scenario }
  | { type: "global-toggle" }
  | { type: "service-toggle"; id: string }
  | { type: "service-add"; service: Service }
  | { type: "service-remove"; id: string }
  | { type: "normalize" }
  | { type: "archive" }
  | { type: "estimate-update" }
  | { type: "data-status"; status: DataStatus }
  | { type: "recipient-add"; email: string }
  | { type: "recipient-toggle"; email: string }
  | { type: "recipient-remove"; email: string };
export const BASE_TIME = "2026-10-08T16:37:12-03:00";
export const NORMALIZED_TIME = "2026-10-08T16:45:12-03:00";
export const STORE_KEY = "aim-react-mock-v1";
const seed = [
  ["checkout-service", "Node.js 22", 42, 74, 24, 32, 24, 0.8],
  ["payment-worker", ".NET 8", 38, 66, 18, 28, 21, 0.6],
  ["api-gateway", "Go 1.23", 25, 48, 12, 20, 18, 0.4],
  ["auth-service", "Java 21", 31, 62, 16, 26, 26, 1.1],
  ["catalog-service", "Python 3.12", 54, 96, 20, 30, 23, 0.7],
  ["notification-worker", "Node.js 22", 18, 36, 8, 14, 12, 0.3],
] as const;
export const initialServices = (): Service[] =>
  seed.map(([id, runtime, latency, p99, connections, pool, cpu, ram]) => ({
    id,
    runtime,
    latency,
    p99,
    connections,
    pool,
    cpu,
    ram,
    paused: false,
    endpoint: "http://otel-collector:4317",
  }));
export const initialAudit = (): AuditRecord[] => [
  {
    id: "ENS-0042",
    service: "checkout-service",
    metric: "Pool · +14%/min",
    injectedAt: "2026-10-08T16:30:00-03:00",
    detectedAt: "2026-10-08T16:36:42-03:00",
    mtta: null,
    normalizedAt: null,
    mttr: null,
    type: "pool",
  },
  {
    id: "ENS-0041",
    service: "auth-service",
    metric: "CPU · +9%/min",
    injectedAt: "2026-10-08T14:10:00-03:00",
    detectedAt: "2026-10-08T14:13:20-03:00",
    mtta: null,
    normalizedAt: "2026-10-08T14:22:15-03:00",
    mttr: null,
    type: "cpu",
  },
];
export function initialState(scenario: Scenario = "normal"): State {
  return {
    services: scenario === "empty" ? [] : initialServices(),
    globalPaused: false,
    incident: scenario === "incident" ? "active" : "none",
    normalizedAt: null,
    estimateUpdated: false,
    dataStatus:
      scenario === "stale"
        ? "stale"
        : scenario === "no-data"
          ? "empty"
          : "ready",
    recipients:
      scenario === "no-recipients"
        ? []
        : [
            { email: "alerta-sre@empresa.com", active: true },
            { email: "devops@empresa.com", active: true },
          ],
    audit: scenario === "no-history" ? [] : initialAudit(),
    endpointFails: scenario === "endpoint-failure",
    emailFails: scenario === "email-failure",
  };
}
export function canNormalize(s: State) {
  return (
    s.incident === "active" &&
    !s.globalPaused &&
    s.dataStatus === "ready" &&
    !!s.services.find((x) => x.id === "checkout-service" && !x.paused)
  );
}
export function reducer(s: State, a: Action): State {
  switch (a.type) {
    case "reset":
      return initialState(a.scenario);
    case "global-toggle":
      return { ...s, globalPaused: !s.globalPaused };
    case "service-toggle":
      return s.globalPaused
        ? s
        : {
            ...s,
            services: s.services.map((x) =>
              x.id === a.id ? { ...x, paused: !x.paused } : x,
            ),
          };
    case "service-add":
      return s.services.some((x) => x.id === a.service.id)
        ? s
        : { ...s, services: [...s.services, a.service] };
    case "service-remove":
      return { ...s, services: s.services.filter((x) => x.id !== a.id) };
    case "normalize":
      return canNormalize(s)
        ? {
            ...s,
            incident: "normalized",
            normalizedAt: NORMALIZED_TIME,
            audit: s.audit.map((x) =>
              x.id === "ENS-0042" ? { ...x, normalizedAt: NORMALIZED_TIME } : x,
            ),
          }
        : s;
    case "archive":
      return s.incident === "normalized" ? { ...s, incident: "archived" } : s;
    case "estimate-update":
      return canNormalize(s) ? { ...s, estimateUpdated: true } : s;
    case "data-status":
      return { ...s, dataStatus: a.status };
    case "recipient-add":
      return s.recipients.some(
        (x) => x.email.toLowerCase() === a.email.toLowerCase(),
      )
        ? s
        : {
            ...s,
            recipients: [
              ...s.recipients,
              { email: a.email.toLowerCase(), active: true },
            ],
          };
    case "recipient-toggle":
      return {
        ...s,
        recipients: s.recipients.map((x) =>
          x.email === a.email ? { ...x, active: !x.active } : x,
        ),
      };
    case "recipient-remove":
      return {
        ...s,
        recipients: s.recipients.filter((x) => x.email !== a.email),
      };
  }
}
export function monitoring(s: State, service: Service) {
  return !s.globalPaused && !service.paused;
}
export function risk(
  s: State,
  service: Service,
): "unknown" | "origin" | "reflex" | "normal" {
  if (!monitoring(s, service) || s.dataStatus !== "ready") return "unknown";
  if (s.incident !== "active") return "normal";
  return service.id === "checkout-service"
    ? "origin"
    : ["payment-worker", "api-gateway"].includes(service.id)
      ? "reflex"
      : "normal";
}
export function metrics(service: Service, incident: IncidentStatus) {
  if (incident !== "active") return service;
  const overrides: Record<string, Partial<Service>> = {
    "checkout-service": {
      latency: 184,
      p99: 420,
      connections: 78,
      pool: 92,
      cpu: 68,
      ram: 1.4,
    },
    "payment-worker": {
      latency: 96,
      p99: 168,
      connections: 30,
      pool: 54,
      cpu: 40,
      ram: 0.8,
    },
    "api-gateway": {
      latency: 78,
      p99: 144,
      connections: 22,
      pool: 40,
      cpu: 34,
      ram: 0.6,
    },
  };
  return { ...service, ...overrides[service.id] };
}
export function endpointValid(value: string) {
  try {
    const u = new URL(value);
    return (
      ["http:", "https:", "grpc:", "grpcs:"].includes(u.protocol) &&
      !!u.hostname &&
      !u.username &&
      !u.password
    );
  } catch {
    return false;
  }
}
export function emailValid(value: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}
export const dateBRT = (value: string) =>
  new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    dateStyle: "short",
    timeStyle: "medium",
  }).format(new Date(value)) + " BRT";
export const formatNumber = (n: number) =>
  new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(n);
export function restoreState(raw: string | null): State {
  if (!raw) return initialState();
  try {
    const saved = JSON.parse(raw);
    if (saved.version !== 1) return initialState();
    const s = saved.state;
    const string = (v: unknown) => typeof v === "string";
    const number = (v: unknown) =>
      typeof v === "number" && Number.isFinite(v) && v >= 0;
    if (
      !s ||
      !Array.isArray(s.services) ||
      !s.services.every(
        (x: Service) =>
          x &&
          string(x.id) &&
          string(x.runtime) &&
          string(x.endpoint) &&
          typeof x.paused === "boolean" &&
          [x.latency, x.p99, x.connections, x.pool, x.cpu, x.ram].every(number),
      ) ||
      !Array.isArray(s.recipients) ||
      !s.recipients.every(
        (x: Recipient) =>
          x && emailValid(x.email) && typeof x.active === "boolean",
      ) ||
      !Array.isArray(s.audit) ||
      !s.audit.every(
        (x: AuditRecord) =>
          x &&
          string(x.id) &&
          string(x.service) &&
          string(x.metric) &&
          Number.isFinite(Date.parse(x.injectedAt)) &&
          Number.isFinite(Date.parse(x.detectedAt)) &&
          x.mtta === null &&
          x.mttr === null &&
          (x.normalizedAt === null ||
            Number.isFinite(Date.parse(x.normalizedAt))) &&
          ["cpu", "pool"].includes(x.type),
      ) ||
      !["none", "active", "normalized", "archived"].includes(s.incident) ||
      !["ready", "loading", "empty", "stale"].includes(s.dataStatus) ||
      ![s.globalPaused, s.estimateUpdated, s.endpointFails, s.emailFails].every(
        (x) => typeof x === "boolean",
      ) ||
      (s.normalizedAt !== null && !Number.isFinite(Date.parse(s.normalizedAt)))
    )
      return initialState();
    return {
      ...s,
      dataStatus: s.dataStatus === "loading" ? "ready" : s.dataStatus,
    };
  } catch {
    return initialState();
  }
}

import { expect, test } from "@playwright/test";
import type { Page, Route } from "@playwright/test";
import type { DemoRun } from "../src/domain/replay";

const replayId = "11111111-1111-4111-8111-111111111111";
const transformId = "22222222-2222-4222-8222-222222222222";
const secondTransform = "33333333-3333-4333-8333-333333333333";
const serviceId = "recommendationservice";
const instanceId = "recommendationservice-1";
const start = 1719205980000000000n;
const ns = (index: number) => (start + BigInt(index) * 15_000_000_000n).toString();

type ReplayMockOptions = {
  empty?: boolean;
  failing?: boolean;
  defaultTransformId?: string;
  followTransformId?: string;
  rawPointCount?: number;
  createdReplayId?: string;
  holdMetrics?: { transformId: string; release?: () => void };
  demoRunHandler?: (route: Route, url: URL) => Promise<void>;
};

async function mockReplay(page: Page, options: ReplayMockOptions = {}) {
  const metricQueries: URLSearchParams[] = [];
  await page.route("**/api/v1/demo-runs**", async (route) => {
    const url = new URL(route.request().url());
    if (options.demoRunHandler) return options.demoRunHandler(route, url);
    if (url.pathname.endsWith("/active")) return route.fulfill({ json: { demo_run: null } });
    return route.fulfill({ status: 404, json: { detail: "não encontrado" } });
  });
  await page.route("**/api/v1/replays**", async (route) => {
    const url = new URL(route.request().url());
    const pathReplayId = url.pathname.match(/\/replays\/([^/]+)/)?.[1];
    const requestedReplayId = pathReplayId ? decodeURIComponent(pathReplayId) : replayId;
    let body: unknown;
    if (options.failing) return route.fulfill({ status: 503, json: { detail: "indisponível" } });
    if (url.pathname.endsWith("/services")) {
      body = { services: [{ service_id: serviceId, service_name: "recommendationservice", instances: [{ instance_id: instanceId, instance_name: instanceId }] }] };
    } else if (url.pathname.endsWith("/transforms")) {
      const transforms = [
        { transform_run_id: transformId, version: "counter-rates-v1", status: "completed", completed_at: "2026-11-10T12:00:00Z" },
        { transform_run_id: secondTransform, version: "counter-rates-60s-v1", status: "completed", completed_at: "2026-11-10T12:01:00Z" },
      ];
      if (options.followTransformId) transforms.unshift({ transform_run_id: options.followTransformId, version: "counter-rates-v1", status: "completed", completed_at: "2026-11-10T12:02:00Z" });
      body = { default_transform_run_id: options.defaultTransformId ?? transformId, transforms };
    } else if (url.pathname.endsWith("/progress")) {
      body = { replay_run_id: replayId, service_id: serviceId, instance_id: instanceId, raw_point_count: options.rawPointCount ?? 282, ingest_batch_count: 3, latest_source_timestamp_unix_nano: ns(4), latest_received_at: "2026-11-10T12:03:00Z" };
    } else if (url.pathname.endsWith("/events")) {
      body = { events: [{ event_id: "injected-cpu", event_kind: "injected_fault", failure_type: "cpu", start_unix_nano: ns(1), end_unix_nano: ns(3), instance_id: instanceId, source_file_sha256: "a".repeat(64), source_event_ordinal: 2 }] };
    } else if (url.pathname.endsWith("/metrics")) {
      metricQueries.push(url.searchParams);
      const selected = url.searchParams.get("transform_run_id");
      if (options.holdMetrics?.transformId === selected) {
        await new Promise<void>((resolve) => { options.holdMetrics!.release = resolve; });
      }
      body = { replay_run_id: requestedReplayId, transform_run_id: selected, service_id: serviceId, instance_id: instanceId, metrics: [
        ...[0, 0, 0, selected === secondTransform || selected === options.followTransformId ? 0.5 : 0.25].map((value, index) => ({ metric_name: "cpu_cores", value, unit: "cores", coverage_state: "complete", reason: null, window_start_unix_nano: ns(index), window_end_unix_nano: ns(index + 1) })),
        ...[2, 0, 0, 3].map((value, index) => ({ metric_name: "success_response_rate", value, unit: "1/s", coverage_state: "complete", reason: null, window_start_unix_nano: ns(index), window_end_unix_nano: ns(index + 1) })),
        ...[12, null, null, 18].map((value, index) => ({ metric_name: "success_latency_mean_ms", value, unit: "ms", coverage_state: value === null ? "not_applicable" : "complete", reason: value === null ? "no_observed_increment" : null, window_start_unix_nano: ns(index), window_end_unix_nano: ns(index + 1) })),
      ] };
    } else {
      const runs = options.empty ? [] : [{ replay_run_id: replayId, source_name: "AIOpsArena", case_id: "Case-1", status: "received", display_start_unix_nano: ns(0), display_end_unix_nano: ns(4) }];
      if (options.createdReplayId) runs.unshift({ replay_run_id: options.createdReplayId, source_name: "AIOpsArena", case_id: "Case-2", status: "processed", display_start_unix_nano: ns(0), display_end_unix_nano: ns(4) });
      body = { replays: runs };
    }
    await route.fulfill({ json: body });
  });
  return metricQueries;
}

test("Dashboard → replay seleciona run, preserva no_observed_increment e separa mock", async ({ page }) => {
  const queries = await mockReplay(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Replay histórico AIOpsArena" })).toBeVisible();
  await page.getByRole("link", { name: "Abrir replay histórico", exact: true }).click();
  await expect(page.getByRole("heading", { name: "CPU média por intervalo" })).toBeVisible();
  expect(queries[0].get("instance_id")).toBe(instanceId);
  expect(queries[0].get("transform_run_id")).toBe(transformId);
  expect(queries[0].get("from_unix_nano")).toBe(ns(0));
  expect(queries[0].get("to_unix_nano")).toBe(ns(4));
  await expect(page.getByText("0,25 cores", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Falha de CPU injetada", exact: true })).toBeVisible();
  const latency = page.getByRole("region", { name: "Latência média das respostas 200", exact: true });
  await expect(latency.getByRole("img")).toHaveAttribute("aria-label", /2 de 4 janelas com valor. 2 sem incremento observado/);
  await expect(latency.locator("polyline")).toHaveCount(2);
  await expect(page.getByText(/P99/)).toHaveCount(0);
  await expect(page.getByRole("switch", { name: "Sentinela global" })).toHaveCount(0);
  await page.getByText("Consultar valores e cobertura por intervalo (4 janelas)", { exact: true }).click();
  await expect(page.getByRole("cell", { name: "— Não aplicável · Sem incremento observado" })).toHaveCount(2);
  await page.getByRole("combobox", { name: "Execução de transformação", exact: true }).selectOption(secondTransform);
  await expect(page.getByText("0,5 cores", { exact: true })).toBeVisible();
  expect(queries.at(-1)!.get("transform_run_id")).toBe(secondTransform);
  await page.setViewportSize({ width: 390, height: 844 });
  const overflow = await page.evaluate(() => Array.from(document.querySelectorAll<HTMLElement>("body *"))
    .filter((element) => { const rect = element.getBoundingClientRect(); return rect.left < -1 || rect.right > window.innerWidth + 1; })
    .slice(0, 4).map((element) => ({ tag: element.tagName, className: element.className, text: element.innerText.slice(0, 50), left: Math.round(element.getBoundingClientRect().left), right: Math.round(element.getBoundingClientRect().right), parents: [element.parentElement, element.parentElement?.parentElement, element.parentElement?.parentElement?.parentElement].map((parent) => parent && ({ tag: parent.tagName, className: parent.className, left: Math.round(parent.getBoundingClientRect().left), right: Math.round(parent.getBoundingClientRect().right), overflow: getComputedStyle(parent).overflow })) })));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), JSON.stringify(overflow)).toBe(true);
  await page.screenshot({ path: "test-results/replay-mobile.png", fullPage: true });
});

test("exporta CSVs com escopo correto e acompanha nova transformação", async ({ page }) => {
  const options: { defaultTransformId?: string; followTransformId?: string; rawPointCount?: number } = { defaultTransformId: transformId, rawPointCount: 100 };
  const queries = await mockReplay(page, options);
  await page.goto("/");
  await page.getByRole("link", { name: "Abrir replay histórico", exact: true }).click();

  const rawHref = await page.getByRole("link", { name: "Exportar pontos brutos completos CSV" }).getAttribute("href");
  const rawUrl = new URL(rawHref!, page.url());
  expect(rawUrl.searchParams.get("instance_id")).toBe(instanceId);
  expect(rawUrl.searchParams.has("from_unix_nano")).toBe(false);
  expect(rawUrl.searchParams.has("to_unix_nano")).toBe(false);

  const derivedHref = await page.getByRole("link", { name: "Exportar métricas derivadas CSV" }).getAttribute("href");
  const derivedUrl = new URL(derivedHref!, page.url());
  expect(derivedUrl.searchParams.get("instance_id")).toBe(instanceId);
  expect(derivedUrl.searchParams.get("transform_run_id")).toBe(transformId);
  expect(derivedUrl.searchParams.get("from_unix_nano")).toBe(ns(0));
  expect(derivedUrl.searchParams.get("to_unix_nano")).toBe(ns(4));

  await expect(page.getByRole("status", { name: /Chegada das .*OTLP/ })).toBeVisible();
  await page.getByRole("button", { name: /Pausar acompanhamento/ }).click();
  options.defaultTransformId = secondTransform;
  options.followTransformId = "44444444-4444-4444-8444-444444444444";
  options.rawPointCount = 282;
  await page.getByRole("button", { name: /Acompanhar ingest/ }).click();
  await expect(page.getByText("0,5 cores", { exact: true })).toBeVisible({ timeout: 5000 });
  expect(queries.at(-1)!.get("transform_run_id")).toBe(options.followTransformId);
  await expect(page.getByText(/282 pontos brutos persistidos/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Pausar acompanhamento" })).toBeVisible();
});

test("mantém os cards, os valores e a posição durante consultas de métricas", async ({ page }) => {
  const options: ReplayMockOptions = { holdMetrics: { transformId: secondTransform } };
  await mockReplay(page, options);
  await page.goto("/");
  await page.getByRole("link", { name: "Abrir replay histórico", exact: true }).click();

  const cpu = page.getByRole("region", { name: "CPU média por intervalo", exact: true });
  await expect(cpu).toBeVisible();
  const mountedCpuPanel = await cpu.elementHandle();
  await page.getByRole("combobox", { name: "Execução de transformação", exact: true }).selectOption(secondTransform);
  await expect(page.getByText("Atualizando séries…", { exact: true })).toBeVisible();
  await expect(page.getByText("0,25 cores", { exact: true })).toBeVisible();
  expect(await mountedCpuPanel!.evaluate((element) => element.isConnected)).toBe(true);
  (options.holdMetrics!.release as (() => void) | undefined)?.();
  await expect(page.getByText("0,5 cores", { exact: true })).toBeVisible();

  options.holdMetrics!.release = undefined;
  await page.getByRole("button", { name: "Atualizar", exact: true }).click({ force: true });
  await expect(page.getByText("Atualizando séries…", { exact: true })).toBeVisible();
  await page.evaluate(() => {
    const main = document.querySelector<HTMLElement>(".workspace-scroll")!;
    main.scrollTop = Math.min(480, main.scrollHeight - main.clientHeight);
  });
  const beforeRefreshScroll = await page.locator(".workspace-scroll").evaluate((element) => element.scrollTop);
  expect(await mountedCpuPanel!.evaluate((element) => element.isConnected)).toBe(true);
  await expect(page.getByText("0,5 cores", { exact: true })).toBeVisible();
  expect(await page.locator(".workspace-scroll").evaluate((element) => element.scrollTop)).toBe(beforeRefreshScroll);
  (options.holdMetrics!.release as (() => void) | undefined)?.();
  await expect(page.getByText("0,5 cores", { exact: true })).toBeVisible();
});

test("inicia demo idempotente, acompanha marcos OTLP e abre o replay quando há séries", async ({ page }) => {
  const newDemoRunId = "55555555-5555-4555-8555-555555555555";
  const newReplayId = "66666666-6666-4666-8666-666666666666";
  let postBody = "";
  let idempotencyKey = "";
  let statusReads = 0;
  let latestRun: DemoRun = {
    demo_run_id: newDemoRunId, replay_run_id: newReplayId, status: "running" as const,
    current_stage: "sending", total_chunks: 3, completed_chunks: 1,
    raw_point_count: 100, expected_raw_point_count: 282,
    latest_transform_run_id: null, latest_transform_60s_run_id: null,
    error_code: null, message: null, created_at: "2026-11-12T12:00:00Z", started_at: "2026-11-12T12:00:01Z", completed_at: null,
  };
  const options: ReplayMockOptions = {
    demoRunHandler: async (route, url) => {
      if (url.pathname.endsWith("/active")) return route.fulfill({ json: { demo_run: null } });
      if (route.request().method() === "POST") {
        postBody = route.request().postData() ?? "";
        idempotencyKey = route.request().headers()["idempotency-key"] ?? "";
        options.createdReplayId = newReplayId;
        return route.fulfill({ status: 202, json: latestRun });
      }
      statusReads += 1;
      if (statusReads > 1) latestRun = { ...latestRun, completed_chunks: 3, raw_point_count: 282, latest_transform_60s_run_id: secondTransform, current_stage: "verifying", status: "completed", completed_at: "2026-11-12T12:00:03Z" };
      return route.fulfill({ json: latestRun });
    },
  };
  options.defaultTransformId = secondTransform;
  await mockReplay(page, options);
  await page.goto("/");
  await page.getByRole("button", { name: "Iniciar demonstração", exact: true }).click();
  await expect(page.getByRole("status", { name: "Status da demonstração" })).toContainText("100 pontos OTLP persistidos de 282");
  await expect(page.getByRole("status", { name: "Status da demonstração" })).toContainText("1 de 3 lotes");
  expect(postBody).toBe("{}");
  expect(idempotencyKey).toMatch(/^[0-9a-f-]{36}$/i);
  await expect(page.getByRole("heading", { name: "CPU média por intervalo" })).toBeVisible({ timeout: 8000 });
  expect(page.url()).toContain(newReplayId);
  await expect(page.getByText("0,5 cores", { exact: true })).toBeVisible();
});

test("409 acompanha run ativa e preserva o replay escolhido manualmente", async ({ page }) => {
  const activeRunId = "77777777-7777-4777-8777-777777777777";
  const activeReplayId = "88888888-8888-4888-8888-888888888888";
  let postCount = 0;
  let allowCompletion = false;
  let activeRun: DemoRun = {
    demo_run_id: activeRunId, replay_run_id: activeReplayId, status: "running" as const,
    current_stage: "sending", total_chunks: 3, completed_chunks: 1,
    raw_point_count: 100, expected_raw_point_count: 282,
    latest_transform_run_id: null, latest_transform_60s_run_id: null,
    error_code: null, message: null, created_at: "2026-11-12T12:00:00Z", started_at: "2026-11-12T12:00:01Z", completed_at: null,
  };
  const options: ReplayMockOptions = {
    demoRunHandler: async (route, url) => {
      if (url.pathname.endsWith("/active")) return route.fulfill({ json: { demo_run: null } });
      if (route.request().method() === "POST") {
        postCount += 1;
        options.createdReplayId = activeReplayId;
        return route.fulfill({ status: 409, json: { detail: { code: "demo_already_running", message: "run ativa", demo_run_id: activeRunId, replay_run_id: activeReplayId } } });
      }
      if (allowCompletion) activeRun = { ...activeRun, completed_chunks: 3, raw_point_count: 282, latest_transform_60s_run_id: secondTransform, status: "completed", current_stage: "completed", completed_at: "2026-11-12T12:00:03Z" };
      return route.fulfill({ json: activeRun });
    },
  };
  await mockReplay(page, options);
  await page.goto("/");
  await page.getByRole("button", { name: "Iniciar demonstração", exact: true }).click();
  const status = page.getByRole("status", { name: "Status da demonstração" });
  await expect(status).toContainText("Demonstração em andamento");
  await expect(status).toContainText("100 pontos OTLP persistidos de 282");
  await page.getByLabel("Execução de replay").selectOption(replayId);
  allowCompletion = true;
  await expect(status).toContainText("Demonstração concluída", { timeout: 5000 });
  await expect(page.getByLabel("Execução de replay")).toHaveValue(replayId);
  expect(new URL(page.url()).hash).toBe("");
  expect(postCount).toBe(1);
});

test("recupera status interrupted pelo último ID após reload", async ({ page }) => {
  const failedId = "99999999-9999-4999-8999-999999999999";
  const failedRun: DemoRun = {
    demo_run_id: failedId, replay_run_id: replayId, status: "failed",
    current_stage: "interrupted", total_chunks: 3, completed_chunks: 2,
    raw_point_count: 144, expected_raw_point_count: 282,
    latest_transform_run_id: transformId, latest_transform_60s_run_id: null,
    error_code: "interrupted", message: "A API reiniciou durante a execução.",
    created_at: "2026-11-12T12:00:00Z", started_at: "2026-11-12T12:00:01Z", completed_at: "2026-11-12T12:00:20Z",
  };
  const options: ReplayMockOptions = {
    demoRunHandler: async (route, url) => {
      if (url.pathname.endsWith("/active")) return route.fulfill({ json: { demo_run: null } });
      return route.fulfill({ json: failedRun });
    },
  };
  await mockReplay(page, options);
  await page.addInitScript(({ id }) => window.sessionStorage.setItem("aim.demo-run.latest-id", id), { id: failedId });
  await page.goto("/");
  const status = page.getByRole("status", { name: "Status da demonstração" });
  await expect(status).toContainText("Demonstração falhou");
  await expect(status).toContainText("144 pontos OTLP persistidos de 282");
  await expect(status).toContainText("A API reiniciou durante a execução.");
});

test("API indisponível e replay vazio não substituem dados por mock", async ({ page }) => {
  const options = { failing: true, empty: false };
  await mockReplay(page, options);
  await page.goto("/");
  await expect(page.getByText("Replay indisponível", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir replay histórico", exact: true })).toHaveCount(0);
  options.failing = false;
  options.empty = true;
  await page.getByRole("button", { name: "Tentar novamente a consulta", exact: true }).click();
  await expect(page.getByText("Nenhum replay persistido", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Malha demonstrativa", exact: true })).toBeVisible();
});

test("rejeita envelope inválido sem interromper a navegação do mock", async ({ page }) => {
  await page.route("**/api/v1/replays", (route) => route.fulfill({ json: { replays: "inválido" } }));
  await page.goto("/");
  await expect(page.getByText("A API retornou uma resposta inválida para esta consulta.", { exact: true })).toBeVisible();
  await page.getByRole("navigation", { name: "Navegação principal" }).getByRole("link", { name: "Serviços", exact: true }).click();
  await expect(page.getByRole("button", { name: "+ Novo serviço", exact: true })).toBeVisible();
});

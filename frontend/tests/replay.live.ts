import { expect, test } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

type MetricPoint = {
  value: number | null;
  coverage_state: string;
  reason: string | null;
  window_start_unix_nano: string;
  window_end_unix_nano: string;
};

async function readMetrics(request: import("@playwright/test").APIRequestContext, replayId: string, serviceId: string, instanceId: string, transformId: string) {
  const params = new URLSearchParams({ instance_id: instanceId, transform_run_id: transformId });
  const response = await request.get(`/api/v1/replays/${replayId}/services/${serviceId}/metrics?${params}`);
  expect(response.ok(), `Falha ao consultar métricas da transformação ${transformId}`).toBeTruthy();
  return (await response.json()).metrics as MetricPoint[];
}

async function verifyCsv(request: import("@playwright/test").APIRequestContext, replayId: string, serviceId: string, instanceId: string, transformId: string, rows: number) {
  const params = new URLSearchParams({ instance_id: instanceId, transform_run_id: transformId });
  const response = await request.get(`/api/v1/replays/${replayId}/services/${serviceId}/export/derived.csv?${params}`);
  expect(response.ok(), `Falha ao exportar CSV da transformação ${transformId}`).toBeTruthy();
  expect(response.headers()["content-type"]).toContain("text/csv");
  const csv = await response.text();
  expect(csv.split(/\r?\n/).filter(Boolean)).toHaveLength(rows + 1); // inclui cabeçalho
  expect(csv).toContain(transformId);
}

async function verifyRawCsv(request: import("@playwright/test").APIRequestContext, replayId: string, serviceId: string, instanceId: string, points: number) {
  const params = new URLSearchParams({ instance_id: instanceId });
  const response = await request.get(`/api/v1/replays/${replayId}/services/${serviceId}/export/raw.csv?${params}`);
  expect(response.ok(), "Falha ao exportar pontos brutos persistidos").toBeTruthy();
  expect(response.headers()["content-type"]).toContain("text/csv");
  const csv = await response.text();
  const lines = csv.split(/\r?\n/).filter(Boolean);
  expect(lines).toHaveLength(points + 1); // cabeçalho e pontos persistidos
  expect(lines[0]).toContain("source_file_sha256");
  expect(lines[0]).toContain("source_row_ordinal");
  const metrics = lines.slice(1).map((line) => line.split(",", 7)[6]);
  expect(new Set(metrics)).toEqual(new Set([
    "container_cpu_usage_seconds_total",
    "istio_requests_total.grpc.200.0",
    "istio_request_duration_milliseconds_sum.grpc.200.0",
  ]));
}

test("Replay real compara derivação fiel 15 s e agregada 60 s sem misturar versões", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));

  const runsResponse = await request.get("/api/v1/replays");
  expect(runsResponse.ok(), "Execute start-v1.ps1 e demo-v1.ps1 antes deste teste real").toBeTruthy();
  const { replays } = await runsResponse.json();
  const requestedReplayId = process.env.AIM_LIVE_REPLAY_ID;
  const replay = requestedReplayId
    ? replays.find((item: { replay_run_id: string }) => item.replay_run_id === requestedReplayId)
    : replays.find((item: { status: string }) => item.status === "processed");
  expect(replay, requestedReplayId ? `Replay AIM_LIVE_REPLAY_ID=${requestedReplayId} não encontrado` : "Nenhum replay processado real disponível").toBeTruthy();

  const servicesResponse = await request.get(`/api/v1/replays/${replay.replay_run_id}/services`);
  expect(servicesResponse.ok()).toBeTruthy();
  const { services } = await servicesResponse.json();
  const service = services.find((item: { service_name: string }) => item.service_name === "recommendationservice");
  expect(service, "Serviço recommendationservice não encontrado no replay").toBeTruthy();
  const instance = service.instances.find((item: { instance_name: string }) => item.instance_name === "recommendationservice-1");
  expect(instance, "Instância recommendationservice-1 não encontrada no replay").toBeTruthy();
  await verifyRawCsv(request, replay.replay_run_id, service.service_id, instance.instance_id, 282);

  const transformsResponse = await request.get(`/api/v1/replays/${replay.replay_run_id}/transforms`);
  expect(transformsResponse.ok()).toBeTruthy();
  const { transforms, default_transform_run_id: defaultTransformId } = await transformsResponse.json();
  const aggregate = transforms.find((item: { version: string }) => item.version === "counter-rates-60s-v1");
  const faithful = transforms.find((item: { version: string }) => item.version === "counter-rates-v1");
  expect(aggregate, "Transformação agregada counter-rates-60s-v1 não encontrada").toBeTruthy();
  expect(faithful, "Transformação fiel counter-rates-v1 não encontrada").toBeTruthy();
  expect(defaultTransformId, "A transformação agregada de 60 s deve ser o default do replay").toBe(aggregate.transform_run_id);

  const aggregateMetrics = await readMetrics(request, replay.replay_run_id, service.service_id, instance.instance_id, aggregate.transform_run_id);
  expect(aggregateMetrics).toHaveLength(69);
  expect(aggregateMetrics.filter((point) => point.coverage_state === "complete" && point.value !== null)).toHaveLength(69);
  expect(new Set(aggregateMetrics.map((point) => `${point.window_start_unix_nano}/${point.window_end_unix_nano}`)).size).toBe(23);
  await verifyCsv(request, replay.replay_run_id, service.service_id, instance.instance_id, aggregate.transform_run_id, 69);

  const faithfulMetrics = await readMetrics(request, replay.replay_run_id, service.service_id, instance.instance_id, faithful.transform_run_id);
  expect(faithfulMetrics).toHaveLength(276);
  expect(faithfulMetrics.filter((point) => point.coverage_state === "complete" && point.value !== null)).toHaveLength(207);
  expect(faithfulMetrics.filter((point) => point.coverage_state === "not_applicable" && point.reason === "no_observed_increment")).toHaveLength(69);
  expect(new Set(faithfulMetrics.map((point) => `${point.window_start_unix_nano}/${point.window_end_unix_nano}`)).size).toBe(92);
  await verifyCsv(request, replay.replay_run_id, service.service_id, instance.instance_id, faithful.transform_run_id, 276);

  const evidence = join(process.cwd(), "..", ".runtime", "v1");
  mkdirSync(evidence, { recursive: true });
  await page.goto("/#/");
  const entry = page.getByRole("region", { name: "Replay histórico AIOpsArena" });
  await expect(entry.getByLabel("Execução de replay")).toBeVisible();
  await entry.getByLabel("Execução de replay").selectOption(replay.replay_run_id);
  await expect(entry.getByText("recommendationservice-1", { exact: true })).toBeVisible();
  await page.screenshot({ path: join(evidence, "live-dashboard-desktop.png"), fullPage: true });
  await entry.getByRole("link", { name: "Abrir replay histórico" }).click();
  const ingestion = page.getByRole("status", { name: "Chegada das métricas OTLP" });
  await expect(ingestion).toContainText("282 pontos brutos persistidos");
  await expect(ingestion).toContainText("12 lotes OTLP");

  const selector = page.getByLabel("Execução de transformação");
  await expect(selector).toHaveValue(aggregate.transform_run_id);
  await expect(selector.locator(`option[value="${aggregate.transform_run_id}"]`)).toContainText("Agregada · 60 s");
  await expect(page.getByText("23 janelas persistidas", { exact: false })).toBeVisible();
  await expect(page.getByText("Consultar valores e cobertura por intervalo (23 janelas)", { exact: true })).toBeVisible();
  let csvHref = await page.getByRole("link", { name: "Exportar métricas derivadas CSV" }).getAttribute("href");
  expect(new URL(csvHref!, page.url()).searchParams.get("transform_run_id")).toBe(aggregate.transform_run_id);
  await page.screenshot({ path: join(evidence, "live-replay-60s-desktop.png"), fullPage: true });
  const records = page.locator("details.replay-records");
  if (await records.getAttribute("open") === null) await records.locator("summary").click();
  await expect(page.getByRole("row")).toHaveCount(24);

  await selector.selectOption(faithful.transform_run_id);
  await expect(selector.locator(`option[value="${faithful.transform_run_id}"]`)).toContainText("Fiel · 15 s");
  await expect(page.getByText("92 janelas persistidas", { exact: false })).toBeVisible();
  await expect(page.getByText("Consultar valores e cobertura por intervalo (92 janelas)", { exact: true })).toBeVisible();
  csvHref = await page.getByRole("link", { name: "Exportar métricas derivadas CSV" }).getAttribute("href");
  expect(new URL(csvHref!, page.url()).searchParams.get("transform_run_id")).toBe(faithful.transform_run_id);
  await page.screenshot({ path: join(evidence, "live-replay-15s-desktop.png"), fullPage: true });
  if (await records.getAttribute("open") === null) await records.locator("summary").click();
  await expect(page.getByRole("row")).toHaveCount(93);
  await expect(page.getByRole("cell", { name: "— Não aplicável · Sem incremento observado" })).toHaveCount(69);

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByText("92 janelas persistidas", { exact: false })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({ path: join(evidence, "live-replay-15s-mobile.png"), fullPage: true });
  await selector.selectOption(aggregate.transform_run_id);
  await expect(page.getByText("23 janelas persistidas", { exact: false })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({ path: join(evidence, "live-replay-60s-mobile.png"), fullPage: true });
  expect(errors).toEqual([]);
});

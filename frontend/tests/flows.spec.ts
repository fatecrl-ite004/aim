import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";
// These tests cover the browser-local mock independently of the replay backend.
test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/replays", (route) => route.fulfill({ json: { replays: [] } }));
});
async function nav(page: Page, name: string) {
  await page
    .getByRole("navigation", { name: "Navegação principal" })
    .getByRole("link", { name, exact: true })
    .click();
}
async function scenario(page: Page, name: string) {
  await page.getByRole("button", { name: "Demonstração", exact: true }).click();
  await page.getByRole("button", { name, exact: true }).click();
}
test("dashboard, pausas, métricas e persistência", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Visão geral da malha" }),
  ).toBeVisible();
  await page
    .getByRole("switch", { name: "Pausar monitoramento de checkout-service" })
    .click();
  await page.getByRole("switch", { name: "Sentinela global" }).click();
  await expect(
    page.getByText("Ⅱ Sentinela global em pausa", { exact: true }),
  ).toBeVisible();
  await page.getByRole("switch", { name: "Sentinela global" }).click();
  await expect(
    page.getByRole("switch", {
      name: "Retomar monitoramento de checkout-service",
    }),
  ).toHaveAttribute("aria-checked", "false");
  await page.getByRole("link", { name: "payment-worker", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "payment-worker", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("38 ms · P99 66 ms", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "1 hora", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "1 hora", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.reload();
  await nav(page, "Visão geral");
  await expect(
    page.getByRole("switch", {
      name: "Retomar monitoramento de checkout-service",
    }),
  ).toHaveAttribute("aria-checked", "false");
  expect(errors).toEqual([]);
});
test("cadastro local, endpoint inválido, runtime e desvinculação", async ({
  page,
}) => {
  await page.goto("/#/servicos");
  await page
    .getByRole("button", { name: "+ Novo serviço", exact: true })
    .click();
  await page.getByLabel("Identificador do serviço").fill("meu-servico");
  await page.getByLabel("Tecnologia / runtime").selectOption("Go 1.23");
  await page
    .getByLabel("Endpoint OTel", { exact: true })
    .fill("endereco-invalido");
  await page
    .getByRole("button", { name: "Salvar contrato", exact: true })
    .click();
  await expect(
    page.getByText("Informe uma URI HTTP, HTTPS, gRPC ou gRPCS válida."),
  ).toBeVisible();
  await page
    .getByLabel("Endpoint OTel", { exact: true })
    .fill("http://otel:4317");
  await page
    .getByRole("button", { name: "Salvar contrato", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  const row = page.getByRole("row").filter({ hasText: "meu-servico" });
  await expect(row).toContainText("Go 1.23");
  await page.getByRole("button", { name: "Ações de meu-servico" }).click();
  await page.getByRole("menuitem", { name: "Desvincular serviço" }).click();
  await expect(page.getByRole("dialog")).toContainText(
    "históricos serão preservados",
  );
  await page.getByRole("button", { name: "Confirmar desvinculação" }).click();
  await expect(row).toHaveCount(0);
  await nav(page, "Auditoria e testes");
  await expect(page.getByText("ENS-0041")).toBeVisible();
});
test("incidente, topologia, normalização e arquivamento", async ({ page }) => {
  await page.goto("/");
  await scenario(page, "Incidente ativo");
  await page
    .getByRole("link", { name: "checkout-service", exact: true })
    .click();
  await expect(
    page.getByText("184 ms · P99 420 ms", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Ver topologia de impacto" }).click();
  const dialog = page.getByRole("dialog");
  await dialog
    .getByRole("button", { name: "payment-worker ↳ Afetado por reflexo" })
    .click();
  await expect(
    dialog.getByRole("heading", {
      name: "payment-worker — reflexo correlacionado",
    }),
  ).toBeVisible();
  await page.screenshot({ path: "test-results/aim-topology.png" });
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await page.getByRole("button", { name: "Demonstração", exact: true }).click();
  await page
    .getByRole("button", { name: "Simular sinais normalizados" })
    .click();
  await expect(
    page.getByText("✓ Incidente estabilizado — tendência normalizada"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Arquivar incidente" }).click();
  await expect(
    page.getByRole("heading", { name: "Visão geral da malha" }),
  ).toBeVisible();
  await nav(page, "Auditoria e testes");
  await expect(
    page.getByRole("row").filter({ hasText: "ENS-0042" }),
  ).toContainText("16:45:12");
});
test("notificações: inválido, duplicado, aviso derivado e envio", async ({
  page,
}) => {
  await page.goto("/#/notificacoes");
  await page
    .getByLabel("E-mail do destinatário", { exact: true })
    .fill("invalido");
  await page.getByRole("button", { name: "Adicionar", exact: true }).click();
  await expect(
    page.getByText("Informe um endereço de e-mail válido."),
  ).toBeVisible();
  await page
    .getByLabel("E-mail do destinatário", { exact: true })
    .fill("devops@empresa.com");
  await page.getByRole("button", { name: "Adicionar", exact: true }).click();
  await expect(
    page.getByText("Este endereço já está na lista de destinatários."),
  ).toBeVisible();
  await page
    .getByRole("switch", { name: "Recebimento de alerta-sre@empresa.com" })
    .click();
  await page
    .getByRole("switch", { name: "Recebimento de devops@empresa.com" })
    .click();
  await expect(
    page.getByText("Nenhum destinatário ativo", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Disparar e-mail de teste" }),
  ).toBeDisabled();
  await page
    .getByRole("switch", { name: "Recebimento de devops@empresa.com" })
    .click();
  await expect(
    page.getByText("Nenhum destinatário ativo", { exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Disparar e-mail de teste" }).click();
  await expect(page.getByRole("status")).toContainText(
    "E-mail de teste enviado",
  );
});
test("auditoria: filtros independentes e arquivos baixáveis", async ({
  page,
}) => {
  await page.goto("/#/auditoria");
  await page
    .getByLabel("Serviço", { exact: true })
    .selectOption("auth-service");
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(page.getByText("ENS-0041")).toBeVisible();
  await expect(page.getByText("ENS-0042")).toHaveCount(0);
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar JSON" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("aim-auditoria.json");
  const stream = await download.createReadStream();
  stream!.setEncoding("utf8");
  let content = "";
  for await (const chunk of stream!) content += chunk;
  const json = JSON.parse(content);
  expect(json).toHaveLength(1);
  expect(json[0]["Microsserviço"]).toBe("auth-service");
  expect(Object.keys(json[0])).toHaveLength(8);
  await page.getByLabel("Tipo de anomalia").selectOption("pool");
  await page.getByRole("button", { name: "Aplicar filtros" }).click();
  await expect(
    page.getByRole("heading", { name: "Nenhum resultado para os filtros" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Limpar filtros", exact: true })
    .click();
  await expect(page.getByText("ENS-0042")).toBeVisible();
});
test("recupera falhas predefinidas e dados desatualizados", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Demonstração", exact: true }).click();
  await page.getByText("Estados excepcionais", { exact: true }).click();
  await page
    .getByRole("button", { name: "Endpoint indisponível", exact: true })
    .click();
  await page.getByRole("button", { name: "Preencher exemplo" }).click();
  await page
    .getByRole("button", { name: "Salvar contrato", exact: true })
    .click();
  await expect(
    page.getByText("Endpoint indisponível", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Tentar novamente", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("button", { name: "Demonstração", exact: true }).click();
  await page.getByText("Estados excepcionais", { exact: true }).click();
  await page
    .getByRole("button", { name: "Telemetria desatualizada", exact: true })
    .click();
  await expect(
    page.getByText("◷ Telemetria desatualizada — risco não avaliado"),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Atualizar telemetria", exact: true })
    .click();
  await expect(
    page.getByText("✓ Silêncio operacional — operação nominal"),
  ).toBeVisible();
});
test("ativos locais, layout desktop e mobile sem overflow global", async ({
  page,
}) => {
  await page.goto("/");
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({
    path: "test-results/aim-dashboard.png",
    fullPage: true,
  });
  const assets = await page.locator("img").evaluateAll((imgs) =>
    imgs.map((i) => ({
      loaded: (i as HTMLImageElement).naturalWidth > 0,
      url: (i as HTMLImageElement).src,
    })),
  );
  expect(assets.every((a) => a.loaded && !a.url.includes("figma.com"))).toBe(
    true,
  );
  await page
    .getByRole("link", { name: "checkout-service", exact: true })
    .click();
  await expect(
    page.getByText("42 ms · P99 74 ms", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/aim-metrics.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await nav(page, "Visão geral");
  await expect(
    page.getByRole("heading", { name: "Visão geral da malha" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/aim-mobile.png",
    fullPage: true,
  });
});

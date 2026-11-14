import { describe, expect, test } from "vitest";
import type { ReplayMetric } from "../src/domain/replay";
import { contiguousSegments, coverageText, formatMetric, nanoDate, timePosition } from "../src/domain/replay";

const metric = (start: string, end: string, value: number | null, state: ReplayMetric["coverage_state"] = "complete", reason: string | null = null): ReplayMetric => ({
  metric_name: "success_latency_mean_ms", value, unit: "ms",
  window_start_unix_nano: start, window_end_unix_nano: end,
  coverage_state: state, reason,
});

describe("séries históricas e qualidade", () => {
  test("preserva zero observado, interrompe no_observed_increment e não une lacunas", () => {
    const zero = metric("100", "200", 0);
    const traffic = metric("200", "300", 12);
    const noIncrement = metric("300", "400", null, "not_applicable", "no_observed_increment");
    const later = metric("400", "500", 13);
    const afterGap = metric("600", "700", 14);
    expect(contiguousSegments([zero, traffic, noIncrement, later, afterGap])).toEqual([[zero, traffic], [later], [afterGap]]);
    expect(formatMetric(0)).toBe("0");
    expect(formatMetric(null)).toBe("—");
    expect(coverageText(noIncrement)).toBe("Não aplicável · Sem incremento observado");
  });

  test("não plota valores inválidos como resultados observados", () => {
    expect(contiguousSegments([
      metric("100", "200", 0, "invalid", "counter_reset"),
      metric("200", "300", null, "missing"),
      metric("300", "400", 3, "partial"),
    ])).toHaveLength(1);
    expect(contiguousSegments([metric("100", "200", null, "not_applicable", "no_observed_increment")])).toEqual([]);
  });

  test("calcula offsets antes de converter nanos históricos para Number", () => {
    const start = "1719205980000000001";
    expect(timePosition("1719205980000000002", start, "1719205980000000003")).toBe(0.5);
    expect(nanoDate(start).toISOString()).toBe("2024-06-24T05:13:00.000Z");
  });
});

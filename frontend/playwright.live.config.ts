import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

export default defineConfig({
  ...base,
  testMatch: "**/*.live.ts",
  workers: 1,
  webServer: undefined,
});

import { defineConfig } from "vitest/config";
import { loadEnv } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const proxy = { "/api": { target: env.AIM_API_PROXY_TARGET || "http://127.0.0.1:8000", changeOrigin: true } };
  return {
    plugins: [react()],
    base: "./",
    server: { host: "127.0.0.1", port: 5173, strictPort: true, proxy },
    preview: { host: "127.0.0.1", proxy },
    test: { include: ["tests/**/*.test.ts"] },
  };
});

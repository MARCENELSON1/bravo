import path from "path"
import { defineConfig } from 'vitest/config'
import { loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // VITE_API_TARGET decide contra qué backend corre el dev server. Sin la variable
  // apunta al local de siempre; poniéndola en .env.local se trabaja contra el
  // backend deployado, con datos reales.
  const env = loadEnv(mode, process.cwd(), "")
  const apiTarget = env.VITE_API_TARGET || "http://localhost:8000"

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      // Same-origin in dev: the SPA calls relative /api/... and Vite proxies to
      // the FastAPI backend. This keeps the HttpOnly refresh cookie first-party
      // (no CORS needed). In production a reverse proxy serves both under one origin.
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: './src/test/setup.ts',
      css: false,
    },
  }
})

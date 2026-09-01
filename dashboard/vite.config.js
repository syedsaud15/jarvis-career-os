import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  const apiKey = env.JARVIS_API_KEY || globalThis.process?.env?.JARVIS_API_KEY
  return {
    plugins: [react()],
    envDir: '..',
    cacheDir: '../.vite-cache',
    server: {
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          headers: apiKey ? { 'X-API-Key': apiKey } : {},
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})

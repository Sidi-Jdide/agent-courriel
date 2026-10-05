/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const API = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    // En développement, Vite redirige les appels vers FastAPI.
    proxy: { '/api': API, '/docs': API, '/openapi.json': API },
  },
  test: { environment: 'jsdom' },
})

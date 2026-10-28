import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// VITE_API_URL is injected at build time for cloud deploys (Render backend URL).
// When empty, API calls use a relative /api path — works with the nginx Docker proxy locally.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

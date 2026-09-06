import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiTarget = process.env.VITE_API_TARGET || 'https://idp-api-754915077075.us-central1.run.app'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/auth': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/templates': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/requests': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/deployments': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/governance': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/admin': {
        target: apiTarget,
        changeOrigin: true,
      },
      '/callbacks': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
})

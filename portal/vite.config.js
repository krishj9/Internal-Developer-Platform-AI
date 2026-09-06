import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/templates': 'http://127.0.0.1:8000',
      '/requests': 'http://127.0.0.1:8000',
      '/deployments': 'http://127.0.0.1:8000',
      '/governance': 'http://127.0.0.1:8000',
      '/admin': 'http://127.0.0.1:8000',
      '/callbacks': 'http://127.0.0.1:8000',
    },
  },
})

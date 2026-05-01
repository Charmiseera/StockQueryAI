import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/query': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/tts': 'http://localhost:8000',
      '/login': 'http://localhost:8000',
      '/register': 'http://localhost:8000',
      '/me': 'http://localhost:8000',
      '/ingest': 'http://localhost:8000',
    }
  }
})

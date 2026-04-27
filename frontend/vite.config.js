import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/register': 'http://localhost:8000',
      '/login': 'http://localhost:8000',
      '/verify-email': 'http://localhost:8000',
      '/forgot-password': 'http://localhost:8000',
      '/reset-password': 'http://localhost:8000',
      '/me': 'http://localhost:8000',
      '/history': 'http://localhost:8000',
      '/query': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/tts': 'http://localhost:8000',
    }
  }
})

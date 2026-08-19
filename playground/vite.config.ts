import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // In dev, Vite serves the app on its own port; proxy API calls to the
      // FastAPI server so the frontend can use plain relative fetch() calls
      // exactly as it does in production, where FastAPI serves both.
      '/api': 'http://localhost:8092',
    },
  },
})

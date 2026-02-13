import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/call-service': {
        target: 'https://cxc-call-service.onrender.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/call-service/, ''),
        timeout: 600000,
        proxyTimeout: 600000,
      },
    },
  },
})

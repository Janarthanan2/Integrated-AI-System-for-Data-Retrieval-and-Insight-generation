import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1000, // Optional: Increase limit if chunks are still slightly large
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-bootstrap', 'bootstrap'],
          'vendor-mui': ['@mui/material', '@mui/icons-material', '@mui/x-charts', '@mui/x-data-grid', '@emotion/react', '@emotion/styled'],
          'vendor-charts': ['apexcharts', 'react-apexcharts', 'recharts'],
          'vendor-utils': ['lucide-react', 'react-markdown', 'remark-gfm']
        }
      }
    }
  },
  server: {
    proxy: {
      '/query': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/models': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/admin': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    },
    host: true,
    allowedHosts: true
  }
})

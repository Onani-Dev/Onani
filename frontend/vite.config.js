import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/',
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://flask:5000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://nginx-dev:80',
        changeOrigin: true,
      },
      '/images': {
        target: 'http://nginx-dev:80',
        changeOrigin: true,
      },
      '/avatars': {
        target: 'http://nginx-dev:80',
        changeOrigin: true,
      },
      '/sample': {
        target: 'http://nginx-dev:80',
        changeOrigin: true,
      },
    },
  },
})

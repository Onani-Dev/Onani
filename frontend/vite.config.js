import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import packageJson from './package.json'

const appVersion = packageJson.version
const releaseTag = `v${appVersion}`
const releaseUrl = `https://github.com/Onani-Dev/Onani/releases/tag/${releaseTag}`

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/',
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
    __APP_RELEASE_URL__: JSON.stringify(releaseUrl),
  },
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
        target: 'http://flask:5000',
        changeOrigin: true,
      },
      '/images': {
        target: 'http://flask:5000',
        changeOrigin: true,
      },
      '/videos': {
        target: 'http://flask:5000',
        changeOrigin: true,
      },
      '/avatars': {
        target: 'http://flask:5000',
        changeOrigin: true,
      },
      '/sample': {
        target: 'http://flask:5000',
        changeOrigin: true,
      },
      '/external': {
        target: 'http://flask:5000',
        changeOrigin: true,
      },
    },
  },
})

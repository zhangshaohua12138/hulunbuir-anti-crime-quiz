import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: '/vue/',
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8080', changeOrigin: false },
      '/static': { target: 'http://127.0.0.1:8080', changeOrigin: false },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
        },
      },
    },
  },
})
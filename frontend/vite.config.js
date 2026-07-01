import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import http from 'node:http'

const localAgent = new http.Agent({ keepAlive: true })

export default defineConfig({
  base: './',
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag.startsWith('mc-')
        }
      }
    })
  ],
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        agent: localAgent,
        bypass(req) {
          const accept = req.headers.accept || ''
          if (accept.includes('text/html')) {
            return '/index.html'
          }
        }
      }
    }
  }
})

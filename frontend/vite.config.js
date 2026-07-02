import { cpSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import http from 'node:http'

const localAgent = new http.Agent({ keepAlive: true })

function copyMdsIcons() {
  return {
    name: 'copy-mds-icons',
    closeBundle() {
      const src = resolve(__dirname, 'node_modules/@maersk-global/icons/js/20px')
      const dest = resolve(__dirname, 'dist/node_modules/@maersk-global/icons/js/20px')
      mkdirSync(dest, { recursive: true })
      cpSync(src, dest, { recursive: true })
    }
  }
}

export default defineConfig({
  base: './',
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag.startsWith('mc-')
        }
      }
    }),
    copyMdsIcons()
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

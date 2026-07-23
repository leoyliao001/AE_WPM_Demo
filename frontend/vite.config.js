import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import http from 'node:http'

const localAgent = new http.Agent({ keepAlive: true })

export default defineConfig(({ command }) => ({
  // Absolute base when served via Apache HTTPS proxy; relative for production build
  base: command === 'build' ? './' : '/',
  cacheDir: resolve(__dirname, '.vite-cache'),
  resolve: {
    alias: {
      '@floating-ui/dom': resolve(__dirname, 'node_modules/@floating-ui/dom/dist/floating-ui.dom.esm.js'),
      '@floating-ui/core': resolve(__dirname, 'node_modules/@floating-ui/core/dist/floating-ui.core.esm.js'),
      '@floating-ui/utils/dom': resolve(__dirname, 'node_modules/@floating-ui/utils/dist/floating-ui.utils.dom.esm.js'),
      '@floating-ui/utils': resolve(__dirname, 'node_modules/@floating-ui/utils/dist/floating-ui.utils.esm.js')
    }
  },
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
    host: '127.0.0.1',
    port: 3001,
    strictPort: true,
    // Browser opens https://<registered-host>/ (Apache → here). HMR uses same host on 443/WSS.
    hmr: {
      protocol: 'wss',
      clientPort: 443
    },
    fs: {
      allow: ['..']
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
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
}))

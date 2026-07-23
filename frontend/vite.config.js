import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import http from 'node:http'

const localAgent = new http.Agent({ keepAlive: true })

// Set VITE_BEHIND_APACHE=1 when using enable-dev-proxy.bat (HTTPS → Vite)
const behindApache = process.env.VITE_BEHIND_APACHE === '1'

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
    // If 3001 is busy, try 3002, 3003, ...
    strictPort: false,
    // Only force WSS/443 HMR when fronted by Apache DEV proxy
    ...(behindApache
      ? {
          hmr: {
            protocol: 'wss',
            clientPort: 443
          }
        }
      : {}),
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

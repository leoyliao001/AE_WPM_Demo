import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import http from 'node:http'
import fs from 'node:fs'

const localAgent = new http.Agent({ keepAlive: true })

// Set VITE_BEHIND_APACHE=1 when using enable-dev-proxy.bat (HTTPS → Vite)
const behindApache = process.env.VITE_BEHIND_APACHE === '1'

// Dev backend that /api is proxied to.
//   default         → 127.0.0.1:8001 — your own `manage.py runserver` (SQLite)
//   VITE_API_TARGET → override, e.g. http://127.0.0.1:8000 to hit the production
//                     AE_WPM service (Waitress + MSSQL)
// Never default to 8000: the AE_WPM Windows service owns that port, and Windows
// lets a second process bind an already-listening port without any error, so
// requests end up split unpredictably between the two backends.
const apiTarget = process.env.VITE_API_TARGET || 'http://127.0.0.1:8001'

function logApiTargetPlugin() {
  return {
    name: 'log-api-target',
    apply: 'serve',
    configureServer() {
      console.log(`[vite] /api -> ${apiTarget}`)
    }
  }
}

function copyMdsIconsPlugin() {
  return {
    name: 'copy-mds-icons',
    apply: 'build',
    writeBundle(options) {
      const outDir = options.dir || resolve(__dirname, 'dist')
      const sourceDir = resolve(__dirname, 'node_modules/@maersk-global/icons/js')
      const targetDir = resolve(outDir, 'assets/node_modules/@maersk-global/icons/js')

      if (!fs.existsSync(sourceDir)) {
        this.warn(`MDS icons source not found: ${sourceDir}`)
        return
      }

      fs.mkdirSync(targetDir, { recursive: true })
      fs.cpSync(sourceDir, targetDir, { recursive: true, force: true })
    }
  }
}

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
    }),
    copyMdsIconsPlugin(),
    logApiTargetPlugin()
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
        target: apiTarget,
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

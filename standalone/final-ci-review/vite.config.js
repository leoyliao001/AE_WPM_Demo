import { cpSync, mkdirSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const frontendModules = resolve(__dirname, '../../frontend/node_modules')
const require = createRequire(resolve(frontendModules, 'vite/package.json'))

const { defineConfig } = require('vite')
const vuePlugin = require('@vitejs/plugin-vue')
const vue = vuePlugin.default || vuePlugin

function copyMdsIcons() {
  return {
    name: 'copy-mds-icons',
    closeBundle() {
      const src = resolve(frontendModules, '@maersk-global/icons/js/20px')
      const dest = resolve(__dirname, 'dist/node_modules/@maersk-global/icons/js/20px')
      mkdirSync(dest, { recursive: true })
      cpSync(src, dest, { recursive: true })
    }
  }
}

export default defineConfig({
  root: __dirname,
  resolve: {
    alias: {
      vue: resolve(frontendModules, 'vue'),
      '@maersk-global': resolve(frontendModules, '@maersk-global')
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
    copyMdsIcons()
  ],
  server: {
    port: 3002,
    fs: {
      allow: [resolve(__dirname, '../..')]
    }
  }
})

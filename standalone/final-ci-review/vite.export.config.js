import { cpSync, copyFileSync, mkdirSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const frontendModules = resolve(__dirname, '../../frontend/node_modules')
const exportDir = resolve(__dirname, '../../exports/final-ci-review')
const require = createRequire(resolve(frontendModules, 'vite/package.json'))

const { defineConfig } = require('vite')
const vuePlugin = require('@vitejs/plugin-vue')
const vue = vuePlugin.default || vuePlugin

function copyMdsIcons() {
  return {
    name: 'copy-mds-icons',
    closeBundle() {
      const src = resolve(frontendModules, '@maersk-global/icons/js/20px')
      const dest = resolve(exportDir, 'node_modules/@maersk-global/icons/js/20px')
      mkdirSync(dest, { recursive: true })
      cpSync(src, dest, { recursive: true })
    }
  }
}

function finalizeExport() {
  return {
    name: 'finalize-export',
    closeBundle() {
      const indexPath = resolve(exportDir, 'index.html')
      copyFileSync(indexPath, resolve(exportDir, 'Final-CI-Review.html'))

      writeFileSync(
        resolve(exportDir, '打开页面.bat'),
        `@echo off\r\nchcp 65001 >nul\r\ncd /d "%~dp0"\r\necho Starting Final CI Review on http://localhost:8765 ...\r\nstart "" "http://localhost:8765/Final-CI-Review.html"\r\npython -m http.server 8765\r\n`,
        'utf8'
      )

      writeFileSync(
        resolve(exportDir, 'README.txt'),
        `Final CI Review — 本地离线包\r\n================================\r\n\r\n【推荐】双击「打开页面.bat」启动本地服务并在浏览器中打开页面。\r\n\r\n也可手动启动：\r\n  cd /d "%~dp0"\r\n  python -m http.server 8765\r\n  浏览器访问 http://localhost:8765/Final-CI-Review.html\r\n\r\n说明：\r\n- 请勿直接双击 HTML 文件（浏览器安全限制会导致脚本无法加载）。\r\n- 数据保存在浏览器 localStorage（key: automation_idea_records_v1）。\r\n- 测试 Sign-off：在浏览器控制台执行\r\n    localStorage.setItem('intake_requestor_email', 'vinod.gupta@maersk.com')\r\n- MDS 字体/样式需联网加载 CDN 资源。\r\n`,
        'utf8'
      )
    }
  }
}

export default defineConfig({
  root: __dirname,
  base: './',
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
    copyMdsIcons(),
    finalizeExport()
  ],
  build: {
    outDir: exportDir,
    emptyOutDir: true,
    assetsInlineLimit: 100000000,
    rollupOptions: {
      output: {
        inlineDynamicImports: true
      }
    }
  }
})

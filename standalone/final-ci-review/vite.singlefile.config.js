import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const frontendModules = resolve(__dirname, '../../frontend/node_modules')
const exportFile = resolve(__dirname, '../../exports/Final-CI-Review.html')
const require = createRequire(resolve(frontendModules, 'vite/package.json'))

const { defineConfig } = require('vite')
const vuePlugin = require('@vitejs/plugin-vue')
const { viteSingleFile } = require('vite-plugin-singlefile')
const vue = vuePlugin.default || vuePlugin

const MDS_STYLES = [
  'https://assets.maerskline.com/mds/fonts/fonts-cdn.css',
  'https://assets.maerskline.com/mds/latest/design-tokens/maersk/light/css/design-tokens-px.min.css',
  'https://assets.maerskline.com/mds/latest/foundations/foundations.min.css'
]

function inlineMdsStyles() {
  return {
    name: 'inline-mds-styles',
    async transformIndexHtml(html) {
      const blocks = await Promise.all(
        MDS_STYLES.map(async (url) => {
          const res = await fetch(url)
          if (!res.ok) throw new Error(`Failed to fetch MDS style: ${url}`)
          const css = await res.text()
          return `<style data-mds-source="${url}">\n${css}\n</style>`
        })
      )
      return html.replace('</head>', `${blocks.join('\n')}\n</head>`)
    }
  }
}

function finalizeSingleFile() {
  return {
    name: 'finalize-single-file',
    closeBundle() {
      const exportsDir = resolve(__dirname, '../../exports')
      mkdirSync(exportsDir, { recursive: true })
      const built = resolve(exportsDir, 'index.singlefile.html')
      copyFileSync(built, exportFile)

      let html = readFileSync(exportFile, 'utf8')
      html = html.replace(
        /<link rel="stylesheet" href="https:\/\/assets\.maerskline\.com\/mds\/[^"]+">\s*/g,
        ''
      )
      const readme = `<!--\r\n  Final CI Review — 单文件版\r\n  用法：直接双击本 HTML 用浏览器打开（推荐 Chrome / Edge）。\r\n  样式已内嵌；图标首次加载需联网。\r\n  数据：localStorage（automation_idea_records_v1）\r\n  测试 Sign-off：localStorage.setItem('intake_requestor_email','vinod.gupta@maersk.com')\r\n  重新生成：cd frontend && npm run build:final-ci-html\r\n-->\r\n`
      if (!html.startsWith('<!--')) {
        html = readme + html
      }
      writeFileSync(exportFile, html, 'utf8')
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
    inlineMdsStyles(),
    viteSingleFile({ removeViteModuleLoader: true }),
    finalizeSingleFile()
  ],
  build: {
    outDir: resolve(__dirname, '../../exports'),
    emptyOutDir: false,
    assetsInlineLimit: 100000000,
    rollupOptions: {
      input: resolve(__dirname, 'index.singlefile.html'),
      output: {
        inlineDynamicImports: true
      }
    }
  }
})

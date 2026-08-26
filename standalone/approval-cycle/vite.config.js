import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Standalone preview for ApprovalCycle.vue — avoids the private @maersk-global registry.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3002,
    fs: { allow: ['../..'] }
  }
})

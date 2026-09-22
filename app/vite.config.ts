import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 1420,
    strictPort: true,
    // Never watch Rust build artifacts: cargo writes DLLs under
    // src-tauri/target while Vite holds watchers -> EBUSY crash.
    watch: {
      ignored: ['**/src-tauri/**', '**/target/**'],
    },
  },
})
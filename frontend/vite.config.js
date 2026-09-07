import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// `vitest/config` re-exports vite's defineConfig, so this file still drives the
// dev server and build — it just also carries the `test` block for Vitest.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
  },
})

/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Import defineConfig from 'vite' (a runtime dependency), NOT 'vitest/config'
// (a devDependency) — otherwise `vite build` would require vitest to be
// installed and a production build with --omit=dev would fail. Vitest still
// reads the `test` block below from this file. The reference comment above just
// gives editors type hints for `test`.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
  },
})

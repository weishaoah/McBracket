/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Relative base so the build works on GitHub Pages project sites
// (https://<user>.github.io/McBracket/) without any rebuild.
export default defineConfig({
  base: './',
  plugins: [react()],
  server: { host: '127.0.0.1', port: 5173 },
  test: {
    // Keep the vitest SSR cache inside the project: some sandboxed
    // environments block writes to the system temp dir, which makes an
    // otherwise green run fail with a transient EPERM.
    cacheDir: './node_modules/.vitest',
  },
})

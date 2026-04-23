import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),
  ],
  root: 'src',  // HTML ist in src/
  publicDir: '../public',  // Public assets relativ zu src/
  build: {
    outDir: '../dist',  // Build output ins Root dist/
    emptyOutDir: true,
    sourcemap: true,
  },
  server: {
    port: 5173,
    open: true,
  },
})

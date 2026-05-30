import { defineConfig } from 'vite'
import { resolve } from 'path'
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
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'src/index.html'),
        dashboard: resolve(__dirname, 'src/dashboard.html'),
        blueprints: resolve(__dirname, 'src/blueprints.html'),
        'architecture-builder': resolve(__dirname, 'src/architecture-builder.html'),
        'infrastructure-designer': resolve(__dirname, 'src/infrastructure-designer.html'),
        pricing: resolve(__dirname, 'src/pricing.html'),
        security: resolve(__dirname, 'src/security.html'),
        login: resolve(__dirname, 'src/login.html'),
        register: resolve(__dirname, 'src/register.html'),
        // Admin pages vorerst auskommentiert (komplexe Dependencies)
        // admin: resolve(__dirname, 'src/admin.html'),
        // 'admin-faq': resolve(__dirname, 'src/admin-faq.html'),
        // 'admin-feedback': resolve(__dirname, 'src/admin-feedback.html'),
        // 'admin-reviews': resolve(__dirname, 'src/admin-reviews.html'),
        // 'admin-vouchers': resolve(__dirname, 'src/admin-vouchers.html'),
        // billing: resolve(__dirname, 'src/billing.html'),
        // 'aws-credentials': resolve(__dirname, 'src/aws-credentials.html'),
      },
    },
  },
  server: {
    port: 5173,
    open: true,
  },
})

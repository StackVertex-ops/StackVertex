/**
 * Vitest Configuration für OverCloud Frontend Unit Tests
 */

import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './tests/unit/setup.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        'dist/',
        '**/*.spec.js',
        '**/*.test.js',
        '**/setup.js'
      ]
    },
    include: ['tests/unit/**/*.test.js'],
    exclude: ['node_modules', 'dist', 'tests/e2e']
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});

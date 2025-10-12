import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

// ES Module equivalent of __dirname
const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      'pages': path.resolve(__dirname, './src/pages'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '(components)': path.resolve(__dirname, './src/(components)'),
    }
  },
  server: {
    // Server stability optimizations for Playwright tests
    port: 5173,
    strictPort: true,
    host: true,
    // Increase timeouts to prevent 500 errors during long test runs
    hmr: {
      timeout: 30000, // 30 seconds
    },
    watch: {
      // Reduce file system overhead during tests
      usePolling: false,
      interval: 100,
    },
  },
  // Optimize dependencies pre-bundling for faster dev server
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      '@tanstack/react-query-devtools',
    ],
  },
  // Build optimizations
  build: {
    // Reduce chunk size warnings
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'query-vendor': ['@tanstack/react-query', '@tanstack/react-query-devtools'],
        },
      },
    },
  },
})

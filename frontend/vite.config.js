import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';

// SPA-Build (kein SSR). In Produktion wird dist/ vom FastAPI-Backend statisch
// ausgeliefert; im Dev proxyt Vite /api an den uvicorn-Server.
export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  base: './',
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});

import { defineConfig } from "vite";
import solid from "vite-plugin-solid";

export default defineConfig({
  base: "/static/bundler/",
  plugins: [solid()],
  build: {
    manifest: "manifest.json",
    emptyOutDir: true,
    outDir: "../static/bundler/",
    rollupOptions: {
      input: {
        admin: "src/entrypoints/admin.tsx",
      },
    },
  },
});

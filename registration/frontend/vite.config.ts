import { devtools as tanstackDevtools } from "@tanstack/devtools-vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import devtools from "solid-devtools/vite";
import { defineConfig } from "vite";
import solid from "vite-plugin-solid";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  base: "/static/bundler/",
  plugins: [
    tsconfigPaths(),
    tanstackDevtools(),
    devtools({
      autoname: true,
    }),
    tanstackRouter({
      target: "solid",
      autoCodeSplitting: true,
    }),
    solid(),
  ],
  build: {
    manifest: "manifest.json",
    emptyOutDir: true,
    outDir: "../static/bundler/",
    rollupOptions: {
      input: "src/index.tsx",
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        quietDeps: true,
        silenceDeprecations: ["color-functions", "import"],
      },
    },
  },
});

import * as esbuild from "esbuild";
import { solidPlugin } from "esbuild-plugin-solid";

const IS_PROD = process.env.NODE_ENVIRONMENT === "production";

function buildOpts(entryPoints) {
  return {
    entryPoints,
    bundle: true,
    outdir: "../static/",
    minify: IS_PROD,
    sourcemap: true,
    drop: IS_PROD ? ["console"] : [],
    target: ["es2020"],
    loader: {
      ".woff": "file",
      ".woff2": "file",
    },
    plugins: [solidPlugin()],
  };
}

await Promise.all([
  esbuild.build(buildOpts(["src/entrypoints/admin.ts"])),
]);

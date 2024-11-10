import { writeFileSync } from "fs";

import esbuild from "esbuild";
import { sassPlugin } from "esbuild-sass-plugin";
import { solidPlugin } from "esbuild-plugin-solid";

const IS_PROD = process.env.NODE_ENVIRONMENT === "production";

const result = await esbuild.build({
  bundle: true,
  drop: IS_PROD ? ["console"] : [],
  entryPoints: ["src/entrypoints/admin.tsx"],
  metafile: true,
  minify: IS_PROD,
  outdir: "../static/",
  sourcemap: true,
  target: ["es2020"],
  loader: {
    ".woff": "file",
    ".woff2": "file",
    ".ttf": "file",
  },
  plugins: [
    sassPlugin({
      quietDeps: ["bulma"],
    }),
    solidPlugin(),
  ],
});

if (result.metafile) {
  writeFileSync("./metafile.json", JSON.stringify(result.metafile));
}

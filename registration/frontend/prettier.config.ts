import { type Config } from "prettier";

const config: Config = {
  plugins: ["@trivago/prettier-plugin-sort-imports"],
  importOrder: ["^@(admin|components)/.*$", "^[./]"],
  importOrderSeparation: true,
  importOrderSortSpecifiers: true,
};

export default config;

import js from "@eslint/js";
import pluginQuery from "@tanstack/eslint-plugin-query";
import * as tsParser from "@typescript-eslint/parser";
import solid from "eslint-plugin-solid/configs/typescript";
import globals from "globals";

export default [
  js.configs.recommended,
  ...pluginQuery.configs["flat/recommended"],
  {
    files: ["**/*.{ts,tsx}"],
    ...solid,
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        project: "tsconfig.json",
      },
      globals: globals.browser,
    },
  },
  {
    files: ["**/*.{ts,tsx,js,jsx,mjs}"],
    rules: {
      "no-unused-vars": "off",
    },
  },
];

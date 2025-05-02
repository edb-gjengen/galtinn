import { defineConfig } from "eslint/config";
import globals from "globals";
import babelParser from "@babel/eslint-parser";
import js from "@eslint/js";
import prettierRecommended from 'eslint-plugin-prettier/recommended'
import importPlugin from 'eslint-plugin-import'

export default defineConfig([
  js.configs.recommended,
  importPlugin.flatConfigs.recommended,
  prettierRecommended,
  {
    languageOptions: {
      globals: { ...globals.browser },
      parser: babelParser,
      sourceType: "module",
      parserOptions: {
          requireConfigFile: false,
      },
    },
  },
]);

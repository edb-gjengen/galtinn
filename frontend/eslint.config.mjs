import globals from 'globals';
import js from '@eslint/js';

import { defineConfig } from 'eslint/config';
import eslintPluginPrettierRecommended from 'eslint-plugin-prettier/recommended';
import importPlugin from 'eslint-plugin-import';

export default defineConfig([
    js.configs.recommended,
    eslintPluginPrettierRecommended,
    importPlugin.flatConfigs.recommended,
    { languageOptions: { globals: { ...globals.browser, config: false } } },
]);

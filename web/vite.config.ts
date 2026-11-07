import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The built app is committed under keel/static/app, so a clone runs `keel up`
// without Node. Only people changing the UI need `npm run build`.
export default defineConfig({
  plugins: [react()],
  build: { outDir: "../keel/static/app", emptyOutDir: true },
  server: { proxy: { "/api": "http://127.0.0.1:8420" } },
});

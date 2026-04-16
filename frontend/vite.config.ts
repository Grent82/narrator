import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendTarget = process.env.VITE_BACKEND_PROXY_TARGET || "http://localhost:17000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/stories": {
        target: backendTarget,
        changeOrigin: true,
      },
      "/turn": {
        target: backendTarget,
        changeOrigin: true,
      },
      "/health": {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
});

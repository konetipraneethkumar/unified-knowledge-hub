import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

function rewriteSpaPath(server: { middlewares: { use: (middleware: (request: { url?: string }, response: unknown, next: () => void) => void) => void } }) {
  server.middlewares.use((request, _response, next) => {
    if (request.url === "/history" || request.url === "/settings") {
      request.url = "/index.html";
    }
    next();
  });
}

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    {
      name: "smriti-spa-route-rewrite",
      configureServer: rewriteSpaPath,
      configurePreviewServer: rewriteSpaPath,
    },
  ],
});
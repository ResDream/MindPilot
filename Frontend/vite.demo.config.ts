import { resolve } from "node:path"
import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import svgLoader from "vite-svg-loader"

export default defineConfig({
  root: resolve(__dirname, "src/renderer"),
  define: { "import.meta.env.VITE_MINDPILOT_DEMO": JSON.stringify("true") },
  resolve: { alias: { "@renderer": resolve(__dirname, "src/renderer/src") } },
  plugins: [vue(), svgLoader()],
  server: { host: "127.0.0.1", port: 5173, strictPort: true }
})

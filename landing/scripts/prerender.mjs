/**
 * Post-build: inyecta en dist/index.html el HTML ya renderizado y el JSON-LD.
 *
 * Corre después de los dos `vite build` (cliente y SSR). Sin esto el archivo que
 * sirve Railway tiene 0 caracteres de texto y es invisible para cualquier bot
 * que no ejecute JavaScript.
 */
import { readFile, writeFile, rm } from "node:fs/promises"
import { fileURLToPath } from "node:url"
import path from "node:path"

// Rutas relativas a ESTE archivo, sin asumir cómo se llama la carpeta: Railway
// monta el Root Directory en /app, no en /landing.
const projectDir = fileURLToPath(new URL("../", import.meta.url))
const indexPath = path.join(projectDir, "dist", "index.html")
const serverEntry = path.join(projectDir, "dist-ssr", "entry-server.js")

const { render, structuredData } = await import(serverEntry)

const html = render()
const jsonLd = await structuredData()

let template = await readFile(indexPath, "utf8")

if (!template.includes('<div id="root"></div>')) {
  throw new Error("No encontré el <div id=\"root\"> vacío en dist/index.html")
}
template = template.replace('<div id="root"></div>', `<div id="root">${html}</div>`)

// El JSON-LD va al final del <head>, antes de cerrarlo.
template = template.replace(
  "</head>",
  `  <script type="application/ld+json">${jsonLd}</script>\n  </head>`,
)

await writeFile(indexPath, template, "utf8")
// El bundle SSR es un artefacto intermedio: no se publica.
await rm(path.join(projectDir, "dist-ssr"), { recursive: true, force: true })

const text = template
  .replace(/<script[\s\S]*?<\/script>/g, "")
  .replace(/<[^>]+>/g, " ")
  .replace(/\s+/g, " ")
  .trim()
console.log(`prerender ok — ${text.length} caracteres de texto en el HTML servido`)

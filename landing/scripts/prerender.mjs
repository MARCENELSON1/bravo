/**
 * Post-build: genera las DOS variantes estáticas de la landing desde una sola base.
 *
 *   dist/index.html      → es-AR  (render("AR"))
 *   dist/en/index.html   → en-US  (render("INTL"))
 *
 * Cada una lleva su <head> por región (title/description/OG/canonical + hreflang),
 * su `<html lang>` y su JSON-LD. Ambas URLs quedan crawleables directo; hreflang le
 * dice a Google que son la misma página en dos idiomas. Sin esto el archivo que
 * sirve Railway tiene 0 caracteres de texto y es invisible para cualquier bot que
 * no ejecute JavaScript.
 */
import { readFile, writeFile, rm, mkdir } from "node:fs/promises"
import { fileURLToPath, pathToFileURL } from "node:url"
import path from "node:path"

const projectDir = fileURLToPath(new URL("../", import.meta.url))
const distDir = path.join(projectDir, "dist")
const indexPath = path.join(distDir, "index.html")
const serverEntry = path.join(projectDir, "dist-ssr", "entry-server.js")

// `import()` necesita una URL file://, no una ruta del sistema: en Windows una
// ruta absoluta como C:... hace que Node lea "c:" como esquema y falle.
const { render, structuredData, seoHead, seoMetaFor } = await import(
  pathToFileURL(serverEntry).href,
)

const base = await readFile(indexPath, "utf8")

if (!base.includes('<div id="root"></div>')) {
  throw new Error('No encontré el <div id="root"> vacío en dist/index.html')
}
if (!/<!--SEO:start-->[\s\S]*?<!--SEO:end-->/.test(base)) {
  throw new Error("No encontré el bloque <!--SEO:start-->…<!--SEO:end--> en dist/index.html")
}

// AR se escribe sobre dist/index.html; INTL va a dist/en/index.html.
const VARIANTS = [
  { region: "AR", out: indexPath },
  { region: "INTL", out: path.join(distDir, "en", "index.html") },
]

for (const { region, out } of VARIANTS) {
  const html = render(region)
  const jsonLd = await structuredData(region)
  const { lang } = seoMetaFor(region)

  const doc = base
    // <head> variable por región (reemplaza todo el bloque marcado).
    .replace(/<!--SEO:start-->[\s\S]*?<!--SEO:end-->/, seoHead(region))
    // idioma del documento: el cliente deriva la región de acá al hidratar.
    .replace(/<html lang="[^"]*">/, `<html lang="${lang}">`)
    // el árbol ya renderizado.
    .replace('<div id="root"></div>', `<div id="root">${html}</div>`)
    // JSON-LD al final del <head>.
    .replace("</head>", `  <script type="application/ld+json">${jsonLd}</script>\n  </head>`)

  await mkdir(path.dirname(out), { recursive: true })
  await writeFile(out, doc, "utf8")

  const text = doc
    .replace(/<script[\s\S]*?<\/script>/g, "")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim()
  console.log(
    `prerender ${region} → ${path.relative(distDir, out) || "index.html"} — ${text.length} caracteres de texto`,
  )
}

// El bundle SSR es un artefacto intermedio: no se publica.
await rm(path.join(projectDir, "dist-ssr"), { recursive: true, force: true })
